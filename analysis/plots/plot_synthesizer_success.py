import argparse
from peewee import SqliteDatabase, DoesNotExist
import matplotlib.pyplot as plt
import scienceplots
import numpy as np

import os,sys
from analysis.analysis_targets import SYNTHESIZERS

# It is assumed these models are available from a 'db.models' module.
# You might need to adjust the import path based on your project structure.
from regex_generation.db.models import SynthesizerGenerationQuery, SynthesizerGeneratedCandidate

plt.style.use(['science', 'ieee', 'vibrant'])
# Use linux libertine font
plt.rcParams.update({
    "font.family": "Linux Libertine O",})


# =============================================
# Analysis and Plotting
# =============================================
def analyze_and_plot(synthesizers):
    """Queries the database, calculates success rates, and generates a plot."""
    print("Starting synthesizer analysis...")

    id_to_synthesizer_name = {v: k for k, v in synthesizers.items()}
    results = {name: {'successful_queries': 0, 'total_queries': 0} for name in synthesizers.keys()}

    # A more efficient way to find successful queries is to get all candidates
    # with accuracy = 1 and then find their unique parent query IDs.
    successful_query_ids = {
        candidate.query_id for candidate in
        SynthesizerGeneratedCandidate.select(SynthesizerGeneratedCandidate.query)
        .where(SynthesizerGeneratedCandidate.accuracy == 1)
    }

    # Now, iterate through all queries to count totals and successes per synthesizer
    all_queries = SynthesizerGenerationQuery.select()

    for query in all_queries:
        # The synthesizer ID is expected in the 'query_parameters' JSON field
        synthesizer_id = query.query_parameters.get('experiment_id').split('_')[-1]
        synthesizer_name = id_to_synthesizer_name.get(synthesizer_id)

        if not synthesizer_name:
            continue

        results[synthesizer_name]['total_queries'] += 1
        if query.id in successful_query_ids:
            results[synthesizer_name]['successful_queries'] += 1

    # --- Calculate Averages ---
    avg_results = {}
    for name, data in results.items():
        total = data['total_queries']
        if total > 0:
            avg_results[name] = data['successful_queries'] / total
        else:
            avg_results[name] = 0

    # --- Plotting ---
    print("Generating plot...")
    synthesizer_names = list(avg_results.keys())
    success_rates = list(avg_results.values())

    x = np.arange(len(synthesizer_names))
    width = 0.5

    fig, ax = plt.subplots(figsize=(2, 1.5))
    rects = ax.bar(x, success_rates, width, label='success@1')

    ax.set_ylabel('Avg. Task Success Rate')
    # ax.set_title('Synthesizer Performance: success@1')
    ax.set_xticks(x)
    ax.set_xticklabels(synthesizer_names)
    # ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_ylim(0, 1)

    # ax.bar_label(rects, padding=3, fmt='%.2f')

    # fig.tight_layout()

    # For debug print the plot size
    print(f"Plot size: {fig.get_size_inches()}")

    # Compact legend above the plot
    # ax.legend(
    #     loc='upper right',
    #     bbox_to_anchor=(1.10, 1.20),
    #     ncol=1,
    #     # frameon=False,
    #     handletextpad=0.3,  # Reduce padding between handle and text
    #     columnspacing=0.8,  # Reduce space between columns
    #     handleheight=0.5,  # Shrink the height of the legend symbols
    #     handlelength=1.0,  # Reduce the length of the legend markers
    #     fontsize='small'
    # )

    # Hide legend
    ax.legend().set_visible(False)

    pwd = os.path.dirname(os.path.abspath(__file__))
    plt.savefig(pwd + '/synthesizer_success_rate_plot.pdf', dpi=600)
    print("Plot saved to synthesizer_success_rate_plot.pdf")
    # plt.show()


# =============================================
# Main Execution
# =============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze synthesizer success rates from a database."
    )
    parser.add_argument(
        "--db-path", type=str, help="Path to the SQLite database file."
    )
    args = parser.parse_args()

    db = SqliteDatabase(args.db_path)

    # Bind models to the database instance at runtime.
    SynthesizerGenerationQuery._meta.database = db
    SynthesizerGeneratedCandidate._meta.database = db

    try:
        db.connect()
        print(f"Successfully connected to database at {args.db_path}")
        analyze_and_plot(SYNTHESIZERS)
    except ImportError:
        print("Error: Could not import models from 'db.models'.")
        print("Please ensure the script is run from a location where 'db.models' is accessible.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if not db.is_closed():
            db.close()
            print("Database connection closed.")
