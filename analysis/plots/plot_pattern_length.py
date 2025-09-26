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

from analysis.analysis_targets import PATTERN_LENGTH_TARGETS

# A cache to store ground truth lengths to avoid redundant DB queries
GT_LENGTH_CACHE = {}

def get_gt_length_for_task(task):
    """
    Fetches the pattern length for a given task's ground truth.
    Assumes task object has a 'ground_truth' attribute to look up in GroundTruthMetric.
    """
    if not hasattr(task, 'ground_truth') or task.ground_truth is None:
        return None

    if task.ground_truth in GT_LENGTH_CACHE:
        return GT_LENGTH_CACHE[task.ground_truth]

    try:
        gt_metric = GroundTruthMetric.get(GroundTruthMetric.ground_truth == task.ground_truth)
        GT_LENGTH_CACHE[task.ground_truth] = gt_metric.pattern_length
        return gt_metric.pattern_length
    except GroundTruthMetric.DoesNotExist:
        GT_LENGTH_CACHE[task.ground_truth] = None
        return None

def analyze_and_plot(targets):
    """Queries the database, analyzes pattern lengths, and generates box plots."""
    print("Starting pattern length analysis...")

    id_to_target_name = {v: k for k, v in targets.items()}

    # --- Data Holders ---
    avg_lengths_by_target = defaultdict(list)
    diffs_by_target = defaultdict(list)
    # NEW: Holds lists of variance of candidate lengths for each query
    variances_by_target = defaultdict(list)


    # 1. Get Ground Truth pattern lengths
    print("Fetching ground truth pattern lengths...")
    ground_truth_lengths = [
        gt.pattern_length for gt in
        GroundTruthMetric.select(GroundTruthMetric.pattern_length)
        .where(GroundTruthMetric.pattern_length.is_null(False))
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

            target_id_full = query.query_parameters.get(param_key)
            if not target_id_full: continue

            target_id = target_id_full.split('_')[-1]
            target_name = id_to_target_name.get(target_id)

            if not target_name:
                continue

            gt_length = get_gt_length_for_task(query.task)

            query_candidate_lengths = []
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
                                .select(CandidateRegexMetric.pattern_length)
                                .where(fk_field == candidate.id))

                for metric in metric_query:
                    if metric.pattern_length is not None:
                        query_candidate_lengths.append(metric.pattern_length)

            if query_candidate_lengths:
                avg_candidate_length = sum(query_candidate_lengths) / len(query_candidate_lengths)
                avg_lengths_by_target[target_name].append(avg_candidate_length)

                if gt_length is not None:
                    diff = avg_candidate_length - gt_length
                    diffs_by_target[target_name].append(diff)

                # NEW: Calculate variance for this query
                if len(query_candidate_lengths) > 1: # Variance needs at least 2 points
                    variance = np.var(query_candidate_lengths)
                    variances_by_target[target_name].append(variance)


    # --- Plotting ---
    print("Generating plot...")

    target_names = list(targets.keys())
    fig, ax = plt.subplots(figsize=(5, 3))
    ax2 = ax.twinx() # NEW: Create a second y-axis for variance
    ax2.set_yscale('log')

    # Initialize plot objects to handle cases where data might be missing
    bp_len, bp_diff, bp_var = None, None, None

    # Plot Ground Truth first
    bp_gt = ax.boxplot([ground_truth_lengths], positions=[1], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                       boxprops=dict(facecolor='lightgray'),
                       medianprops=dict(color='black'))

    # Plot groups of three box plots for each target
    positions = []
    labels = ["Ground Truth"]
    current_pos = 3

    for name in target_names:
        avg_lengths = avg_lengths_by_target[name]
        diffs = diffs_by_target[name]
        variances = variances_by_target[name]

        if avg_lengths:
             bp_len = ax.boxplot([avg_lengths], positions=[current_pos], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                                 boxprops=dict(facecolor='skyblue'),
                                 medianprops=dict(color='darkblue'))
        if diffs:
            bp_diff = ax.boxplot([diffs], positions=[current_pos + 1], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                                 boxprops=dict(facecolor='lightgreen'),
                                 medianprops=dict(color='darkgreen'))
        # NEW: Plot variance on the second axis
        if variances:
            bp_var = ax2.boxplot([variances], positions=[current_pos + 2], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                                 boxprops=dict(facecolor='lightcoral'),
                                 medianprops=dict(color='darkred'))

        positions.append(current_pos + 1) # Position label in the middle of the group
        labels.append(name)
        current_pos += 4 # Increment for a group of 3 plots + space

    ax.set_ylabel('Avg. Pattern Length per Task')
    ax.set_ylim(-100, 100)
    ax2.set_ylabel('Variance')
    # ax2.set_ylim(1, 5000)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Configure x-axis ticks and labels
    ax.set_xticks([1] + positions)
    ax.set_xticklabels(labels, ha='right', rotation=20)

    # Add a legend dynamically
    legend_handles = [bp_gt["boxes"][0]]
    legend_labels = ['Ground Truth']
    if bp_len:
        legend_handles.append(bp_len["boxes"][0])
        legend_labels.append('Avg. Length')
    if bp_diff:
        legend_handles.append(bp_diff["boxes"][0])
        legend_labels.append('Avg. Difference')
    if bp_var:
        legend_handles.append(bp_var["boxes"][0])
        legend_labels.append('Set Variance')

    # ax.legend(legend_handles, legend_labels, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.5))
    # Hide legend
    ax.legend().set_visible(False)

    fig.tight_layout()
    plt.savefig('pattern_length_comparison_plot.png', dpi=300, bbox_inches='tight')
    print("Plot saved to pattern_length_comparison_plot.png")

# =============================================
# Main Execution
# =============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze pattern length distributions from a database."
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

    targets = PATTERN_LENGTH_TARGETS

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
