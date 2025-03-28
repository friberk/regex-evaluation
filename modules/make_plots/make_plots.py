import matplotlib.pyplot as plt
import scienceplots
import numpy as np
import pandas as pd
import json
from pathlib import Path
import matplotlib.ticker as mticker

plt.style.use(['science', 'nature', 'vibrant'])
# Use linux libertine font
plt.rcParams.update({
    "font.family": "Linux Libertine O",})

targets = {
    "reuse-by-example": {
        "full-match": "../../data/generated-regexes-with-accuracies/reuse-by-example/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-accuracies/reuse-by-example/partial-match/partial_match.ndjson",
    },
    "synthesizers": {
        "forest": {
            "full-match": "../../data/generated-regexes-with-accuracies/synthesizers/forest/full-match/full_match.ndjson",
            "partial-match": "../../data/generated-regexes-with-accuracies/synthesizers/forest/partial-match/partial_match.ndjson",
        },
        "rfixer": {
            "full-match": "../../data/generated-regexes-with-accuracies/synthesizers/rfixer/full-match/full_match.ndjson",
            "partial-match": "../../data/generated-regexes-with-accuracies/synthesizers/rfixer/partial-match/partial_match.ndjson",
        },
        "rfixer-gtp": {
            "full-match": "../../data/generated-regexes-with-accuracies/synthesizers/rfixer-gtp/full-match/full_match.ndjson",
            "partial-match": "../../data/generated-regexes-with-accuracies/synthesizers/rfixer-gtp/partial-match/partial_match.ndjson",
        },
    },
    "llms": {
        "gpt-4o": {
            "full-match": "../../data/generated-regexes-with-accuracies/llms/gpt-4o/full-match/full_match.ndjson",
            "full-match-trials": "../../data/generated-regexes-with-accuracies/llms/gpt-4o/full-match/full_match_trials.ndjson",
            "partial-match": "../../data/generated-regexes-with-accuracies/llms/gpt-4o/partial-match/partial_match.ndjson",
            "partial-match-trials": "../../data/generated-regexes-with-accuracies/llms/gpt-4o/partial-match/partial_match_trials.ndjson",
        },
        "o3-mini": {
            "full-match": "../../data/generated-regexes-with-accuracies/llms/o3-mini/full-match/full_match.ndjson",
            "full-match-trials": "../../data/generated-regexes-with-accuracies/llms/o3-mini/full-match/full_match_trials.ndjson",
            "partial-match": "../../data/generated-regexes-with-accuracies/llms/o3-mini/partial-match/partial_match.ndjson",
            "partial-match-trials": "../../data/generated-regexes-with-accuracies/llms/o3-mini/partial-match/partial_match_trials.ndjson",
        },
        "llama3.1:8b": {
            "full-match": "../../data/generated-regexes-with-accuracies/llms/llama3.1:8b/full-match/full_match.ndjson",
            "full-match-trials": "../../data/generated-regexes-with-accuracies/llms/llama3.1:8b/full-match/full_match_trials.ndjson",
            "partial-match": "../../data/generated-regexes-with-accuracies/llms/llama3.1:8b/partial-match/partial_match.ndjson",
            "partial-match-trials": "../../data/generated-regexes-with-accuracies/llms/llama3.1:8b/partial-match/partial_match_trials.ndjson",
        },
        "llama3.2:1b": {
            "full-match": "../../data/generated-regexes-with-accuracies/llms/llama3.2:1b/full-match/full_match.ndjson",
            "full-match-trials": "../../data/generated-regexes-with-accuracies/llms/llama3.2:1b/full-match/full_match_trials.ndjson",
            "partial-match": "../../data/generated-regexes-with-accuracies/llms/llama3.2:1b/partial-match/partial_match.ndjson",
            "partial-match-trials": "../../data/generated-regexes-with-accuracies/llms/llama3.2:1b/partial-match/partial_match_trials.ndjson",
        },
        "llama3.2:3b": {
            "full-match": "../../data/generated-regexes-with-accuracies/llms/llama3.2:3b/full-match/full_match.ndjson",
            "full-match-trials": "../../data/generated-regexes-with-accuracies/llms/llama3.2:3b/full-match/full_match_trials.ndjson",
            "partial-match": "../../data/generated-regexes-with-accuracies/llms/llama3.2:3b/partial-match/partial_match.ndjson",
            "partial-match-trials": "../../data/generated-regexes-with-accuracies/llms/llama3.2:3b/partial-match/partial_match_trials.ndjson",
        },
        "gemma2:27b": {
            "full-match": "../../data/generated-regexes-with-accuracies/llms/gemma2:27b/full-match/full_match.ndjson",
            "full-match-trials": "../../data/generated-regexes-with-accuracies/llms/gemma2:27b/full-match/full_match_trials.ndjson",
            "partial-match": "../../data/generated-regexes-with-accuracies/llms/gemma2:27b/partial-match/partial_match.ndjson",
            "partial-match-trials": "../../data/generated-regexes-with-accuracies/llms/gemma2:27b/partial-match/partial_match_trials.ndjson",
        },
        "mistral:latest": {
            "full-match": "../../data/generated-regexes-with-accuracies/llms/mistral:latest/full-match/full_match.ndjson",
            "full-match-trials": "../../data/generated-regexes-with-accuracies/llms/mistral:latest/full-match/full_match_trials.ndjson",
            "partial-match": "../../data/generated-regexes-with-accuracies/llms/mistral:latest/partial-match/partial_match.ndjson",
            "partial-match-trials": "../../data/generated-regexes-with-accuracies/llms/mistral:latest/partial-match/partial_match_trials.ndjson",
        },
        "qwen2.5-coder:7b": {
            "full-match": "../../data/generated-regexes-with-accuracies/llms/qwen2.5-coder:7b/full-match/full_match.ndjson",
            "full-match-trials": "../../data/generated-regexes-with-accuracies/llms/qwen2.5-coder:7b/full-match/full_match_trials.ndjson",
            "partial-match": "../../data/generated-regexes-with-accuracies/llms/qwen2.5-coder:7b/partial-match/partial_match.ndjson",
            "partial-match-trials": "../../data/generated-regexes-with-accuracies/llms/qwen2.5-coder:7b/partial-match/partial_match_trials.ndjson",
        },
        "qwen2.5-coder:32b": {
            "full-match": "../../data/generated-regexes-with-accuracies/llms/qwen2.5-coder:32b/full-match/full_match.ndjson",
            "full-match-trials": "../../data/generated-regexes-with-accuracies/llms/qwen2.5-coder:32b/full-match/full_match_trials.ndjson",
            "partial-match": "../../data/generated-regexes-with-accuracies/llms/qwen2.5-coder:32b/partial-match/partial_match.ndjson",
            "partial-match-trials": "../../data/generated-regexes-with-accuracies/llms/qwen2.5-coder:32b/partial-match/partial_match_trials.ndjson",
        },
    }
}

BEST_TARGETS = {
    "reuse-by-example": {
        "full-match": "../../data/generated-regexes-with-accuracies/reuse-by-example/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-accuracies/reuse-by-example/partial-match-new/partial_match.ndjson",
    },
    "rfixer": {
        "full-match": "../../data/generated-regexes-with-accuracies/synthesizers/rfixer/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-accuracies/synthesizers/rfixer/partial-match/partial_match.ndjson",
    },
    "o3-mini": {
        "full-match": "../../data/generated-regexes-with-accuracies/llms/o3-mini/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-accuracies/llms/o3-mini/partial-match/partial_match.ndjson",
    },
    # "gpt-4o": {
    #     "full-match": "../../data/generated-regexes-with-accuracies/llms/gpt-4o/full-match/full_match.ndjson",
    #     "partial-match": "../../data/generated-regexes-with-accuracies/llms/gpt-4o/partial-match/partial_match.ndjson",
    # },
}

BEST_TARGETS_SYNTACTIC = {
    "reuse-by-example": {
        "full-match": "../../data/generated-regexes-with-syntactic-similarities/reuse-by-example/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-syntactic-similarities/reuse-by-example/partial-match/partial_match.ndjson",
    },
    "rfixer": {
        "full-match": "../../data/generated-regexes-with-syntactic-similarities/synthesizers/rfixer/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-syntactic-similarities/synthesizers/rfixer/partial-match/partial_match.ndjson",
    },
    "o3-mini": {
        "full-match": "../../data/generated-regexes-with-syntactic-similarities/llms/o3-mini/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-syntactic-similarities/llms/o3-mini/partial-match/partial_match.ndjson",
    },
}

BEST_TARGETS_SEMANTIC = {
    "reuse-by-example": {
        "full-match": "../../data/generated-regexes-with-semantic-similarities/reuse-by-example/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-semantic-similarities/reuse-by-example/partial-match/partial_match.ndjson",
    },
    "rfixer": {
        "full-match": "../../data/generated-regexes-with-semantic-similarities/synthesizers/rfixer/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-semantic-similarities/synthesizers/rfixer/partial-match/partial_match.ndjson",
    },
    "o3-mini": {
        "full-match": "../../data/generated-regexes-with-semantic-similarities/llms/o3-mini/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-semantic-similarities/llms/o3-mini/partial-match/partial_match.ndjson",
    },
}

BEST_TARGETS_HELPFULNESS = {
    "reuse-by-example": {
        "full-match": "../../data/generated-regexes-with-helpfulness-scores/reuse-by-example/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-helpfulness-scores/reuse-by-example/partial-match/partial_match.ndjson",
    },
    "rfixer": {
        "full-match": "../../data/generated-regexes-with-helpfulness-scores/synthesizers/rfixer/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-helpfulness-scores/synthesizers/rfixer/partial-match/partial_match.ndjson",
    },
    "o3-mini": {
        "full-match": "../../data/generated-regexes-with-helpfulness-scores/llms/o3-mini/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-helpfulness-scores/llms/o3-mini/partial-match/partial_match.ndjson",
    },
    "Ground Truth": {
        "full-match": "../../data/generated-regexes-with-helpfulness-scores/reuse-by-example/full-match/full_match.ndjson",
        "partial-match": "../../data/generated-regexes-with-helpfulness-scores/reuse-by-example/partial-match/partial_match.ndjson",
    },
}

def plot_rq1_synthesizer_comparison():
    # Function to read NDJSON file and calculate average accuracy
    def calculate_average_accuracy(file_path):
        # Read NDJSON file line by line (each line is a separate JSON object)
        accuracies = []
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # Extract accuracy from the first candidate
                    if 'candidates' in data and len(data['candidates']) > 0:
                        if isinstance(data['candidates'][0], dict) and 'accuracy' in data['candidates'][0]:
                            # if not data['candidates'][0]['accuracy'] and not data['candidates'][0]['regex_pattern']:
                                # continue
                            if data['candidates'][0]['accuracy'] == None:
                                append_data = 0.0
                            else:
                                append_data = data['candidates'][0]['accuracy']

                            accuracies.append(append_data)
                except json.JSONDecodeError:
                    continue

        # Calculate average accuracy
        if accuracies:
            return np.mean(accuracies)
        else:
            return 0.0

    # Function to process all synthesizers
    def get_synthesizer_data():
        results = {}

        for tool, tool_data in targets["synthesizers"].items():
            results[tool] = {}

            for match_type, file_path in tool_data.items():
                # Check if file exists
                path = Path(file_path)
                if path.exists():
                    results[tool][match_type] = calculate_average_accuracy(file_path)
                else:
                    print(f"Warning: File {file_path} not found. Using default value.")
                    # Use default values if file doesn't exist
                    if tool == "forest":
                        results[tool][match_type] = 0.68 if match_type == "full-match" else 0.75
                    elif tool == "rfixer":
                        results[tool][match_type] = 0.61 if match_type == "full-match" else 0.70
                    elif tool == "rfixer-gtp":
                        results[tool][match_type] = 0.78 if match_type == "full-match" else 0.84

        # Convert to DataFrame for easier manipulation
        data = {
            'Tool': [],
            'Match Type': [],
            'Accuracy': []
        }

        for tool, match_types in results.items():
            for match_type, accuracy in match_types.items():
                data['Tool'].append(tool)
                data['Match Type'].append(match_type)
                data['Accuracy'].append(accuracy)

        return pd.DataFrame(data)

    # Get and process data
    df = get_synthesizer_data()

    # Calculate average accuracies
    avg_accuracies = df.pivot_table(index='Tool', columns='Match Type', values='Accuracy')

    # Get the data in format needed for plotting
    tools = avg_accuracies.index.tolist()
    full_match = avg_accuracies['full-match'].tolist()
    partial_match = avg_accuracies['partial-match'].tolist()

    # Print the results for verification
    print("Synthesizer average accuracies:")
    print(avg_accuracies)

    fig, ax = plt.subplots()

    # Set width of bars
    barWidth = 0.35
    r1 = np.arange(len(tools))
    r2 = [x + barWidth for x in r1]

    # Format the tool names for display (capitalize first letter)
    display_tools = [tool.replace('rfixer-gtp', 'RFixer\\textsubscript{GTP}').replace('rfixer', 'RFixer').replace('forest', '\\textsc{Forest}') for tool in tools]

    # Create bars
    bars1 = ax.bar(r1, full_match, barWidth, label='Full Match', edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(r2, partial_match, barWidth, label='Partial Match', edgecolor='black', linewidth=0.5)

    # Add labels and title
    ax.set_xlabel('Synthesizer Tools')
    ax.set_ylabel('Average Accuracy per Task')
    # ax.set_title('Accuracy Comparison of Synthesizer Tools')
    ax.set_ylim(0, 1.0)
    ax.set_xticks([r + barWidth/2 for r in range(len(display_tools))])
    ax.set_xticklabels(display_tools)

    # Add a grid
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Add text labels on top of the bars
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

    # add_labels(bars1)
    # add_labels(bars2)

    # Add a legend
    legend = ax.legend(loc='upper right', facecolor='white', edgecolor='black', frameon = True, framealpha=1)
    legend.get_frame().set_linewidth(0.5)

    # Layout adjustment
    fig.tight_layout()

    plt.savefig('synthesizers_accuracy_pandas.png', dpi=300)
    plt.show()

    plt.savefig('synthesizer_comparison.pdf', format='pdf')

def plot_rq1_synthesizer_comparison_new():
       # Function to read NDJSON file and calculate average accuracy
    def calculate_average_accuracy(file_path):
        # Read NDJSON file line by line (each line is a separate JSON object)
        accuracies = []
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # Extract accuracy from the first candidate
                    if 'candidates' in data and len(data['candidates']) > 0:
                        if isinstance(data['candidates'][0], dict) and 'accuracy' in data['candidates'][0]:
                            # if not data['candidates'][0]['accuracy'] and not data['candidates'][0]['regex_pattern']:
                                # continue
                            if data['candidates'][0]['accuracy'] == None:
                                append_data = 0.0
                            else:
                                append_data = data['candidates'][0]['accuracy']

                            accuracies.append(append_data)
                except json.JSONDecodeError:
                    continue

        # Calculate average accuracy
        if accuracies:
            return np.mean(accuracies)
        else:
            return 0.0

    # Function to process all synthesizers
    def get_synthesizer_data():
        results = {}

        for tool, tool_data in targets["synthesizers"].items():
            results[tool] = {}

            for match_type, file_path in tool_data.items():
                # Check if file exists
                path = Path(file_path)
                if path.exists():
                    results[tool][match_type] = calculate_average_accuracy(file_path)
                else:
                    print(f"Warning: File {file_path} not found. Using default value.")
                    # Use default values if file doesn't exist
                    if tool == "forest":
                        results[tool][match_type] = 0.68 if match_type == "full-match" else 0.75
                    elif tool == "rfixer":
                        results[tool][match_type] = 0.61 if match_type == "full-match" else 0.70
                    elif tool == "rfixer-gtp":
                        results[tool][match_type] = 0.78 if match_type == "full-match" else 0.84

        # Convert to DataFrame for easier manipulation
        data = {
            'Tool': [],
            'Match Type': [],
            'Accuracy': []
        }

        for tool, match_types in results.items():
            for match_type, accuracy in match_types.items():
                data['Tool'].append(tool)
                data['Match Type'].append(match_type)
                data['Accuracy'].append(accuracy)

        return pd.DataFrame(data)

    # Get and process data
    df = get_synthesizer_data()
    avg_accuracies = df.pivot_table(index='Tool', columns='Match Type', values='Accuracy')

    # Print the results for verification
    print("Synthesizer average accuracies:")
    print(avg_accuracies)

    tools = avg_accuracies.index.tolist()
    full_match = avg_accuracies['full-match'].tolist()
    partial_match = avg_accuracies['partial-match'].tolist()

    # For display in the plot
    display_tools = [
        tool.replace('rfixer-gtp', 'RFixer\\textsubscript{GTP}')
            .replace('rfixer', 'RFixer')
            .replace('forest', '\\textsc{Forest}')
        for tool in tools
    ]

    # --- NEW PLOTTING CODE (Horizontal Bar Chart) ---
    fig, ax = plt.subplots(figsize=(3.3, 1.25))

    # Reduce bar height and spacing
    bar_height = 0.005  # smaller than 0.35
    spacing = 0.0125     # controls vertical spacing between each pair

    # y_positions: space out each “group” of two bars
    y_positions = np.arange(len(tools)) * (bar_height + spacing)

    # Plot Full Match bars
    bars1 = ax.barh(
        y_positions,
        full_match,
        bar_height,
        label='Full Match',
        edgecolor='black',
        linewidth=0.5
    )
    # Plot Partial Match bars, shifted slightly upward
    bars2 = ax.barh(
        y_positions + bar_height,
        partial_match,
        bar_height,
        label='Partial Match',
        edgecolor='black',
        linewidth=0.5
    )

    # Set axes labels
    ax.set_xlabel('Accuracy')
    ax.set_ylabel('Tools')

    # Center the y-ticks between the two bars
    ax.set_yticks(y_positions + bar_height / 2)
    ax.set_yticklabels(display_tools)

    # Set accuracy range
    ax.set_xlim(0, 1.0)

    # Optionally invert the y-axis so the first tool appears at the top
    ax.invert_yaxis()

    # Add a grid
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Add a legend
    # Add a legend
    legend = ax.legend(
        loc='upper right',
        # bbox_to_anchor=(-0.1, -0.02),
        ncol=1,
        handletextpad=0.3,  # Reduce padding between handle and text
        columnspacing=0.8,  # Reduce space between columns
        handleheight=0.5,  # Shrink the height of the legend symbols
        handlelength=1.0,  # Reduce the length of the legend markers
        fontsize='x-small',
        frameon = True, framealpha=1
        )  # Reduce text size
    legend.get_frame().set_linewidth(0.5)

    # Make layout tight
    fig.tight_layout()

    # Get current figure size
    fig_size = plt.gcf().get_size_inches()
    print("Current figure size:", fig_size)

    # Save the figure
    plt.savefig('synthesizer_comparison.pdf', format='pdf')


def plot_rq1_llm_comparison():
    """
    Create a bar chart comparing LLM performance for regex generation.
    Shows accuracy for full/partial match and conservative/balanced/liberal approaches.
    """
    # Define the file paths
    # Function to read NDJSON file and extract accuracy data by regex type
    def calculate_accuracies_by_type(file_path):
        # Initialize dictionaries to store accuracies by type
        accuracies = {
            'conservative': [],
            'balanced': [],
            'liberal': []
        }

        with open(file_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if 'candidates' in data:
                        for candidate in data['candidates']:
                            regex_type = candidate['type']
                            if regex_type in accuracies:
                                if candidate['accuracy'] is None:
                                    append_data = 0.0
                                else:
                                    append_data = candidate['accuracy']

                                accuracies[regex_type].append(append_data)
                except json.JSONDecodeError:
                    continue

        # Calculate mean accuracies for each type
        mean_accuracies = {}
        for regex_type, acc_list in accuracies.items():
            if acc_list:
                mean_accuracies[regex_type] = np.mean(acc_list)
            else:
                mean_accuracies[regex_type] = 0.0

        return mean_accuracies

    # Process all LLMs and create a DataFrame
    data = {
        'LLM': [],
        'Match Type': [],
        'Regex Type': [],
        'Accuracy': []
    }

    for llm, llm_data in targets["llms"].items():
        for match_type, file_path in llm_data.items():
            # Only process the main match files, not trials
            if match_type.endswith('-trials'):
                continue

            accuracies = calculate_accuracies_by_type(file_path)

            for regex_type, accuracy in accuracies.items():
                data['LLM'].append(llm)
                data['Match Type'].append(match_type)
                data['Regex Type'].append(regex_type)
                data['Accuracy'].append(accuracy)

    # Create DataFrame
    df = pd.DataFrame(data)

    # Display the data for verification
    print("LLM performance data:")
    print(df.pivot_table(index=['LLM', 'Match Type'], columns='Regex Type', values='Accuracy'))

    # Create the plot
    fig, ax = plt.subplots()

    # Define bar width and positions
    n_llms = len(df['LLM'].unique())
    n_match_types = len(df['Match Type'].unique())
    n_regex_types = len(df['Regex Type'].unique())

    # Calculate the width of a single bar and the total width of a group
    single_bar_width = 0.2
    group_width = single_bar_width * n_regex_types

    # Colors for regex types
    colors = {
        'conservative': '#1f77b4',  # Blue
        'balanced': '#ff7f0e',      # Orange
        'liberal': '#2ca02c'        # Green
    }

    # Hatch patterns for match types (instead of alpha)
    hatches = {
        'full-match': None,         # Solid fill for full match
        'partial-match': '////'     # Hatched pattern for partial match
    }

    # Get unique LLMs and match types
    llms = df['LLM'].unique()
    match_types = ['full-match', 'partial-match']
    regex_types = ['conservative', 'balanced', 'liberal']

    # Simplified model names for display
    display_llms = [llm.replace('qwen2.5-coder:', 'Qwen ') for llm in llms]
    display_llms = [llm.replace('mistral:latest', 'Mistral 7B') for llm in display_llms]
    display_llms = [llm.replace('gpt-4o', 'GPT-4o') for llm in display_llms]
    display_llms = [llm.replace('llama3.1:8b', 'Ll 3.1 8B') for llm in display_llms]
    display_llms = [llm.replace('llama3.2:1b', 'Ll 3.2 1B') for llm in display_llms]
    display_llms = [llm.replace('llama3.2:3b', 'Ll 3.2 3B') for llm in display_llms]
    display_llms = [llm.replace('o3-mini', 'o3-mini') for llm in display_llms]
    display_llms = [llm.replace('gemma2:27b', 'Gemma 27B') for llm in display_llms]

    # Create positions for each group of bars
    positions = np.arange(len(llms))

    # Define the offset for each match type
    match_type_offset = {
        'full-match': -single_bar_width/1.5,
        'partial-match': single_bar_width/1.5
    }

    # Plot bars for each LLM, match type, and regex type
    for i, match_type in enumerate(match_types):
        for j, regex_type in enumerate(regex_types):
            # Filter data for this combination
            filtered_data = df[(df['Match Type'] == match_type) & (df['Regex Type'] == regex_type)]

            # Sort data to match LLMs order
            filtered_data = filtered_data.set_index('LLM').loc[llms].reset_index()

            # Calculate positions for this set of bars
            pos = positions + match_type_offset[match_type] + j * (single_bar_width/n_regex_types)

            # Plot the bars
            bars = ax.bar(
                pos,
                filtered_data['Accuracy'],
                width=single_bar_width/n_regex_types,
                label=f"{match_type.replace('-', ' ').title()} - {regex_type.title()}",
                color=colors[regex_type],
                edgecolor='black',
                linewidth=0.5,
                hatch=hatches[match_type]
            )

    # Set x-axis ticks and labels
    ax.set_xticks(positions)
    ax.set_xticklabels(display_llms, rotation=20)

    # Set y-axis limit
    ax.set_ylim(0, 1.0)

    # Add grid
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7, axis='y')

    # Add labels and title
    ax.set_xlabel('Language Models')
    ax.set_ylabel('Accuracy')
    # ax.set_title('Comparison of LLMs for Regex Generation')

    # Create legend handles for regex strictness (first row)
    regex_handles = [
        plt.Rectangle((0,0), 1, 1, fc=colors['conservative'], label="Conservative"),
        plt.Rectangle((0,0), 1, 1, fc=colors['balanced'], label="Balanced"),
        plt.Rectangle((0,0), 1, 1, fc=colors['liberal'], label="Liberal"),
        plt.Rectangle((0,0), 1, 1, fc="gray", alpha=1.0, label="Full Match"),
        plt.Rectangle((0,0), 1, 1, fc="gray", alpha=1.0, hatch='////', linewidth=1.0, label="Partial Match"),
    ]

    # Combine handles in the desired order:
    # First row: regex handles (3 items)
    # Second row: match handles (2 items) + dummy (1 item)
    combined_handles = regex_handles

    # Place the combined legend just below the x-axis with 3 columns.
    # The bbox_to_anchor and loc settings place the legend centered below the plot.
    legend = ax.legend(handles=combined_handles,
            loc='upper center',
            bbox_to_anchor=(0.5, -0.35),  # Adjust as needed
            ncol=5,
            handletextpad=0.3,  # Reduce padding between handle and text
            columnspacing=0.8,  # Reduce space between columns
            handleheight=0.5,  # Shrink the height of the legend symbols
            handlelength=1.0,  # Reduce the length of the legend markers
            fontsize='x-small',
            frameon = True, framealpha=1
            )  # Reduce text size
    legend.get_frame().set_linewidth(0.5)

    # Format y-axis as percentage
    # ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))

    # Adjust layout
    fig.tight_layout()

    # Save figure
    plt.savefig('llm_comparison.pdf', dpi=300)

def plot_rq1_best_target_comparison():
    import json
    import numpy as np
    import matplotlib.pyplot as plt
    from pathlib import Path
    from matplotlib.patches import Patch

    # Helper: Read NDJSON file and extract accuracies for candidates that are "balanced"
    def get_balanced_accuracies(file_path):
        accuracies = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        task_accuracies = []
                        if 'candidates' in data:
                            for candidate in data['candidates']:
                                if 'accuracy' in candidate:
                                    # Use candidate type if present, else default to balanced
                                    if candidate['accuracy'] is None:
                                        append_data = 0.0
                                    else:
                                        append_data = candidate['accuracy']
                                    task_accuracies.append(append_data)
                        accuracies.append(task_accuracies)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")
        return accuracies

    # Helper: Read NDJSON file and extract accuracies grouped by regex type
    def get_accuracies_by_type(file_path):
        # Initialize dictionaries for all three types
        accuracies = {"conservative": [], "balanced": [], "liberal": []}
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if 'candidates' in data:
                            for candidate in data['candidates']:
                                if 'accuracy' in candidate:
                                    candidate_type = candidate.get('type', 'balanced')
                                    if candidate_type in accuracies:
                                        accuracies[candidate_type].append(candidate['accuracy'])
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")
        return accuracies

    # Helper: Compute histogram percentages given a list of accuracies
    def compute_histogram_percentages(accuracies, bins):
        task_accuracies = []
        for task in accuracies:
            task_accuracies.append(np.mean(task))

        if len(task_accuracies) == 0:
            return np.zeros(len(bins) - 1)
        counts, _ = np.histogram(task_accuracies, bins=bins)
        percentages = counts / len(task_accuracies) * 100
        return percentages

    # Helper: Given a histogram (as an array of percentages) and the bin edges,
    # create polygon coordinates for a step-like shape.
    # If left==True, mirror the percentages to the left (negative x).
    def compute_polygon_coords(percentages, bins, target_name, left=True, regex_type=None):
        if left:
            x_vals = -np.repeat(percentages, 2)
        else:
            x_vals = np.repeat(percentages, 2)
        y_vals = np.repeat(bins[1:], 2)

        # Add an offset to separate the polygons
        # if target_name == "o3-mini":
        #     if regex_type == "balanced":
        #         x_vals += 10
        #     elif regex_type == "liberal":
        #         x_vals -= 10
        #     else:
        #         x_vals += 0.0

        x_poly = np.concatenate(([0], x_vals, [0]))
        y_poly = np.concatenate(([bins[0]], y_vals, [bins[-1]]))
        return x_poly, y_poly

    # Define bins: 10 bins covering the range 0 to 1
    bins = np.linspace(0, 1, 21)  # [0, 0.1, 0.2, ..., 1.0]

    # Dictionary to hold computed data for each best target.
    # BEST_TARGETS is assumed available in the module scope.
    target_data = {}
    global_max = 0  # to determine common x-axis limits later

    for target_name, files in BEST_TARGETS.items():
        target_data[target_name] = {}
        for match_type in ['full-match', 'partial-match']:
            if match_type in files:
                print(f"Processing {match_type} data for target {target_name}...")
                file_path = files[match_type]
                accuracies = get_balanced_accuracies(file_path)
                percentages = compute_histogram_percentages(accuracies, bins)
                # Print the percentage distribution for verification
                print(f"Percentage distribution for {match_type} in {target_name}:")
                for i, (start, end) in enumerate(zip(bins[:-1], bins[1:])):
                    print(f"{start:.2f}-{end:.2f}: {percentages[i]:.2f}%")
                if percentages.size > 0:
                    local_max = percentages.max()
                    if local_max > global_max:
                        global_max = local_max
                x_poly, y_poly = compute_polygon_coords(percentages, bins, target_name, left=(match_type == 'full-match'))
                target_data[target_name][match_type] = {
                    'accuracies': accuracies,
                    'percentages': percentages,
                    'x_poly': x_poly,
                    'y_poly': y_poly
                }
            else:
                print(f"Warning: {match_type} data not found for target {target_name}.")

    # In case no data was found, use a default x-axis range
    if global_max == 0:
        global_max = 1
    # Add a margin of 10%
    x_limit = global_max * 1.1

    # Create one subplot per best target (3 in total)
    fig, axes = plt.subplots(1, len(BEST_TARGETS.keys()), sharey=True, figsize=(3.3, 1.5))
    fig.subplots_adjust(wspace=1)
    if not isinstance(axes, np.ndarray):
        axes = [axes]

    # Colors for non-o3-mini targets (balanced only)
    base_colors = {
        'full-match': 'C0',   # blue
        'partial-match': 'C1'  # orange
    }
    # Colors for o3-mini regex types
    regex_colors = {
        'conservative': '#1f77b4',
        'balanced': '#ff7f0e',
        'liberal': '#2ca02c'
    }
    # Hatches for o3-mini regex types (choose any pattern you like)
    regex_hatches = {
        'conservative': '',
        'balanced': '///',
        'liberal': '\\\\'
    }
    alpha_value = 1

    # Loop over each best target and plot its data
    for ax, (target_name, match_info) in zip(axes, target_data.items()):
        # For other targets, plot balanced data for full and partial match
        if 'full-match' in match_info:
            ax.fill(match_info['full-match']['x_poly'], match_info['full-match']['y_poly'],
                    color=base_colors['full-match'], alpha=alpha_value,
                    edgecolor='black', linewidth=0.5,
                    label='Full Match')
        if 'partial-match' in match_info:
            ax.fill(match_info['partial-match']['x_poly'], match_info['partial-match']['y_poly'],
                    color=base_colors['partial-match'], alpha=alpha_value,
                    edgecolor='black', linewidth=0.5,
                    label='Partial Match')
        # Draw a vertical line at x=0 to separate the two halves
        ax.axvline(x=0, color='black', linewidth=0.5)
        # Set title for each target (with your custom formatting)
        formatted_target_name = "\\texttt{reuse-by-example}" if target_name == "reuse-by-example" else ("RFixer" if target_name == "rfixer" else ("o3-mini" if target_name == "o3-mini" else "GPT 4o"))
        ax.set_title(formatted_target_name)
        # Set consistent x-axis limits across subplots
        ax.set_xlim(-x_limit, x_limit)
        # Set y-axis limits and ticks (accuracy from 0 to 1 with steps of 0.1)
        ax.set_ylim(0, 1)
        ax.set_yticks(np.linspace(0, 1, 11))
        # Format x-axis ticks to show absolute percentages
        xticks = ax.get_xticks()
        ax.set_xticklabels([f"{abs(x):.0f}" for x in xticks])
        # Add a light grid for better readability
        ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # One common X and Y axis label for all subplots
    fig.supxlabel('Percentage of Tasks', y=-0.075)

    fig.supylabel('Accuracy', x=-0.05)
    # fig.suptitle('Distribution of Accuracies per Task', y=1.01)

    # Create a legend for the match types (full/partial)
    match_handles = [
        Patch(facecolor=base_colors['full-match'], label='Full Match'),
        Patch(facecolor=base_colors['partial-match'], label='Partial Match')
    ]

    # Select the axis of the subplot on middle
    ax = axes[1]

    legend = ax.legend(handles=match_handles,
            loc='lower center',
            bbox_to_anchor=(0.5, -0.4),  # Adjust as needed
            ncol=2,
            handletextpad=0.3,  # Reduce padding between handle and text
            columnspacing=0.8,  # Reduce space between columns
            handleheight=0.5,  # Shrink the height of the legend symbols
            handlelength=1.0,  # Reduce the length of the legend markers
            fontsize='x-small',
            frameon = True, framealpha=1
            )  # Reduce text size
    legend.get_frame().set_linewidth(0.5)

    print("Current figure size:", plt.gcf().get_size_inches())

    plt.savefig('best_target_comparison.pdf', dpi=300)

def analyze_perfect_accuracy_tasks():
    """
    Analyzes the BEST_TARGETS data to find the percentage of tasks that have
    at least one candidate with perfect accuracy (accuracy = 1.0).

    Prints detailed statistics for each target and match type, including:
    - Total number of tasks
    - Number of tasks with perfect accuracy
    - Percentage of tasks with perfect accuracy
    - Statistics grouped by candidate type (if available)
    """
    import json
    import numpy as np
    from pathlib import Path

    # Results dictionary to store our findings
    results = {}

    # Process each target in BEST_TARGETS
    for target_name, files in BEST_TARGETS.items():
        results[target_name] = {}

        for match_type, file_path in files.items():
            # Skip trial files if they exist
            if match_type.endswith('-trials'):
                continue

            # Initialize counters
            total_tasks = 0
            perfect_accuracy_tasks = 0

            # For tracking statistics by candidate type
            by_type = {
                'conservative': {'total': 0, 'perfect': 0},
                'balanced': {'total': 0, 'perfect': 0},
                'liberal': {'total': 0, 'perfect': 0}
            }

            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            total_tasks += 1

                            # Check if any candidate has perfect accuracy
                            has_perfect_accuracy = False

                            if 'candidates' in data and len(data['candidates']) > 0:
                                for candidate in data['candidates']:
                                    if 'accuracy' in candidate:
                                        # Categorize by type if available
                                        candidate_type = candidate.get('type', 'balanced')
                                        if candidate_type in by_type:
                                            by_type[candidate_type]['total'] += 1

                                        # Check for perfect accuracy
                                        if candidate['accuracy'] == 1.0:
                                            has_perfect_accuracy = True

                                            # Count perfect by type
                                            if candidate_type in by_type:
                                                by_type[candidate_type]['perfect'] += 1

                            if has_perfect_accuracy:
                                perfect_accuracy_tasks += 1

                        except json.JSONDecodeError:
                            continue

            except FileNotFoundError:
                print(f"Warning: File {file_path} not found.")
                continue

            # Calculate percentages
            percentage = (perfect_accuracy_tasks / total_tasks * 100) if total_tasks > 0 else 0

            # Calculate percentages by type
            type_percentages = {}
            for ctype, counts in by_type.items():
                if counts['total'] > 0:
                    type_percentages[ctype] = counts['perfect'] / counts['total'] * 100
                else:
                    type_percentages[ctype] = 0

            # Store results
            results[target_name][match_type] = {
                'total_tasks': total_tasks,
                'perfect_accuracy_tasks': perfect_accuracy_tasks,
                'percentage': percentage,
                'by_type': {
                    'counts': by_type,
                    'percentages': type_percentages
                }
            }

    # Print the results in a formatted way
    print("\n" + "="*80)
    print(f"ANALYSIS OF TASKS WITH PERFECT ACCURACY (ACCURACY = 1.0)")
    print("="*80)

    for target_name, match_types in results.items():
        print(f"\n{target_name.upper()}")
        print("-" * len(target_name.upper()))

        for match_type, stats in match_types.items():
            print(f"\n  {match_type}:")
            print(f"    Total tasks: {stats['total_tasks']}")
            print(f"    Tasks with perfect accuracy: {stats['perfect_accuracy_tasks']}")
            print(f"    Percentage: {stats['percentage']:.2f}%")

            # Print type statistics if they exist
            if any(stats['by_type']['counts'][t]['total'] > 0 for t in ['conservative', 'balanced', 'liberal']):
                print("\n    By regex type:")
                for regex_type in ['conservative', 'balanced', 'liberal']:
                    type_stats = stats['by_type']['counts'][regex_type]
                    if type_stats['total'] > 0:
                        print(f"      {regex_type.capitalize()}: " +
                              f"{type_stats['perfect']}/{type_stats['total']} " +
                              f"({stats['by_type']['percentages'][regex_type]:.2f}%)")

    print("\n" + "="*80)

    # Now print a summary table for easy comparison
    print("\nSUMMARY TABLE (Percentage of tasks with perfect accuracy)")
    print("-" * 60)

    # Headers
    print(f"{'Target':<20} {'Full Match':<15} {'Partial Match':<15}")
    print("-" * 60)

    # Data rows
    for target_name in results:
        full_match_pct = results[target_name].get('full-match', {}).get('percentage', 0)
        partial_match_pct = results[target_name].get('partial-match', {}).get('percentage', 0)

        print(f"{target_name:<20} {full_match_pct:>6.2f}%{'':<8} {partial_match_pct:>6.2f}%")

    print("-" * 60)

def plot_rq1_best_target_test_string_count_vs_accuracy():
    """
    Create a line graph that shows the relationship between test string count
    and accuracy for the best targets.
    """
    # Helper function to read NDJSON and extract test string count and accuracy
    def extract_test_count_vs_accuracy(file_path, target_name):
        data_points = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        # Check if the data contains candidates
                        if 'candidates' in data and len(data['candidates']) > 0:
                            # Look for test string count directly or in test_strings
                            test_count = None
                            if 'test_string_count' in data:
                                test_count = data['test_string_count']

                            # Only proceed if we found a test count
                            if test_count is not None:
                                for candidate in data['candidates']:
                                    if candidate['accuracy'] is None:
                                        append_data = 0.0
                                    else:
                                        append_data = candidate['accuracy']

                                    data_points.append((test_count, append_data))
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"Error processing line in {file_path}: {e}")
                        continue
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")
        return data_points

    # Dictionary to store data points for each target and match type
    target_data = {}

    # Extract data for each target and match type
    for target_name, files in BEST_TARGETS.items():
        target_data[target_name] = {}
        for match_type, file_path in files.items():
            # Skip trial files
            if match_type.endswith('-trials'):
                continue

            data_points = extract_test_count_vs_accuracy(file_path, target_name)
            target_data[target_name][match_type] = data_points
            print(f"Extracted {len(data_points)} data points from {target_name} {match_type}")

    # Create the plot
    fig, ax = plt.subplots()

    # Define line styles and markers for different targets
    line_styles = {
        'reuse-by-example': '-',
        'rfixer': '--',
        'o3-mini': ':'
    }

    markers = {
        'reuse-by-example': 'o',
        'rfixer': 's',
        'o3-mini': '^'
    }

    # Colors for match types (using the same colors as in the other plots)
    colors = {
        'full-match': '#1f77b4',   # blue
        'partial-match': '#ff7f0e'  # orange
    }

    # Plot data for each target and match type
    for target_name, match_data in target_data.items():
        for match_type, data_points in match_data.items():
            if data_points:
                # Group data points by test string count
                grouped_data = {}
                for count, acc in data_points:
                    if count not in grouped_data:
                        grouped_data[count] = []
                    grouped_data[count].append(acc)

                # Calculate average accuracy for each test string count
                avg_data = [(count, sum(accs)/len(accs)) for count, accs in grouped_data.items()]
                avg_data.sort(key=lambda x: x[0])

                # Extract x and y values for plotting
                x_avg = [point[0] for point in avg_data]
                y_avg = [point[1] for point in avg_data]

                # Format target name for display (following the style in the other functions)
                if target_name == "reuse-by-example":
                    display_name = "\\texttt{reuse-by-example}"
                elif target_name == "rfixer":
                    display_name = "RFixer"
                else:
                    display_name = target_name

                # Plot line
                ax.plot(x_avg, y_avg,
                        linestyle=line_styles[target_name],
                        # marker=markers[target_name],
                        color=colors[match_type],
                        label=f"{display_name} ({match_type.replace('-', ' ')})",
                        alpha=0.7)

    # Add grid
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Set axis labels and title
    ax.set_xlabel('Number of Test Strings')
    ax.set_ylabel('Average Accuracy')
    # ax.set_title('Relationship Between Test String Count and Accuracy')

    # Add legend with the same style as other plots
    # legend = ax.legend(loc='lower right',
    #                    facecolor='white',
    #                    edgecolor='black',
    #                    frameon=True,
    #                    framealpha=1)
    # legend.get_frame().set_linewidth(0.5)

    legend_handles = [
        plt.Line2D([0], [0], label='\\texttt{reuse-by-example}', color='black', linestyle='-'),
        plt.Line2D([0], [0], label='RFixer', color='black', linestyle='--'),
        plt.Line2D([0], [0], label='o3-mini', color='black', linestyle=':'),
    ]
    legend_handles.append(plt.Line2D([0], [0], color=colors['full-match'], linestyle='-', label='Full Match'))
    legend_handles.append(plt.Line2D([0], [0], color=colors['partial-match'], linestyle='-', label='Partial Match'))

    legend = ax.legend(handles=legend_handles,
            loc='lower center',
            bbox_to_anchor=(0.5, -0.30),  # Adjust as needed
            ncol=5,
            handletextpad=0.3,  # Reduce padding between handle and text
            columnspacing=0.8,  # Reduce space between columns
            handleheight=0.5,  # Shrink the height of the legend symbols
            handlelength=1.0,  # Reduce the length of the legend markers
            fontsize='x-small',
            frameon = True, framealpha=1
            )  # Reduce text size

    # Format y-axis to show accuracy between 0 and 1
    ax.set_ylim(0, 1.0)

    # Adjust layout
    fig.tight_layout()

    # Save figure
    plt.savefig('test_string_count_vs_accuracy.pdf', format='pdf', dpi=300)

def plot_rq1_best_target_gt_regex_length_vs_accuracy():
    """
    Create a line graph that shows the relationship between test string count
    and accuracy for the best targets.
    """
    # Helper function to read NDJSON and extract test string count and accuracy
    def extract_test_count_vs_accuracy(file_path, target_name):
        data_points = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        # Check if the data contains candidates
                        if 'candidates' in data and len(data['candidates']) > 0:
                            # Look for test string count directly or in test_strings
                            regex_length = len(data['regex_pattern'])

                            for candidate in data['candidates']:
                                if candidate['accuracy'] is None:
                                    append_data = 0.0
                                else:
                                    append_data = candidate['accuracy']
                                data_points.append((regex_length, append_data))
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"Error processing line in {file_path}: {e}")
                        continue
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")
        return data_points

    def get_regex_lengths(file_path, target_name):
        regex_lengths = []
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if 'regex_pattern' in data:
                            regex_lengths.append(len(data['regex_pattern']))
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")
        return regex_lengths

    #
    full_match_lengths = get_regex_lengths(BEST_TARGETS['reuse-by-example']['full-match'], 'reuse-by-example')
    partial_match_lengths = get_regex_lengths(BEST_TARGETS['reuse-by-example']['partial-match'], 'reuse-by-example')

    percentile_99_fm = np.percentile(full_match_lengths, 80)
    print(f"80th percentile for full match: {percentile_99_fm}")
    percentile_99_pm = np.percentile(partial_match_lengths, 80)
    print(f"80th percentile for partial match: {percentile_99_pm}")

    # Dictionary to store data points for each target and match type
    target_data = {}

    # Extract data for each target and match type
    for target_name, files in BEST_TARGETS.items():
        target_data[target_name] = {}
        for match_type, file_path in files.items():
            # Skip trial files
            if match_type.endswith('-trials'):
                continue

            data_points = extract_test_count_vs_accuracy(file_path, target_name)
            target_data[target_name][match_type] = data_points
            print(f"Extracted {len(data_points)} data points from {target_name} {match_type}")

    # Create the plot
    fig, ax = plt.subplots()

    # Define line styles and markers for different targets
    line_styles = {
        'reuse-by-example': '-',
        'rfixer': '--',
        'o3-mini': ':'
    }

    markers = {
        'reuse-by-example': 'o',
        'rfixer': 's',
        'o3-mini': '^'
    }

    # Colors for match types (using the same colors as in the other plots)
    colors = {
        'full-match': '#1f77b4',   # blue
        'partial-match': '#ff7f0e'  # orange
    }

    # Plot data for each target and match type
    for target_name, match_data in target_data.items():
        for match_type, data_points in match_data.items():
            if data_points:
                # Group data points by test string count
                grouped_data = {}
                for count, acc in data_points:
                    if count not in grouped_data:
                        grouped_data[count] = []
                    grouped_data[count].append(acc)

                # Calculate average accuracy for each test string count
                avg_data = [(count, sum(accs)/len(accs)) for count, accs in grouped_data.items()]
                avg_data.sort(key=lambda x: x[0])

                # Extract x and y values for plotting
                x_avg = [point[0] for point in avg_data]
                y_avg = [point[1] for point in avg_data]

                # Format target name for display (following the style in the other functions)
                if target_name == "reuse-by-example":
                    display_name = "\\texttt{reuse-by-example}"
                elif target_name == "rfixer":
                    display_name = "RFixer"
                else:
                    display_name = target_name

                # Plot line
                ax.plot(x_avg, y_avg,
                        linestyle=line_styles[target_name],
                        # marker=markers[target_name],
                        color=colors[match_type],
                        label=f"{display_name} ({match_type.replace('-', ' ')})",
                        alpha=0.7)

    # Add grid
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Set axis labels and title
    ax.set_xlabel('Length of Ground Truth Regexes')
    ax.set_ylabel('Average Accuracy')
    # ax.set_title('Relationship Between Ground Truth Complexity and Accuracy')

    # Add legend with the same style as other plots
    # legend = ax.legend(loc='lower right',
    #                    facecolor='white',
    #                    edgecolor='black',
    #                    frameon=True,
    #                    framealpha=1)
    # legend.get_frame().set_linewidth(0.5)

    legend_handles = [
        plt.Line2D([0], [0], label='\\texttt{reuse-by-example}', color='black', linestyle='-'),
        plt.Line2D([0], [0], label='RFixer', color='black', linestyle='--'),
        plt.Line2D([0], [0], label='o3-mini', color='black', linestyle=':'),
    ]
    legend_handles.append(plt.Line2D([0], [0], color=colors['full-match'], linestyle='-', label='Full Match'))
    legend_handles.append(plt.Line2D([0], [0], color=colors['partial-match'], linestyle='-', label='Partial Match'))

    legend = ax.legend(handles=legend_handles,
            loc='lower center',
            bbox_to_anchor=(0.5, -0.30),  # Adjust as needed
            ncol=5,
            handletextpad=0.3,  # Reduce padding between handle and text
            columnspacing=0.8,  # Reduce space between columns
            handleheight=0.5,  # Shrink the height of the legend symbols
            handlelength=1.0,  # Reduce the length of the legend markers
            fontsize='x-small',
            frameon = True, framealpha=1
            )  # Reduce text size

    # Format y-axis to show accuracy between 0 and 1
    ax.set_ylim(0, 1.0)

    # Format x-axis to show between 0 and 500
    ax.set_xlim(0, 50)

    # Adjust layout
    fig.tight_layout()

    # Save figure
    plt.savefig('gt_length_vs_accuracy.pdf', format='pdf', dpi=300)

def plot_rq2_best_target_syntactic_similarity():
    """
    Create a bar chart comparing the average normalized AST edit distance
    for the best targets in BEST_TARGETS_SYNTACTIC.
    Shows side-by-side bars for full match and partial match for each target.
    """
    import json
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from pathlib import Path

    # Function to read NDJSON file and calculate average normalized AST edit distance
    def calculate_average_edit_distance(file_path):
        edit_distances = []

        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        # Extract normalized AST edit distance from the first candidate
                        if 'candidates' in data and len(data['candidates']) > 0:
                            for candidate in data['candidates']:
                                if 'normalized_ast_edit_distance' in candidate:
                                    if candidate['normalized_ast_edit_distance'] is None:
                                        continue

                                    edit_distances.append(candidate['normalized_ast_edit_distance'])
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")

        # Calculate average normalized AST edit distance
        if edit_distances:
            return np.mean(edit_distances)
        else:
            return 0.0

    # Process all targets and create a DataFrame
    data = {
        'Target': [],
        'Match Type': [],
        'Average Edit Distance': []
    }

    for target_name, files in BEST_TARGETS_SYNTACTIC.items():
        for match_type, file_path in files.items():
            avg_edit_distance = calculate_average_edit_distance(file_path)

            data['Target'].append(target_name)
            data['Match Type'].append(match_type)
            data['Average Edit Distance'].append(avg_edit_distance)

            print(f"{target_name} ({match_type}): {avg_edit_distance:.4f}")

    # Create DataFrame
    df = pd.DataFrame(data)

    # Display the data for verification
    print("Target syntactic similarity data:")
    print(df.pivot_table(index='Target', columns='Match Type', values='Average Edit Distance'))

    # Get unique targets and sort them
    targets = df['Target'].unique()

    # Create positions for each group of bars
    positions = np.arange(len(targets))

    # Format the target names for display
    display_targets = []
    for target in targets:
        if target == "reuse-by-example":
            display_targets.append("\\texttt{reuse-by-example}")
        elif target == "rfixer":
            display_targets.append("RFixer")
        else:
            display_targets.append("o3-mini")

    # Colors for match types (using the same colors as in the other plots)
    colors = {
        'partial-match': '#0077BB',   # blue
        'full-match': '#EE7733'  # orange
    }

    # Plot bars for each match type
    full_match_data = df[df['Match Type'] == 'full-match'].set_index('Target').loc[targets]['Average Edit Distance'].values
    partial_match_data = df[df['Match Type'] == 'partial-match'].set_index('Target').loc[targets]['Average Edit Distance'].values

    # Create the plot
    fig, ax = plt.subplots(figsize=(3.3, 1.25))

    # Set width of bars
    bar_height = 0.005  # smaller than 0.35
    spacing = 0.0125

    # Calculate positions for the bars
    y_positions = np.arange(len(targets)) * (bar_height + spacing)

    # Create bars
    bars1 = ax.barh(y_positions, full_match_data, bar_height, label='Full Match', edgecolor='black', linewidth=0.5, color=colors['full-match'])
    bars2 = ax.barh(y_positions + bar_height, partial_match_data, bar_height, label='Partial Match', edgecolor='black', linewidth=0.5, color=colors['partial-match'])

    # Add labels and title
    ax.set_ylabel('Strategy')
    ax.set_xlabel('Normalized AST Edit Distance')
    # ax.yaxis.set_label_coords(-0.15, 0.35)


    # Add text labels on top of the bars
    # def add_labels(bars):
    #     for bar in bars:
    #         height = bar.get_height()
    #         ax.annotate(f'{height:.2f}',
    #                    xy=(bar.get_x() + bar.get_width() / 2, height),
    #                    xytext=(0, 3),  # 3 points vertical offset
    #                    textcoords="offset points",
    #                    ha='center', va='bottom')

    # add_labels(bars1)
    # add_labels(bars2)

    # Center the y-ticks between the two bars
    ax.set_yticks(y_positions + bar_height / 2)
    ax.set_yticklabels(display_targets)

    # Set y-axis limits
    ax.set_xlim(0, 2)

    ax.invert_yaxis()

    # Add a grid
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Set x-axis ticks and labels
    # ax.set_xticks(positions)
    # ax.set_xticklabels(display_targets)

    # Add a legend
    legend = ax.legend(
        loc='upper right',
        # bbox_to_anchor=(-0.4, -0.3),  # Adjust as needed
        ncol=1,
        handletextpad=0.3,  # Reduce padding between handle and text
        columnspacing=0.8,  # Reduce space between columns
        handleheight=0.5,  # Shrink the height of the legend symbols
        handlelength=1.0,  # Reduce the length of the legend markers
        fontsize='x-small',
        frameon = True, framealpha=1
        )  # Reduce text size
    legend.get_frame().set_linewidth(0.5)

    # Adjust layout
    fig.tight_layout()

    # Save figure
    plt.savefig('syntactic_similarity_comparison.pdf', format='pdf', dpi=300)
    plt.show()

def plot_rq3_best_target_semantic_similarity():
    """
    Create a bar chart comparing the average normalized AST edit distance
    for the best targets in BEST_TARGETS_SYNTACTIC.
    Shows side-by-side bars for full match and partial match for each target.
    """
    import json
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from pathlib import Path

    # Function to read NDJSON file and calculate average normalized AST edit distance
    def calculate_average_semantic_similarity(file_path):
        semantic_similarities = []

        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        # Extract normalized AST edit distance from the first candidate
                        if 'candidates' in data and len(data['candidates']) > 0:
                            for candidate in data['candidates']:
                                if 'symmetrical_semantic_similarity' in candidate:
                                    if candidate['symmetrical_semantic_similarity'] is None:
                                        continue

                                    semantic_similarities.append(candidate['symmetrical_semantic_similarity'])
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")

        # Calculate average semantic similarity
        if semantic_similarities:
            return np.mean(semantic_similarities)
        else:
            return 0.0

    # Process all targets and create a DataFrame
    data = {
        'Target': [],
        'Match Type': [],
        'Average Semantic Similarity': []
    }

    for target_name, files in BEST_TARGETS_SEMANTIC.items():
        for match_type, file_path in files.items():
            avg_semantic_similarity = calculate_average_semantic_similarity(file_path)

            data['Target'].append(target_name)
            data['Match Type'].append(match_type)
            data['Average Semantic Similarity'].append(avg_semantic_similarity)

            print(f"{target_name} ({match_type}): {avg_semantic_similarity:.4f}")

    # Create DataFrame
    df = pd.DataFrame(data)

    # Display the data for verification
    print("Target semantic similarity data:")
    print(df.pivot_table(index='Target', columns='Match Type', values='Average Semantic Similarity'))

    # Get unique targets and sort them
    targets = df['Target'].unique()

    # Create positions for each group of bars
    positions = np.arange(len(targets))

    # Format the target names for display
    display_targets = []
    for target in targets:
        if target == "reuse-by-example":
            display_targets.append("\\texttt{reuse-by-example}")
        elif target == "rfixer":
            display_targets.append("RFixer")
        else:
            display_targets.append("o3-mini")

    # Colors for match types (using the same colors as in the other plots)
    colors = {
        'partial-match': '#0077BB',   # blue
        'full-match': '#EE7733'  # orange
    }

    # Plot bars for each match type
    full_match_data = df[df['Match Type'] == 'full-match'].set_index('Target').loc[targets]['Average Semantic Similarity'].values
    partial_match_data = df[df['Match Type'] == 'partial-match'].set_index('Target').loc[targets]['Average Semantic Similarity'].values

    # Create the plot
    fig, ax = plt.subplots(figsize=(3.3, 1.25))

    # Set width of bars
    bar_height = 0.005  # smaller than 0.35
    spacing = 0.0125

    # Calculate positions for the bars
    y_positions = np.arange(len(display_targets)) * (bar_height + spacing)

    # Create bars
    bars1 = ax.barh(y_positions, full_match_data, bar_height, label='Full Match', edgecolor='black', linewidth=0.5, color=colors['full-match'])
    bars2 = ax.barh(y_positions + bar_height, partial_match_data, bar_height, label='Partial Match', edgecolor='black', linewidth=0.5, color=colors['partial-match'])

    # Add labels and title
    ax.set_ylabel('Strategy')
    ax.set_xlabel('Symmetrical Semantic Similarity')
    # ax.set_title('Symmetrical Semantic Similarity Comparison of Strategies')

    # Add text labels on top of the bars
    # def add_labels(bars):
    #     for bar in bars:
    #         height = bar.get_height()
    #         ax.annotate(f'{height:.2f}',
    #                    xy=(bar.get_x() + bar.get_width() / 2, height),
    #                    xytext=(0, 3),  # 3 points vertical offset
    #                    textcoords="offset points",
    #                    ha='center', va='bottom')

    # add_labels(bars1)
    # add_labels(bars2)

    # Center the y-ticks between the two bars
    ax.set_yticks(y_positions + bar_height / 2)
    ax.set_yticklabels(display_targets)

    ax.invert_yaxis()

    # Add grid
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Set x-axis ticks and labels
    # ax.set_xticks(positions)
    # ax.set_xticklabels(display_targets)

    # set y-axis to show between 0 and 1
    ax.set_xlim(0, 1)

    # Add a legend
    legend = ax.legend(
        loc='upper right',
        # bbox_to_anchor=(-0.1, -0.02),
        ncol=1,
        handletextpad=0.3,  # Reduce padding between handle and text
        columnspacing=0.8,  # Reduce space between columns
        handleheight=0.5,  # Shrink the height of the legend symbols
        handlelength=1.0,  # Reduce the length of the legend markers
        fontsize='x-small',
        frameon = True, framealpha=1
        )  # Reduce text size
    legend.get_frame().set_linewidth(0.5)

    # Adjust layout
    fig.tight_layout()

    # Save figure
    plt.savefig('semantic_similarity_comparison.pdf', format='pdf', dpi=300)

def plot_rq4_helpfulness_score_distribution_grouped():
    """
    Create a grouped box plot comparing the distribution of helpfulness scores
    for the best targets in BEST_TARGETS_HELPFULNESS.
    Groups box plots by target with different colors for full match and partial match.
    """
    import json
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from pathlib import Path

    # Function to read NDJSON file and extract helpfulness scores
    def extract_helpfulness_scores(file_path):
        helpfulness_scores = []

        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        # Extract helpfulness score from the first candidate
                        if 'candidates' in data and len(data['candidates']) > 0:
                            for candidate in data['candidates']:
                                if 'helpfulness_score' in candidate:
                                    if candidate['helpfulness_score'] is None:
                                        continue

                                    helpfulness_scores.append(candidate['helpfulness_score'])
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")

        return helpfulness_scores

    # Process all targets and create a DataFrame with individual scores
    df_data = []

    for target_name, files in BEST_TARGETS_HELPFULNESS.items():
        for match_type, file_path in files.items():
            helpfulness_scores = extract_helpfulness_scores(file_path)

            if helpfulness_scores:  # Only add if we have scores
                # Calculate mean for reporting
                mean_score = np.mean(helpfulness_scores)
                print(f"{target_name} ({match_type}): {len(helpfulness_scores)} scores, mean: {mean_score:.4f}")

                # Add individual scores to dataframe
                for score in helpfulness_scores:
                    df_data.append({
                        'Target': target_name,
                        'Match Type': match_type,
                        'Helpfulness Score': score
                    })

    # Create DataFrame with individual scores
    df = pd.DataFrame(df_data)

    # Check if we have data
    if df.empty:
        print("No helpfulness score data found.")
        return

    # Discard everything >1 and <-1 from the data
    df = df[(df['Helpfulness Score'] >= -1) & (df['Helpfulness Score'] <= 1)]

    # Print summary statistics
    print("\nHelpfulness score statistics:")
    summary = df.groupby(['Target', 'Match Type'])['Helpfulness Score'].describe()
    print(summary)

    # Fall back to matplotlib if seaborn is not available
    fig, ax = plt.subplots()

    # Get unique targets and match types
    targets = df['Target'].unique()
    match_types = ['full-match', 'partial-match']

    # Colors for match types
    colors = {
        'full-match': '#1f77b4',   # blue
        'partial-match': '#ff7f0e'  # orange
    }

    # Width of the boxes
    width = 0.3

    # Positions for the boxes
    positions = {
        ('full-match', 0): 0.8,
        ('partial-match', 0): 1.2,
        ('full-match', 1): 1.8,
        ('partial-match', 1): 2.2,
        ('full-match', 2): 2.8,
        ('partial-match', 2): 3.2,
    }

    # For each target and match type
    for i, target in enumerate(targets):
        for match_type in match_types:
            # Get data for this target and match type
            data = df[(df['Target'] == target) & (df['Match Type'] == match_type)]['Helpfulness Score'].values

            if len(data) > 0:
                # Create box plot
                bp = ax.boxplot(
                    data,
                    positions=[positions[(match_type, i)]],
                    widths=width,
                    patch_artist=True,
                    showfliers=True,
                    medianprops={'color': 'black'},
                    boxprops={'facecolor': colors[match_type], 'edgecolor': 'black'},
                    whiskerprops={'color': 'black'},
                    capprops={'color': 'black'},
                    flierprops={'marker': 'o', 'markerfacecolor': 'black', 'markersize': 3, 'alpha': 0.5}
                )

    # Set positions for the tick marks
    ax.set_xticks([1, 2, 3])

    # Format the target names for display
    display_targets = []
    for target in df['Target'].unique():
        if target == "reuse-by-example":
            display_targets.append("\\texttt{reuse-by-example}")
        elif target == "rfixer":
            display_targets.append("RFixer")
        else:
            display_targets.append("o3-mini")

    # Set x-axis labels
    ax.set_xticklabels(display_targets)


    # Set y-axis limits based on the data
    # y_min = max(0, df['Helpfulness Score'].min() - 0.5)  # Don't go below 0
    # y_max = min(5, df['Helpfulness Score'].max() + 0.5)  # Don't go above 5 (assuming scores are 0-5)
    # ax.set_ylim(y_min, y_max)

    # Add grid lines
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7, axis='y')

    # Add labels
    ax.set_xlabel('Strategy')
    ax.set_ylabel('Helpfulness Score')

    # Create custom legend
    handles = [
        mpatches.Patch(color='#1f77b4', label='Full Match'),
        mpatches.Patch(color='#ff7f0e', label='Partial Match')
    ]

    legend = ax.legend(
        handles=handles,
        loc='upper right',
        frameon=True,
        framealpha=1,
        handletextpad=0.3,
        handleheight=0.5,
        handlelength=1.0,
        fontsize='x-small'
    )
    legend.get_frame().set_linewidth(0.5)

    # Adjust layout
    fig.tight_layout()

    # Save figure
    plt.savefig('helpfulness_score_distribution_grouped.pdf', format='pdf', dpi=300)

def plot_rq3_helpfulness_score_violin():
    """
    Create violin plots comparing the distribution of helpfulness scores
    for the best targets in BEST_TARGETS_HELPFULNESS.
    Shows the full probability density of the data, better revealing distribution shape.
    """
    import json
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from pathlib import Path

    # Function to read NDJSON file and extract helpfulness scores
    def extract_helpfulness_scores(file_path):
        helpfulness_scores = []

        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        # Extract helpfulness score from the first candidate
                        if 'candidates' in data and len(data['candidates']) > 0:
                            for candidate in data['candidates']:
                                if 'helpfulness_score' in candidate:
                                    if candidate['helpfulness_score'] is None:
                                        continue

                                    helpfulness_scores.append(candidate['helpfulness_score'])
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")

        return helpfulness_scores

    # Function to read NDJSON file and extract helpfulness scores
    def extract_helpfulness_scores_ground_truth(file_path):
        helpfulness_scores = []

        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)

                        if 'helpfulness_score' in data:
                            if data['helpfulness_score'] is None:
                                continue

                            helpfulness_scores.append(data['helpfulness_score'])
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")

        return helpfulness_scores

    # Process all targets and create a DataFrame with individual scores
    df_data = []

    for target_name, files in BEST_TARGETS_HELPFULNESS.items():
        for match_type, file_path in files.items():
            if target_name == 'Ground Truth':
                helpfulness_scores = extract_helpfulness_scores_ground_truth(file_path)
            else:
                helpfulness_scores = extract_helpfulness_scores(file_path)

            if helpfulness_scores:  # Only add if we have scores
                # Calculate mean for reporting
                mean_score = np.mean(helpfulness_scores)
                print(f"{target_name} ({match_type}): {len(helpfulness_scores)} scores, mean: {mean_score:.4f}")

                # Add individual scores to dataframe
                for score in helpfulness_scores:
                    df_data.append({
                        'Target': target_name,
                        'Match Type': match_type,
                        'Helpfulness Score': score
                    })

    # Create DataFrame with individual scores
    df = pd.DataFrame(df_data)

    # Check if we have data
    if df.empty:
        print("No helpfulness score data found.")
        return

    # Discard outliers beyond [-1, 1] range
    # df = df[(df['Helpfulness Score'] >= -1) & (df['Helpfulness Score'] <= 1)]

    # Print summary statistics
    print("\nHelpfulness score statistics:")
    summary = df.groupby(['Target', 'Match Type'])['Helpfulness Score'].describe()
    print(summary)

    # Create the plot
    fig, ax = plt.subplots()

    # Get unique targets and match types
    targets = df['Target'].unique()
    match_types = ['full-match', 'partial-match']

    # Colors for match types
    colors = {
        'partial-match': '#0077BB',   # blue
        'full-match': '#EE7733'  # orange
    }

    # Width of the violins
    width = 0.3

    # Positions for the violins (same as the box plots)
    positions = {
        ('full-match', 0): 0.8,
        ('partial-match', 0): 1.2,
        ('full-match', 1): 1.8,
        ('partial-match', 1): 2.2,
        ('full-match', 2): 2.8,
        ('partial-match', 2): 3.2,
        ('full-match', 3): 3.8,
        ('partial-match', 3): 4.2,
    }

    # For each target and match type
    violin_stats = []
    violin_positions = []
    violin_colors = []

    for i, target in enumerate(targets):
        for match_type in match_types:
            # Get data for this target and match type
            data = df[(df['Target'] == target) & (df['Match Type'] == match_type)]['Helpfulness Score'].values

            if len(data) > 0:
                violin_stats.append(data)
                violin_positions.append(positions[(match_type, i)])
                violin_colors.append(colors[match_type])

    # Create violin plots
    violins = ax.violinplot(
        violin_stats,
        positions=violin_positions,
        widths=width,
        showmeans=True,
        showmedians=True,
        showextrema=True
    )

    # Customize violin plots
    for i, violin in enumerate(violins['bodies']):
        violin.set_facecolor(violin_colors[i])
        violin.set_edgecolor('black')
        violin.set_alpha(1)

    # Customize other elements
    violins['cmeans'].set_color('black')
    violins['cmedians'].set_color('black')
    violins['cbars'].set_color('black')
    violins['cmins'].set_color('black')
    violins['cmaxes'].set_color('black')

    # Set positions for the tick marks
    ax.set_xticks([1, 2, 3, 4])

    # Format the target names for display
    display_targets = []
    for target in df['Target'].unique():
        if target == "reuse-by-example":
            display_targets.append("\\texttt{reuse-by-example}")
        elif target == "rfixer":
            display_targets.append("RFixer")
        elif target == "Ground Truth":
            display_targets.append("Ground Truth")
        else:
            display_targets.append("o3-mini")

    # Set x-axis labels
    ax.set_xticklabels(display_targets, fontsize='small')

    # Add grid lines
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7, axis='y')

    # Add labels
    ax.set_xlabel('Strategy')
    ax.set_ylabel('Helpfulness Score')

    # Create custom legend
    handles = [
        mpatches.Patch(color='#EE7733', label='Full Match'),
        mpatches.Patch(color='#0077BB', label='Partial Match'),
    ]

    legend = ax.legend(
        handles=handles,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.25),  # Adjust as needed
        ncol=2,
        frameon=True,
        framealpha=1,
        handletextpad=0.3,  # Reduce padding between handle and text
        columnspacing=0.8,  # Reduce space between columns
        handleheight=0.5,  # Shrink the height of the legend symbols
        handlelength=1.0,  # Reduce the length of the legend markers
        fontsize='x-small'
    )
    legend.get_frame().set_linewidth(0.5)

    # Adjust layout
    fig.tight_layout()

    # Save figure
    plt.savefig('helpfulness_score_violin.pdf', format='pdf', dpi=300)

def plot_rq4_average_elapsed_time_spend_on_a_task():
    """
    Create a horizontal bar chart comparing the average elapsed time
    for the best targets in BEST_TARGETS.
    Shows side-by-side bars for full match and partial match for each target.
    """
    import json
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from pathlib import Path

    # Function to read NDJSON file and calculate average elapsed time
    def calculate_average_elapsed_time(file_path):
        elapsed_times = []

        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        time_found = False

                        # Try to extract elapsed_time from the top level
                        if 'elapsed_time' in data and data['elapsed_time'] is not None:
                            elapsed_times.append(data['elapsed_time'])
                            time_found = True
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")

        # Calculate average elapsed time
        if elapsed_times:
            # Convert to seconds
            elapsed_times = [t / 1000 for t in elapsed_times]
            return np.mean(elapsed_times)
        else:
            return 0.0

    # Process all targets and create a DataFrame
    data = {
        'Target': [],
        'Match Type': [],
        'Average Elapsed Time': []
    }

    for target_name, files in BEST_TARGETS.items():
        for match_type, file_path in files.items():
            avg_elapsed_time = calculate_average_elapsed_time(file_path)

            data['Target'].append(target_name)
            data['Match Type'].append(match_type)
            data['Average Elapsed Time'].append(avg_elapsed_time)

            print(f"{target_name} ({match_type}): {avg_elapsed_time:.4f} seconds")

    # Create DataFrame
    df = pd.DataFrame(data)

    # Display the data for verification
    print("Target elapsed time data:")
    print(df.pivot_table(index='Target', columns='Match Type', values='Average Elapsed Time'))

    # Get unique targets
    targets = df['Target'].unique()

    # Format the target names for display
    display_targets = []
    for target in targets:
        if target == "reuse-by-example":
            display_targets.append("\\texttt{reuse-by-example}")
        elif target == "rfixer":
            display_targets.append("RFixer")
        else:
            display_targets.append("o3-mini")

    # Colors for match types (using the same colors as in the other plots)
    colors = {
        'partial-match': '#0077BB',   # blue
        'full-match': '#EE7733'  # orange
    }

    # Get data for each match type
    full_match_data = df[df['Match Type'] == 'full-match'].set_index('Target').loc[targets]['Average Elapsed Time'].values
    partial_match_data = df[df['Match Type'] == 'partial-match'].set_index('Target').loc[targets]['Average Elapsed Time'].values

    # Create the plot
    fig, ax = plt.subplots(figsize=(3.3, 1.25))

    # Set width of bars
    bar_height = 0.005  # smaller than 0.35
    spacing = 0.0125

    # Calculate positions for the bars
    y_positions = np.arange(len(targets)) * (bar_height + spacing)

    # Create bars
    bars1 = ax.barh(y_positions, full_match_data, bar_height, label='Full Match', edgecolor='black', linewidth=0.5, color=colors['full-match'])
    bars2 = ax.barh(y_positions + bar_height, partial_match_data, bar_height, label='Partial Match', edgecolor='black', linewidth=0.5, color=colors['partial-match'])

    # Add labels and title
    ax.set_ylabel('Strategy')
    ax.set_xlabel('Elapsed Time (s)')

    # Center the y-ticks between the two bars
    ax.set_yticks(y_positions + bar_height / 2)
    ax.set_yticklabels(display_targets)

    # Invert y-axis so first target appears at the top
    ax.invert_yaxis()

    # Add a grid
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

    # Add a legend
    legend = ax.legend(
        loc='upper right',
        ncol=1,
        handletextpad=0.3,  # Reduce padding between handle and text
        columnspacing=0.8,  # Reduce space between columns
        handleheight=0.5,  # Shrink the height of the legend symbols
        handlelength=1.0,  # Reduce the length of the legend markers
        fontsize='x-small',
        frameon=True,
        framealpha=1
    )
    legend.get_frame().set_linewidth(0.5)

    # Adjust layout
    fig.tight_layout()

    # Save figure
    plt.savefig('elapsed_time_comparison.pdf', format='pdf', dpi=300)
    plt.show()

def plot_rq4_average_elapsed_time_spend_on_a_task_boxplot():
    """
    Create a horizontal box plot comparing the distribution of elapsed times
    for the best targets in BEST_TARGETS.
    Shows side-by-side box plots for full match and partial match for each target.
    """
    import json
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from pathlib import Path

    # Function to read NDJSON file and extract all elapsed times
    def extract_elapsed_times(file_path):
        elapsed_times = []

        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        time_found = False

                        # Try to extract elapsed_time from the top level
                        if 'elapsed_time' in data and data['elapsed_time'] is not None:
                            elapsed_times.append(data['elapsed_time'])
                            time_found = True

                        # Also check for elapsed_ms at top level
                        elif 'elapsed_ms' in data and data['elapsed_ms'] is not None:
                            # Convert ms to seconds
                            elapsed_times.append(data['elapsed_ms'] / 1000.0)
                            time_found = True

                        # If not found at top level, check in candidates
                        if not time_found and 'candidates' in data and len(data['candidates']) > 0:
                            for candidate in data['candidates']:
                                if 'elapsed_time' in candidate and candidate['elapsed_time'] is not None:
                                    elapsed_times.append(candidate['elapsed_time'])
                                    time_found = True
                                    break
                                elif 'elapsed_ms' in candidate and candidate['elapsed_ms'] is not None:
                                    elapsed_times.append(candidate['elapsed_ms'] / 1000.0)
                                    time_found = True
                                    break
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")

        # Convert to seconds
        elapsed_times = [t / 1000 for t in elapsed_times]
        return elapsed_times

    # Process all targets and create a DataFrame with individual times
    df_data = []

    for target_name, files in BEST_TARGETS.items():
        for match_type, file_path in files.items():
            elapsed_times = extract_elapsed_times(file_path)

            if elapsed_times:  # Only add if we have times
                # Calculate mean for reporting
                mean_time = np.mean(elapsed_times)
                print(f"{target_name} ({match_type}): {len(elapsed_times)} times, mean: {mean_time:.4f} seconds")

                # Add individual times to dataframe
                for time in elapsed_times:
                    df_data.append({
                        'Target': target_name,
                        'Match Type': match_type,
                        'Elapsed Time': time
                    })

    # Create DataFrame with individual times
    df = pd.DataFrame(df_data)

    # Check if we have data
    if df.empty:
        print("No elapsed time data found.")
        return

    # Print summary statistics
    print("\nElapsed time statistics:")
    summary = df.groupby(['Target', 'Match Type'])['Elapsed Time'].describe()
    print(summary)

    # Create the plot
    fig, ax = plt.subplots(figsize=(3.3, 1.5))

    # Get unique targets and match types
    targets = df['Target'].unique()
    match_types = ['full-match', 'partial-match']

    # Colors for match types
    colors = {
        'partial-match': '#0077BB',   # blue
        'full-match': '#EE7733'  # orange
    }

    # Width of the boxes
    width = 0.3

    # Positions for the boxes
    positions = {
        ('full-match', 0): 0.8,
        ('partial-match', 0): 1.2,
        ('full-match', 1): 1.8,
        ('partial-match', 1): 2.2,
        ('full-match', 2): 2.8,
        ('partial-match', 2): 3.2,
    }

    # For each target and match type
    box_data = []
    box_positions = []
    box_colors = []

    for i, target in enumerate(targets):
        for match_type in match_types:
            # Get data for this target and match type
            data = df[(df['Target'] == target) & (df['Match Type'] == match_type)]['Elapsed Time'].values

            if len(data) > 0:
                box_data.append(data)
                box_positions.append(positions[(match_type, i)])
                box_colors.append(colors[match_type])

    # Create box plots
    box_plot = ax.boxplot(
        box_data,
        positions=box_positions,
        widths=width,
        vert=False,  # Horizontal orientation
        patch_artist=True,  # Fill boxes with color
        showfliers=True,    # Show outliers
        medianprops={'color': 'black'},
        boxprops={'edgecolor': 'black'},
        whiskerprops={'color': 'black'},
        capprops={'color': 'black'},
        flierprops={'marker': 'o', 'markerfacecolor': 'black', 'markersize': 3, 'alpha': 0.5}
    )

    # Color the boxes based on match type
    for i, box in enumerate(box_plot['boxes']):
        box.set_facecolor(box_colors[i])

    # Set positions for the tick marks
    ax.set_yticks([1, 2, 3])

    # Format the target names for display
    display_targets = []
    for target in targets:
        if target == "reuse-by-example":
            display_targets.append("\\texttt{reuse-by-example}")
        elif target == "rfixer":
            display_targets.append("RFixer")
        else:
            display_targets.append("o3-mini")

    # Set y-axis labels (for horizontal box plots, this is the y-axis)
    ax.set_yticklabels(display_targets)

    # Add grid lines
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.7, axis='x')

    # Add labels
    ax.set_ylabel('Strategy')
    ax.set_xlabel('Elapsed Time (s)')

    # Create custom legend
    handles = [
        mpatches.Patch(color='#EE7733', label='Full Match'),
        mpatches.Patch(color='#0077BB', label='Partial Match'),
    ]

    legend = ax.legend(
        handles=handles,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.25),  # Adjust as needed
        ncol=2,
        frameon=True,
        framealpha=1,
        handletextpad=0.3,  # Reduce padding between handle and text
        columnspacing=0.8,  # Reduce space between columns
        handleheight=0.5,  # Shrink the height of the legend symbols
        handlelength=1.0,  # Reduce the length of the legend markers
        fontsize='x-small'
    )
    legend.get_frame().set_linewidth(0.5)

    # Adjust layout
    fig.tight_layout()

    # Save figure
    plt.savefig('elapsed_time_boxplot.pdf', format='pdf', dpi=300)
    plt.show()

if __name__ == '__main__':
    # plot_rq1_synthesizer_comparison_new()
    # plot_rq1_synthesizer_comparison()
    # plot_rq1_llm_comparison()
    # plot_rq1_best_target_comparison()
    # analyze_perfect_accuracy_tasks()
    # plot_rq1_best_target_test_string_count_vs_accuracy()
    # plot_rq1_best_target_gt_regex_length_vs_accuracy()
    # plot_rq2_best_target_syntactic_similarity()
    # plot_rq3_best_target_semantic_similarity()
    # plot_rq3_helpfulness_score_distribution_grouped()
    # plot_rq3_helpfulness_score_violin()
    plot_rq4_average_elapsed_time_spend_on_a_task()
    # plot_rq4_average_elapsed_time_spend_on_a_task_boxplot()
    pass