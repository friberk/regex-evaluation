import argparse
from peewee import SqliteDatabase, DoesNotExist
import matplotlib.pyplot as plt
import scienceplots
import numpy as np

import os,sys
from analysis.analysis_targets import RBES, SYNTHESIZERS

from regex_generation.db.models import RbeGenerationQuery, RbeGeneratedCandidate

plt.style.use(['science', 'ieee', 'vibrant'])
# Use linux libertine font
plt.rcParams.update({
    "font.family": "Linux Libertine O",})


# =============================================
# Analysis and Plotting
# =============================================
def analyze_and_plot(rbes):
    """Queries the database, calculates success rates, and generates a plot."""
    print("Starting RbE analysis...")

    id_to_rbe_name = {v: k for k, v in rbes.items()}
    results = {name: {'successful_queries': 0, 'total_queries': 0} for name in rbes.keys()}

    # A more efficient way to find successful queries is to get all candidates
    # with accuracy = 1 and then find their unique parent query IDs.
    successful_query_ids = {
        candidate.query_id for candidate in
        RbeGeneratedCandidate.select(RbeGeneratedCandidate.query)
        .where(RbeGeneratedCandidate.accuracy == 1)
    }

    # Now, iterate through all queries to count totals and successes per RbE
    all_queries = RbeGenerationQuery.select()

    for query in all_queries:
        # The RbE ID is expected in the 'query_parameters' JSON field
        rbe_id = query.query_parameters.get('experiment_id').split('_')[-1]
        rbe_name = id_to_rbe_name.get(rbe_id)

        if not rbe_name:
            continue

        results[rbe_name]['total_queries'] += 1
        if query.id in successful_query_ids:
            results[rbe_name]['successful_queries'] += 1

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
    rbe_names = list(avg_results.keys())
    success_rates = list(avg_results.values())

    x = np.arange(len(rbe_names))
    width = 0.5

    fig, ax = plt.subplots(figsize=(2, 1.5))
    rects = ax.bar(x, success_rates, width, label='success@1')

    ax.set_ylabel('Avg. Task Success Rate')
    # ax.set_title('Synthesizer Performance: success@1')
    ax.set_xticks(x)
    ax.set_xticklabels(rbe_names)
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
    plt.savefig(pwd + '/rbe_success_rate_plot.pdf', dpi=600)
    print("Plot saved to rbe_success_rate_plot.pdf")
    # plt.show()


# =============================================
# Main Execution
# =============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze RbE success rates from a database."
    )
    parser.add_argument(
        "--db-path", type=str, help="Path to the SQLite database file."
    )
    args = parser.parse_args()

    db = SqliteDatabase(args.db_path)

    # Bind models to the database instance at runtime.
    RbeGenerationQuery._meta.database = db
    RbeGeneratedCandidate._meta.database = db

    try:
        db.connect()
        print(f"Successfully connected to database at {args.db_path}")
        analyze_and_plot(RBES)
    except ImportError:
        print("Error: Could not import models from 'db.models'.")
        print("Please ensure the script is run from a location where 'db.models' is accessible.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if not db.is_closed():
            db.close()
            print("Database connection closed.")
