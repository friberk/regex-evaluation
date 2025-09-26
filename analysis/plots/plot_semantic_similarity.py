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
    CandidateRegexMetric,
    LlmGeneratedCandidate, LlmGenerationQuery,
    SynthesizerGeneratedCandidate, SynthesizerGenerationQuery,
    RbeGeneratedCandidate, RbeGenerationQuery
)
# Re-using the targets from the previous analysis for consistency
from analysis.analysis_targets import SEMANTIC_SIMILARITY_TARGETS

def analyze_and_plot_similarity(targets):
    """Queries the database, analyzes semantic similarity, and generates box plots."""
    print("Starting semantic similarity analysis...")

    id_to_target_name = {v: k for k, v in targets.items()}

    # Data Holder: Holds lists of AVG similarity scores per query for each target
    avg_similarity_by_target = defaultdict(list)

    # --- Process each query type ---
    query_types = {
        'llm': (LlmGenerationQuery, 'experiment_id'),
        'synthesizer': (SynthesizerGenerationQuery, 'experiment_id'),
        'rbe': (RbeGenerationQuery, 'experiment_id')
    }

    print("Fetching and processing candidate metrics for semantic similarity...")
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

                # Query for the semantic_similarity JSON field
                metric_query = (CandidateRegexMetric
                                .select(CandidateRegexMetric.semantic_similarity)
                                .where(fk_field == candidate.id))

                for metric in metric_query:
                    if metric.semantic_similarity:
                        try:
                            similarity_data = metric.semantic_similarity
                            if isinstance(similarity_data, str):
                                similarity_data = json.loads(similarity_data)

                            # NOTE: Assuming the key is 'cosine_similarity'. Change if needed.
                            score = similarity_data.get('f1_matchset')
                            if score is not None:
                                query_similarities.append(float(score))
                        except (json.JSONDecodeError, TypeError, AttributeError):
                            # Ignore malformed JSON or non-dict data
                            continue

            # Calculate the average similarity for this query and store it
            if query_similarities:
                avg_sim = sum(query_similarities) / len(query_similarities)
                avg_similarity_by_target[target_name].append(avg_sim)

    # --- Plotting ---
    print("Generating plot...")

    target_names = list(targets.keys())

    # Prepare data and labels for plotting
    data_to_plot = [avg_similarity_by_target.get(name, []) for name in target_names]
    labels = target_names

    fig, ax = plt.subplots()
    ax.boxplot(data_to_plot, patch_artist=True, showfliers=False, widths=0.4, whis=(10, 90),
                                boxprops=dict(facecolor='skyblue'),
                                medianprops=dict(color='darkblue'))

    ax.set_ylabel('Avg. Semantic Sim. per Task')
    ax.set_xticklabels(labels, rotation=20, ha='right')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Similarity scores are typically between 0 and 1
    ax.set_ylim(0, 1.05)

    fig.tight_layout()
    plt.savefig('semantic_similarity_plot.png', dpi=300)
    print("Plot saved to semantic_similarity_plot.png")

# =============================================
# Main Execution
# =============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze semantic similarity distributions from a database."
    )
    parser.add_argument(
        "--db-path", type=str, help="Path to the SQLite database file."
    )
    args = parser.parse_args()

    db = SqliteDatabase(args.db_path)

    # Bind all necessary models to the database instance
    models_to_bind = [
        CandidateRegexMetric, LlmGeneratedCandidate, LlmGenerationQuery,
        SynthesizerGeneratedCandidate, SynthesizerGenerationQuery,
        RbeGeneratedCandidate, RbeGenerationQuery
    ]
    for model in models_to_bind:
        model._meta.database = db

    targets = SEMANTIC_SIMILARITY_TARGETS

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
