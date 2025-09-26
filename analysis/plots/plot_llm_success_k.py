import argparse
from peewee import SqliteDatabase
import matplotlib.pyplot as plt
import scienceplots
import numpy as np
import os,sys
from analysis.analysis_targets import LLMS

# Models are available from db.models as per the user's request.
from regex_generation.db.models import LlmGenerationQuery, LlmGenerationAttempt

plt.style.use(['science', 'ieee', 'vibrant'])
# Use linux libertine font
plt.rcParams.update({
    "font.family": "Linux Libertine O",})


# =============================================
# Analysis and Plotting
# =============================================
def analyze_and_plot(models):
    """Queries the database, calculates success@k, and generates a plot."""
    print("Starting analysis...")

    # Invert models dict for easy lookup
    id_to_model_name = {v: k for k, v in models.items()}

    # Dictionary to hold lists of success values (1 or 0) for each model
    results = {name: {'s1': [], 's2': [], 's3': []} for name in models.keys()}

    # Fetch all queries and their attempts efficiently
    queries = LlmGenerationQuery.select()
    # Fetch attempts as model instances to avoid dictionary key ambiguity.
    attempts = (LlmGenerationAttempt.select(LlmGenerationAttempt.query, LlmGenerationAttempt.status, LlmGenerationAttempt.attempt_number)
                .order_by(LlmGenerationAttempt.attempt_number))

    # Group attempts by query_id for quick access
    query_attempts = {}
    for attempt in attempts:
        # Access the foreign key ID directly from the model instance.
        qid = attempt.query_id
        if qid not in query_attempts:
            query_attempts[qid] = []
        # Re-create a dictionary structure for the logic below.
        query_attempts[qid].append({
            'status': attempt.status,
            'attempt_number': attempt.attempt_number
        })


    # Process each query
    for query in queries:
        experiment_id = query.query_parameters.get('experiment_id').split('_')[-1]
        model_name = id_to_model_name.get(experiment_id)

        if not model_name:
            continue

        first_success_attempt = float('inf')

        # Find the first successful attempt for the current query
        for attempt in query_attempts.get(query.id, []):
            if attempt['status'] == 'success':
                first_success_attempt = attempt['attempt_number']
                break

        # Calculate success@k and append the result (1 or 0)
        results[model_name]['s1'].append(1 if first_success_attempt <= 1 else 0)
        results[model_name]['s2'].append(1 if first_success_attempt <= 2 else 0)
        results[model_name]['s3'].append(1 if first_success_attempt <= 3 else 0)

    # Calculate the average success@k for each model
    avg_results = {}
    for name, data in results.items():
        # Avoid division by zero if a model had no queries
        total_queries = len(data['s1'])
        if total_queries > 0:
            avg_results[name] = {
                'avg_s1': sum(data['s1']) / total_queries,
                'avg_s2': sum(data['s2']) / total_queries,
                'avg_s3': sum(data['s3']) / total_queries,
            }

    # --- Plotting ---
    print("Generating plot...")
    # Filter out models with no results to avoid plotting errors
    filtered_avg_results = {k: v for k, v in avg_results.items() if v}

    model_names = list(filtered_avg_results.keys())
    s1_scores = [d['avg_s1'] for d in filtered_avg_results.values()]
    s2_scores = [d['avg_s2'] for d in filtered_avg_results.values()]
    s3_scores = [d['avg_s3'] for d in filtered_avg_results.values()]

    x = np.arange(len(model_names))  # the label locations
    width = 0.25  # the width of the bars

    fig, ax = plt.subplots(figsize=(5, 2.5))
    # fig, ax = plt.subplots()
    rects1 = ax.bar(x - width, s1_scores, width, label='success@1')
    rects2 = ax.bar(x, s2_scores, width, label='success@2')
    rects3 = ax.bar(x + width, s3_scores, width, label='success@3')

    # Add some text for labels, title and axes ticks
    ax.set_ylabel('Avg. Task Success Rate at Attempt $\\mathit{k}$')
    # ax.set_title('Model Performance: Average Success@k')
    ax.set_xticks(x)
    ax.set_xticklabels(model_names, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Set y-axis limits
    ax.set_ylim(0, 1)

    # Add labels on top of bars
    # ax.bar_label(rects1, padding=3, fmt='%.2f', fontsize=8)
    # ax.bar_label(rects2, padding=3, fmt='%.2f', fontsize=8)
    # ax.bar_label(rects3, padding=3, fmt='%.2f', fontsize=8)

    # fig.tight_layout()

    # For debug print the plot size
    print(f"Plot size: {fig.get_size_inches()}")

    # Compact legend above the plot
    ax.legend(
        loc='upper right',
        bbox_to_anchor=(1.00, 1.00),
        ncol=1,
        # frameon=False,
        handletextpad=0.3,  # Reduce padding between handle and text
        columnspacing=0.8,  # Reduce space between columns
        handleheight=0.5,  # Shrink the height of the legend symbols
        handlelength=1.0,  # Reduce the length of the legend markers
        fontsize='small'
    )

    # Save the plot to a file
    pwd = os.path.dirname(os.path.abspath(__file__))
    plt.savefig(pwd + '/success_at_k_plot.png', dpi=300)
    print("Plot saved to success_at_k_plot.png")
    # plt.show() # Uncomment to display the plot directly


# =============================================
# Main Execution
# =============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze model success rates from a real database."
    )
    parser.add_argument(
        "--db-path", type=str, help="Path to the SQLite database file."
    )
    args = parser.parse_args()

    db = SqliteDatabase(args.db_path)

    # Bind the imported models to the database instance at runtime.
    LlmGenerationQuery._meta.database = db
    LlmGenerationAttempt._meta.database = db

    try:
        db.connect()
        print(f"Successfully connected to database at {args.db_path}")
        analyze_and_plot(LLMS)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # The correct method to check if the connection is open is `not db.is_closed()`
        if not db.is_closed():
            db.close()
            print("Database connection closed.")

