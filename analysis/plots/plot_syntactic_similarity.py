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
    "font.family": "Linux Libertine O",})

# It is assumed these models are available from a 'db.models' module.
# You might need to adjust the import path based on your project structure.
from regex_generation.db.models import (
    CandidateRegexMetric,
    LlmGeneratedCandidate, LlmGenerationQuery,
    SynthesizerGeneratedCandidate, SynthesizerGenerationQuery,
    RbeGeneratedCandidate, RbeGenerationQuery
)
from analysis.analysis_targets import SYNTACTIC_SIMILARITY_TARGETS

def analyze_and_plot_similarity(targets):
    """Queries the database, analyzes syntactic similarity and variance, and generates box plots."""
    print("Starting syntactic similarity analysis...")

    id_to_target_name = {v: k for k, v in targets.items()}

    # --- Data Holders ---
    avg_similarity_by_target = defaultdict(list)
    # NEW: Holds lists of variance of similarity scores for each query
    variances_by_target = defaultdict(list)

    # --- Process each query type ---
    query_types = {
        'llm': (LlmGenerationQuery, 'experiment_id'),
        'synthesizer': (SynthesizerGenerationQuery, 'experiment_id'),
        'rbe': (RbeGenerationQuery, 'experiment_id')
    }

    print("Fetching and processing candidate metrics for syntactic similarity...")
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

            query_similarities = []
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
                                .select(CandidateRegexMetric.syntactic_similarity)
                                .where(fk_field == candidate.id))

                for metric in metric_query:
                    if metric.syntactic_similarity:
                        try:
                            similarity_data = metric.syntactic_similarity
                            if isinstance(similarity_data, str):
                                similarity_data = json.loads(similarity_data)

                            score = similarity_data.get('normalized_ast_edit_distance')
                            if score is not None:
                                query_similarities.append(float(score))
                        except (json.JSONDecodeError, TypeError, AttributeError):
                            continue

            if query_similarities:
                avg_sim = sum(query_similarities) / len(query_similarities)
                avg_similarity_by_target[target_name].append(avg_sim)

                # NEW: Calculate variance for this query
                if len(query_similarities) > 1:
                    variance = np.var(query_similarities)
                    variances_by_target[target_name].append(variance)

    # --- Plotting ---
    print("Generating plot...")

    target_names = list(targets.keys())
    fig, ax = plt.subplots()
    ax2 = ax.twinx() # NEW: Create a second y-axis for variance

    bp_sim, bp_var = None, None

    positions = []
    labels = []
    current_pos = 1

    for name in target_names:
        avg_similarities = avg_similarity_by_target[name]
        variances = variances_by_target[name]

        if avg_similarities:
            bp_sim = ax.boxplot([avg_similarities], positions=[current_pos], widths=0.3, patch_artist=True, showfliers=False, whis=(10, 90),
                                boxprops=dict(facecolor='skyblue'),
                                medianprops=dict(color='darkblue'))
        if variances:
            bp_var = ax2.boxplot([variances], positions=[current_pos + 0.4], widths=0.3, patch_artist=True, showfliers=False, whis=(10, 90),
                                 boxprops=dict(facecolor='lightcoral'),
                                 medianprops=dict(color='darkred'))

        positions.append(current_pos + 0.2)
        labels.append(name)
        current_pos += 2

    ax.set_ylabel('Avg. AST Edit Dist. per Task')
    ax2.set_ylabel('Variance')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=20, ha='right')

    ax.set_ylim(0, 1.05)
    # You might want to adjust the variance y-limit based on your data
    ax2.set_ylim(0, 0.1)

    # Add a legend dynamically
    legend_handles = []
    legend_labels = []
    if bp_sim:
        legend_handles.append(bp_sim["boxes"][0])
        legend_labels.append('Avg. AST Edit Distance')
    if bp_var:
        legend_handles.append(bp_var["boxes"][0])
        legend_labels.append('Set Variance')

    # ax.legend(legend_handles, legend_labels, loc='upper left', ncol=1, handletextpad=0.3, columnspacing=0.8, handleheight=0.5, handlelength=1.0, fontsize='small')
    # Hide legend
    ax.legend().set_visible(False)

    fig.tight_layout()
    plt.savefig('syntactic_similarity_variance_plot.png', dpi=300, bbox_inches='tight')
    print("Plot saved to syntactic_similarity_variance_plot.png")

# =============================================
# Main Execution
# =============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze syntactic similarity and variance from a database."
    )
    parser.add_argument(
        "--db-path", type=str, help="Path to the SQLite database file."
    )
    args = parser.parse_args()

    db = SqliteDatabase(args.db_path)

    models_to_bind = [
        CandidateRegexMetric, LlmGeneratedCandidate, LlmGenerationQuery,
        SynthesizerGeneratedCandidate, SynthesizerGenerationQuery,
        RbeGeneratedCandidate, RbeGenerationQuery
    ]
    for model in models_to_bind:
        model._meta.database = db

    targets = SYNTACTIC_SIMILARITY_TARGETS

    try:
        db.connect()
        print(f"Successfully connected to database at {args.db_path}")
        analyze_and_plot_similarity(targets)
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
