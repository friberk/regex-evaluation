import argparse
import json
from peewee import SqliteDatabase, OperationalError
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import scienceplots

plt.style.use(['science', 'nature', 'vibrant'])
# Use linux libertine font
plt.rcParams.update({
    "font.family": "Linux Libertine O",
})

# It is assumed these models are available from a 'db.models' module.
from regex_generation.db.models import (
    CandidateRegexMetric, GroundTruthMetric,
    LlmGeneratedCandidate, LlmGenerationQuery, LlmGenerationTask,
    SynthesizerGeneratedCandidate, SynthesizerGenerationQuery, SynthesizerGenerationTask,
    RbeGeneratedCandidate, RbeGenerationQuery, RbeGenerationTask
)
# Re-using the targets from the previous analysis as requested
from analysis.analysis_targets import AUTOMATON_SIZE_TARGETS

# A cache to store ground truth automaton sizes to avoid redundant DB queries
GT_AUTOMATON_SIZE_CACHE = {}

def get_gt_automaton_size_for_task(task):
    """
    Fetches the automaton size for a given task's ground truth.
    """
    if not hasattr(task, 'ground_truth') or task.ground_truth is None:
        return None

    if task.ground_truth in GT_AUTOMATON_SIZE_CACHE:
        return GT_AUTOMATON_SIZE_CACHE[task.ground_truth]

    try:
        gt_metric = GroundTruthMetric.get(GroundTruthMetric.ground_truth == task.ground_truth)
        if hasattr(gt_metric, 'automaton_size') and gt_metric.automaton_size:
            metrics_data = gt_metric.automaton_size
            if isinstance(metrics_data, str):
                metrics_data = json.loads(metrics_data)

            size = metrics_data.get('automaton_size')
            if size is not None:
                GT_AUTOMATON_SIZE_CACHE[task.ground_truth] = int(size)
                return int(size)
    except (GroundTruthMetric.DoesNotExist, json.JSONDecodeError, TypeError, AttributeError):
        pass

    GT_AUTOMATON_SIZE_CACHE[task.ground_truth] = None
    return None


def analyze_and_plot(targets):
    """
    Queries the database to analyze automaton size and generates box plots.
    """
    print("Starting automaton size analysis...")

    id_to_target_name = {v: k for k, v in targets.items()}

    # --- Data Holders ---
    avg_sizes_by_target = defaultdict(list)
    diffs_by_target = defaultdict(list)
    variances_by_target = defaultdict(list)

    # --- Fetch Ground Truth Automaton Sizes ---
    print("Fetching ground truth automaton sizes...")
    ground_truth_sizes = []
    for gt_metric in GroundTruthMetric.select():
        if hasattr(gt_metric, 'automaton_size') and gt_metric.automaton_size:
            try:
                metrics_data = gt_metric.automaton_size
                if isinstance(metrics_data, str):
                    metrics_data = json.loads(metrics_data)

                size = metrics_data.get('automaton_size')
                if size is not None:
                    ground_truth_sizes.append(int(size))
            except (json.JSONDecodeError, TypeError, AttributeError):
                continue

    # --- Process each query type ---
    query_types = {
        'llm': (LlmGenerationQuery, 'experiment_id'),
        'synthesizer': (SynthesizerGenerationQuery, 'experiment_id'),
        'rbe': (RbeGenerationQuery, 'experiment_id')
    }

    print("Fetching and processing candidate metrics for automaton size...")
    for query_model, param_key in query_types.values():
        for query in query_model.select():
            if not query.query_parameters:
                continue

            target_id_full = query.query_parameters.get(param_key)
            if not target_id_full:
                continue

            target_id = target_id_full.split('_')[-1]
            target_name = id_to_target_name.get(target_id)

            if not target_name:
                continue

            gt_size = get_gt_automaton_size_for_task(query.task)

            query_automaton_sizes = []
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
                                .select(CandidateRegexMetric.automaton_size)
                                .where(fk_field == candidate.id))

                for metric in metric_query:
                    if metric.automaton_size:
                        try:
                            automaton_size_data = metric.automaton_size
                            if isinstance(automaton_size_data, str):
                                 automaton_size_data = json.loads(automaton_size_data)

                            size = automaton_size_data.get('automaton_size')
                            if size is not None:
                                query_automaton_sizes.append(int(size))
                        except (json.JSONDecodeError, TypeError, AttributeError):
                            continue

            if query_automaton_sizes:
                avg_size = sum(query_automaton_sizes) / len(query_automaton_sizes)
                avg_sizes_by_target[target_name].append(avg_size)

                if gt_size is not None:
                    diff = avg_size - gt_size
                    diffs_by_target[target_name].append(diff)

                if len(query_automaton_sizes) > 1:
                    variance = np.var(query_automaton_sizes)
                    variances_by_target[target_name].append(variance)


    # --- Plotting ---
    print("Generating plot...")
    target_names = list(targets.keys())
    fig, ax = plt.subplots()
    ax2 = ax.twinx()  # Create a second y-axis for variance
    ax2.set_yscale('log')

    bp_gt, bp_size, bp_diff, bp_var = None, None, None, None

    # Plot Ground Truth
    if ground_truth_sizes:
        bp_gt = ax.boxplot([ground_truth_sizes], positions=[1], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                           boxprops=dict(facecolor='lightgray'), medianprops=dict(color='black'))

    positions = []
    labels = ["Ground Truth"]
    current_pos = 3

    for name in target_names:
        avg_sizes = avg_sizes_by_target.get(name, [])
        diffs = diffs_by_target.get(name, [])
        variances = variances_by_target.get(name, [])

        if avg_sizes:
            bp_size = ax.boxplot([avg_sizes], positions=[current_pos], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                                 boxprops=dict(facecolor='skyblue'), medianprops=dict(color='darkblue'))
        if diffs:
            bp_diff = ax.boxplot([diffs], positions=[current_pos + 1], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                                 boxprops=dict(facecolor='lightgreen'), medianprops=dict(color='darkgreen'))
        if variances:
            bp_var = ax2.boxplot([variances], positions=[current_pos + 2], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                                 boxprops=dict(facecolor='salmon'), medianprops=dict(color='darkred'))

        positions.append(current_pos + 1)
        labels.append(name)
        current_pos += 4

    ax.set_ylabel('Avg. Automaton Size per Task')
    ax2.set_ylabel('Variance')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    ax.set_xticks([1] + positions)
    ax.set_xticklabels(labels, rotation=20, ha='right')

    legend_handles, legend_labels = [], []
    if bp_gt:
        legend_handles.append(bp_gt["boxes"][0])
        legend_labels.append('Ground Truth')
    if bp_size:
        legend_handles.append(bp_size["boxes"][0])
        legend_labels.append('Avg. Automaton Size')
    if bp_diff:
        legend_handles.append(bp_diff["boxes"][0])
        legend_labels.append('Avg. Difference')
    if bp_var:
        legend_handles.append(bp_var["boxes"][0])
        legend_labels.append('Set Variance')

    # ax.legend(legend_handles, legend_labels, loc='upper center', bbox_to_anchor=(0.5, -0.3), ncol=2)
    # Hide legend
    ax.legend().set_visible(False)

    # fig.tight_layout()
    plt.savefig('automaton_size_plot.png', dpi=300, bbox_inches='tight')
    print("Plot saved to automaton_size_plot.png")

# =============================================
# Main Execution
# =============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze automaton size distributions from a database."
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

    targets = AUTOMATON_SIZE_TARGETS

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

