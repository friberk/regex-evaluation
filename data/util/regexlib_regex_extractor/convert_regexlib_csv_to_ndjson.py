import pandas as pd
import orjson
import argparse

def csv_to_ndjson(csv_file, ndjson_file):
    # Read the CSV file with specified column types
    df = pd.read_csv(csv_file, dtype={
        'id': 'Int64',
        'title': 'string',
        'expression': 'string',
        'description': 'string',
        'matches': 'object',
        'non_matches': 'object',
        'author_source': 'string',
        'rating': 'Int64',
        'comment_count': 'Int64',
        'category': 'string'
    })

    # Open the NDJSON file in binary mode
    with open(ndjson_file, mode='wb') as ndjson_f:
        for _, row in df.iterrows():  # Iterate over each row in the DataFrame
            # Convert the row to a dictionary and serialize it to NDJSON using orjson
            ndjson_f.write(orjson.dumps(row.to_dict()))  # Serialize the row as JSON
            ndjson_f.write(b'\n')  # Write the newline character after each JSON object

if __name__ == "__main__":
    # Setting up argparse to parse command line arguments
    parser = argparse.ArgumentParser(description="Convert CSV to NDJSON.")
    parser.add_argument('--csv-file', '-c', type=str, help="Path to the input CSV file.", required=True)
    parser.add_argument('--out-file', '-o', type=str, help="Path to save the output NDJSON file.", required=True)

    args = parser.parse_args()

    # Call the conversion function with the provided arguments
    csv_to_ndjson(args.csv_file, args.out_file)
