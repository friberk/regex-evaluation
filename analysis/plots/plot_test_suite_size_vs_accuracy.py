import argparse
import json
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
from analysis.analysis_targets import TEST_SUITE_SIZE_TARGETS

def analyze_and_plot(targets):
    """
    Queries the database to analyze success@1 rate vs. test suite size
    and generates a line plot.
    """
    print("Starting success rate vs. test suite size analysis...")

    id_to_target_name = {v: k for k, v in targets.items()}

    # --- Data Holder ---
    # Structure: { target_name: { suite_size: {'total': 0, 'successful': 0} } }
    results = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'successful': 0}))

    # --- Process each query type ---
    query_types = {
        'llm': (LlmGenerationQuery, 'experiment_id'),
        'synthesizer': (SynthesizerGenerationQuery, 'experiment_id'),
        'rbe': (RbeGenerationQuery, 'experiment_id')
    }

    print("Fetching and processing queries...")
    for query_model, param_key in query_types.values():
        # *** FIX: Removing prefetch to avoid the foreign key error.
        # This will use lazy-loading instead, which is more robust here.
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

            # Calculate test suite size from the task (lazy-loaded)
            task = query.task
            if not task or not hasattr(task, 'positive_examples') or not hasattr(task, 'negative_examples'):
                continue

            suite_size = len(task.positive_examples) + len(task.negative_examples)

            # Check for success@1 (at least one candidate has accuracy 1.0)
            is_successful = False
            # Candidates will be lazy-loaded here
            for candidate in query.candidates:
                if candidate.accuracy is not None and candidate.accuracy == 1.0:
                    is_successful = True
                    break

            results[target_name][suite_size]['total'] += 1
            if is_successful:
                results[target_name][suite_size]['successful'] += 1

    # --- Plotting ---
    print("Generating plot...")
    fig, ax = plt.subplots(figsize=(4, 2))

    # Remove the grid
    ax.grid(False)

    # Define distinct styles
    line_styles = {
        "GPT-5": ("--", None),
        "gpt-oss-120b": ("-.", None),
        "gpt-oss-20b": (":", None),
        "RFixer": ("--", None),
        "RbE-All": ("-.", None)
    }

    for target_name in targets.keys():
        if target_name not in results:
            print(f"Warning: No data found for target '{target_name}'. Skipping plot.")
            continue

        target_data = results[target_name]

        # Sort data by test suite size for a clean line plot
        sorted_sizes = sorted(target_data.keys())

        success_rates = []
        for size in sorted_sizes:
            total = target_data[size]['total']
            successful = target_data[size]['successful']
            rate = (successful / total) if total > 0 else 0
            success_rates.append(rate)

        if target_name == 'RbE-All':
            linestyle, marker = line_styles[target_name]
            ax.plot(sorted_sizes, success_rates, marker=marker, linestyle=linestyle, label=target_name, markersize=1, color='green')
        else:
            linestyle, marker = line_styles[target_name]
            ax.plot(sorted_sizes, success_rates, marker=marker, linestyle=linestyle, label=target_name, markersize=1)

    ax.set_xlabel('Test Suite Size ($|P| + |N|$)')
    ax.set_ylabel('Task Success Rate')
    # ax.set_title('Avg. Task Success Rate vs. Test Suite Size')
    ax.legend()
    # ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.set_ylim(0, 1.05)
    # You might want to adjust xlim based on your data range
    # ax.set_xlim(left=0)

    # print size for debug
    print(f"Plot size: {fig.get_size_inches()}")

    # fig.tight_layout()
    plt.savefig('success_vs_test_suite_size_plot.png', dpi=300)
    print("Plot saved to success_vs_test_suite_size_plot.png")

# =============================================
# Main Execution
# =============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze Success@1 Rate vs. Test Suite Size from a database."
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

    targets = TEST_SUITE_SIZE_TARGETS

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

