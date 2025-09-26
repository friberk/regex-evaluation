import argparse
from peewee import SqliteDatabase, OperationalError
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import scienceplots

plt.style.use(['science', 'nature', 'vibrant'])
# Use linux libertine font
plt.rcParams.update({
    "font.family": "Linux Libertine O",})

# It is assumed these models are available from a 'db.models' module.
# You might need to adjust the import path based on your project structure.
from regex_generation.db.models import (
    CandidateRegexMetric, GroundTruthMetric,
    LlmGeneratedCandidate, LlmGenerationQuery, LlmGenerationTask,
    SynthesizerGeneratedCandidate, SynthesizerGenerationQuery, SynthesizerGenerationTask,
    RbeGeneratedCandidate, RbeGenerationQuery, RbeGenerationTask
)

from analysis.analysis_targets import DISTINCT_FEATURES_TARGETS

GT_DISTINCT_FEATURES_CACHE = {}

def get_gt_distinct_features_for_task(task):
    """
    Fetches the distinct features for a given task's ground truth.
    Assumes task object has a 'ground_truth' attribute to look up in GroundTruthMetric.
    """
    if not hasattr(task, 'ground_truth') or task.ground_truth is None:
        return None

    if task.ground_truth in GT_DISTINCT_FEATURES_CACHE:
        return GT_DISTINCT_FEATURES_CACHE[task.ground_truth]

    try:
        gt_metric = GroundTruthMetric.get(GroundTruthMetric.ground_truth == task.ground_truth)
        GT_DISTINCT_FEATURES_CACHE[task.ground_truth] = gt_metric.distinct_features
        return gt_metric.distinct_features
    except GroundTruthMetric.DoesNotExist:
        GT_DISTINCT_FEATURES_CACHE[task.ground_truth] = None
        return None

def analyze_and_plot(targets):
    """Queries the database, analyzes distinct features, and generates box plots."""
    print("Starting distinct features analysis...")

    id_to_target_name = {v: k for k, v in targets.items()}

    # --- Data Holders ---
    # Holds lists of AVG distinct features per query for each target
    avg_distinct_features_by_target = defaultdict(list)
    # Holds lists of (avg_candidate_length - gt_length) for each query
    diffs_by_target = defaultdict(list)
    variances_by_target = defaultdict(list)

    # 1. Get Ground Truth distinct features
    print("Fetching ground truth distinct features...")
    ground_truth_distinct_features = [
        gt.distinct_features for gt in
        GroundTruthMetric.select(GroundTruthMetric.distinct_features)
        .where(GroundTruthMetric.distinct_features.is_null(False))
    ]

    # --- Process each query type ---
    query_types = {
        'llm': (LlmGenerationQuery, 'experiment_id'),
        'synthesizer': (SynthesizerGenerationQuery, 'experiment_id'),
        'rbe': (RbeGenerationQuery, 'experiment_id')
    }

    print("Fetching and processing candidate metrics...")
    for query_model, param_key in query_types.values():
        queries = query_model.select()

        for query in queries:
            if not query.query_parameters: continue

            target_id = query.query_parameters.get(param_key).split('_')[-1]
            target_name = id_to_target_name.get(target_id)

            if not target_name:
                continue

            gt_distinct_features = get_gt_distinct_features_for_task(query.task)

            query_distinct_features = []
            for candidate in query.candidates:
                if isinstance(candidate, LlmGeneratedCandidate):
                    fk_field = CandidateRegexMetric.llm_candidate
                elif isinstance(candidate, SynthesizerGeneratedCandidate):
                    fk_field = CandidateRegexMetric.synthesizer_candidate
                elif isinstance(candidate, RbeGeneratedCandidate):
                    fk_field = CandidateRegexMetric.rbe_candidate
                else:
                    continue

                metric_query = (CandidateRegexMetric
                                .select(CandidateRegexMetric.distinct_features)
                                .where(fk_field == candidate.id))

                for metric in metric_query:
                    if metric.distinct_features is not None:
                        query_distinct_features.append(metric.distinct_features)

            # --- MODIFICATION: Process per-query average ---
            if query_distinct_features:
                avg_distinct_features = sum(query_distinct_features) / len(query_distinct_features)
                avg_distinct_features_by_target[target_name].append(avg_distinct_features)

                if gt_distinct_features is not None:
                    diff = avg_distinct_features - gt_distinct_features
                    diffs_by_target[target_name].append(diff)

                # NEW: Calculate variance for this query
                if len(query_distinct_features) > 1: # Variance needs at least 2 points
                    variance = np.var(query_distinct_features)
                    variances_by_target[target_name].append(variance)

    # --- Plotting ---
    print("Generating plot...")

    target_names = list(targets.keys())
    fig, ax = plt.subplots(figsize=(5, 3))
    ax2 = ax.twinx() # NEW: Create a second y-axis for variance
    # ax2.set_yscale('log')

    # Initialize plot objects to handle cases where data might be missing
    bp_len, bp_diff, bp_var = None, None, None

    # Plot Ground Truth first
    bp_gt = ax.boxplot([ground_truth_distinct_features], positions=[1], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                       boxprops=dict(facecolor='lightgray'),
                       medianprops=dict(color='black'))

    # Plot pairs of box plots for each target
    positions = []
    labels = ["Ground Truth"]
    current_pos = 3

    for name in target_names:
        avg_distinct_features = avg_distinct_features_by_target[name]
        diffs = diffs_by_target[name]
        variances = variances_by_target[name]

        # Add data to plot only if it exists
        if avg_distinct_features:
             bp_len = ax.boxplot([avg_distinct_features], positions=[current_pos], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                                 boxprops=dict(facecolor='skyblue'),
                                 medianprops=dict(color='darkblue'))
        if diffs:
            bp_diff = ax.boxplot([diffs], positions=[current_pos + 1], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                                 boxprops=dict(facecolor='lightgreen'),
                                 medianprops=dict(color='darkgreen'))
        if variances:
            bp_var = ax2.boxplot([variances], positions=[current_pos + 2], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                                 boxprops=dict(facecolor='lightcoral'),
                                 medianprops=dict(color='darkred'))

        positions.append(current_pos + 1)
        labels.append(name)
        current_pos += 4

    # ax.set_title('Average Pattern Length Distribution and Difference from Ground Truth')
    ax.set_ylabel('Avg. Distinct Features per Task')
    ax2.set_ylabel('Variance')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Configure x-axis ticks and labels
    print(positions)
    ax.set_xticks([1.5] + positions)
    ax.set_xticklabels(labels, ha='right', rotation=20)

    # Add a legend dynamically to avoid errors if a plot is missing
    legend_handles = [bp_gt["boxes"][0]]
    legend_labels = ['Ground Truth']
    if bp_len:
        legend_handles.append(bp_len["boxes"][0])
        legend_labels.append('Avg. Candidate Distinct Features')
    if bp_diff:
        legend_handles.append(bp_diff["boxes"][0])
        legend_labels.append('Avg. Difference')
    if bp_var:
        legend_handles.append(bp_var["boxes"][0])
        legend_labels.append('Set Variance')

    # ax.legend(legend_handles, legend_labels, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.5))
    # Hide legend
    ax.legend().set_visible(False)
    # Limit y axis to 100
    ax.set_ylim(-6, 10)

    # For debug print the plot size
    print(f"Plot size: {fig.get_size_inches()}")

    # fig.tight_layout()
    plt.savefig('distinct_features_comparison_plot.png', dpi=300)
    print("Plot saved to distinct_features_comparison_plot.png")

# =============================================
# Main Execution
# =============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze distinct features distributions from a database."
    )
    parser.add_argument(
        "--db-path", type=str, help="Path to the SQLite database file."
    )
    args = parser.parse_args()

    db = SqliteDatabase(args.db_path)

    models_to_bind = [
        CandidateRegexMetric, GroundTruthMetric,
        LlmGeneratedCandidate, LlmGenerationQuery, LlmGenerationTask,
        SynthesizerGeneratedCandidate, SynthesizerGenerationQuery, SynthesizerGenerationTask,
        RbeGeneratedCandidate, RbeGenerationQuery, RbeGenerationTask
    ]
    for model in models_to_bind:
        model._meta.database = db

    targets = DISTINCT_FEATURES_TARGETS

    try:
        db.connect()
        print(f"Successfully connected to database at {args.db_path}")
        analyze_and_plot(targets)
    except ImportError as e:
        print(f"Error: Could not import a model from 'db.models'. Please check your import paths. Details: {e}")
    except OperationalError as e:
        print(f"An error occurred with the database operation: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if not db.is_closed():
            db.close()
            print("Database connection closed.")


