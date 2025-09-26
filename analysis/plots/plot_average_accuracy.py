import argparse
from peewee import SqliteDatabase, OperationalError
import matplotlib.pyplot as plt
from collections import defaultdict
import scienceplots

plt.style.use(['science', 'nature', 'vibrant'])
# Use linux libertine font
plt.rcParams.update({
    "font.family": "Linux Libertine O",
})

# It is assumed these models are available from a 'db.models' module.
from regex_generation.db.models import (
    LlmGeneratedCandidate, LlmGenerationQuery, LlmGenerationTask,
    SynthesizerGeneratedCandidate, SynthesizerGenerationQuery, SynthesizerGenerationTask,
    RbeGeneratedCandidate, RbeGenerationQuery, RbeGenerationTask
)
# Using the same set of targets for consistency
from analysis.analysis_targets import AUTOMATON_SIZE_TARGETS as ACCURACY_TARGETS

def analyze_and_plot(targets):
    """
    Queries the database to analyze the average accuracy of candidates per task
    and generates box plots.
    """
    print("Starting average accuracy per task analysis...")

    id_to_target_name = {v: k for k, v in targets.items()}

    # --- Data Holder ---
    # This will hold all candidate accuracies grouped by target and then by task.
    # Structure: { 'target_name': { 'task_id': [acc1, acc2, ...], ... }, ... }
    accuracies_by_task_by_target = defaultdict(lambda: defaultdict(list))
    # To track unique (regex, accuracy) pairs per task for each target
    seen_candidates_by_task = defaultdict(set)

    # --- Process each query type ---
    query_types = {
        'llm': (LlmGenerationQuery, 'experiment_id'),
        'synthesizer': (SynthesizerGenerationQuery, 'experiment_id'),
        'rbe': (RbeGenerationQuery, 'experiment_id')
    }

    print("Fetching and processing candidate accuracies...")
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

            task_id = query.task_id

            # Tweak: If a query has no candidates, treat it as one candidate with 0 accuracy.
            if not query.candidates.exists():
                accuracies_by_task_by_target[target_name][task_id].append(0.0)
            else:
                for candidate in query.candidates:
                    if candidate.accuracy is not None:
                        # Check for uniqueness of (regex, accuracy) pair within the task
                        candidate_tuple = (candidate.regex_pattern, float(candidate.accuracy))
                        if candidate_tuple not in seen_candidates_by_task[(target_name, task_id)]:
                            accuracies_by_task_by_target[target_name][task_id].append(float(candidate.accuracy))
                            seen_candidates_by_task[(target_name, task_id)].add(candidate_tuple)

    # --- Calculate average accuracy for each task ---
    avg_accuracy_per_task_by_target = defaultdict(list)
    for target, tasks in accuracies_by_task_by_target.items():
        for task_id, accuracies in tasks.items():
            if accuracies:
                avg_accuracy = sum(accuracies) / len(accuracies)
                avg_accuracy_per_task_by_target[target].append(avg_accuracy)

    # --- Plotting ---
    print("Generating plot...")

    target_names = list(targets.keys())

    # Prepare data and labels for plotting
    data_to_plot = [avg_accuracy_per_task_by_target.get(name, []) for name in target_names]
    labels = target_names

    fig, ax = plt.subplots()
    ax.boxplot(data_to_plot, patch_artist=True, showfliers=False, widths=0.4, whis=(10, 90))

    ax.set_ylabel('Avg. Accuracy per Task')
    ax.set_xticklabels(labels, rotation=20, ha='right')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Accuracy is between 0 and 1
    ax.set_ylim(0, 1.05)

    fig.tight_layout()
    plt.savefig('average_accuracy_per_task_plot.png', dpi=300)
    print("Plot saved to average_accuracy_per_task_plot.png")

# =============================================
# Main Execution
# =============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze average candidate accuracy per task from a database."
    )
    parser.add_argument(
        "--db-path", type=str, help="Path to the SQLite database file."
    )
    args = parser.parse_args()

    db = SqliteDatabase(args.db_path)

    models_to_bind = [
        LlmGeneratedCandidate, LlmGenerationQuery, LlmGenerationTask,
        SynthesizerGeneratedCandidate, SynthesizerGenerationQuery, SynthesizerGenerationTask,
        RbeGeneratedCandidate, RbeGenerationQuery, RbeGenerationTask
    ]
    for model in models_to_bind:
        model._meta.database = db

    targets = ACCURACY_TARGETS

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
