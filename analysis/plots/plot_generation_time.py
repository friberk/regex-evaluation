import argparse
from peewee import SqliteDatabase, OperationalError
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
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
from analysis.analysis_targets import AUTOMATON_SIZE_TARGETS as GENERATION_TIME_TARGETS

def analyze_and_plot(targets):
    """
    Queries the database to analyze generation time and number of candidates,
    and generates box plots.
    """
    print("Starting generation time analysis...")

    id_to_target_name = {v: k for k, v in targets.items()}

    # --- Data Holders ---
    # Holds lists of AVG generation times per query for each target
    avg_times_by_target = defaultdict(list)
    # Holds lists of the number of candidates per query for each target
    candidate_counts_by_target = defaultdict(list)


    # --- Process each query type ---
    query_types = {
        'llm': (LlmGenerationQuery, 'experiment_id'),
        'synthesizer': (SynthesizerGenerationQuery, 'experiment_id'),
        'rbe': (RbeGenerationQuery, 'experiment_id')
    }

    print("Fetching and processing candidate generation times...")
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

            query_generation_times = []
            for candidate in query.candidates:
                # generation_time is a direct attribute on the candidate models
                if candidate.generation_time is not None:
                    query_generation_times.append(candidate.generation_time)

            # Calculate avg time and count candidates for this query
            if query_generation_times:
                num_candidates = len(query_generation_times)
                candidate_counts_by_target[target_name].append(num_candidates)

                avg_time = sum(query_generation_times) / num_candidates
                avg_times_by_target[target_name].append(avg_time)

    # --- Plotting ---
    print("Generating plot...")

    target_names = list(targets.keys())
    fig, ax = plt.subplots()
    ax2 = ax.twinx()  # Create a second y-axis for candidate counts

    bp_time, bp_count = None, None
    positions = []
    labels = []
    current_pos = 1

    for name in target_names:
        avg_query_times = avg_times_by_target.get(name, [])
        candidate_counts = candidate_counts_by_target.get(name, [])

        if avg_query_times:
            bp_time = ax.boxplot([avg_query_times], positions=[current_pos], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                                 boxprops=dict(facecolor='skyblue'), medianprops=dict(color='darkblue'))
        if candidate_counts:
            # Plot candidate counts on the second axis
            bp_count = ax2.boxplot([candidate_counts], positions=[current_pos + 1], widths=0.6, patch_artist=True, showfliers=False, whis=(10, 90),
                                   boxprops=dict(facecolor='lightgreen'), medianprops=dict(color='darkgreen'))

        positions.append(current_pos + 0.5)
        labels.append(name)
        current_pos += 3

    ylab=ax.set_ylabel('Time Spent per Task (s)')
    # Move by -0.5 cm in display (screen) space, independent of axes size
    cm_to_in = 1/2.54
    offset = mtransforms.ScaledTranslation(0, -0.1*cm_to_in, fig.dpi_scale_trans)
    ylab.set_transform(ylab.get_transform() + offset)
    ax2.set_ylabel('\\# Candidates per Task')
    ax.grid(axis='y', which='both', linestyle='--', alpha=0.7)
    ax.set_yscale('log')

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=20, ha='right')

    # legend_handles, legend_labels = [], []
    # if bp_time:
    #     legend_handles.append(bp_time["boxes"][0])
    #     legend_labels.append('Avg. Time per Task')
    # if bp_count:
    #     legend_handles.append(bp_count["boxes"][0])
    #     legend_labels.append('Num. of Candidates per Task')

    # ax.legend(legend_handles, legend_labels, loc='upper center', bbox_to_anchor=(0.5, -0.35), ncol=2)

    # Hide legend
    ax.legend().set_visible(False)

    fig.tight_layout()
    plt.savefig('generation_time_vs_candidate_count_plot.png', dpi=300)
    print("Plot saved to generation_time_vs_candidate_count_plot.png")


# =============================================
# Main Execution
# =============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze generation time and candidate counts from a database."
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

    targets = GENERATION_TIME_TARGETS

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

