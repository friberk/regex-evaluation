# RegexLib Scraper

import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
import logging
from tqdm import tqdm
import sys
import re
import csv
import argparse

# CSV output settings
FIELDNAMES = ["id", "title", "expression", "description", "matches", "non_matches", "author_source", "rating", "comment_count", "category"]

URL_TEMPLATE = "https://www.regexlib.com/REDetails.aspx?regexp_id={regex_id}"
SEARCH_START = 1
SEARCH_END = 35500 # 35014 is the last known ID, as of Aug 2025

CATEGORIES = {
    1: {"name": "Email", "ids": []},
    2: {"name": "Uri", "ids": []},
    3: {"name": "Numbers", "ids": []},
    4: {"name": "Strings", "ids": []},
    5: {"name": "Dates and Times", "ids": []},
    6: {"name": "Misc", "ids": []},
    7: {"name": "Address/Phone", "ids": []},
    8: {"name": "Markup/Code", "ids": []}
}

SEARCH_TEMPLATE = "https://www.regexlib.com/Search.aspx?k=&c={category}&m=-1&ps=100&p={page}"

def decode_cfemail(encoded_str):
    r = int(encoded_str[:2], 16)
    email = ''.join(
        chr(int(encoded_str[i:i+2], 16) ^ r)
        for i in range(2, len(encoded_str), 2)
    )
    return email

def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def init_csv():
    """Initialize CSV with headers and proper dtypes if not present."""
    if not os.path.exists(CSV_FILE):
        # create empty DataFrame with specified dtypes
        df = pd.DataFrame(columns=FIELDNAMES)
        df = df.astype({
            'id': 'Int64',
            'title': 'string',
            'expression': 'string',
            'description': 'string',
            'matches': 'object',
            'non_matches': 'object',
            'author_source': 'string',
            'rating': 'Int64',
            'comment_count': 'Int64',
            'category': 'string',
        })
        df.to_csv(CSV_FILE, header=True, index=False, quoting=csv.QUOTE_ALL)

def append_to_csv(details):
    """Append a single row to CSV using pandas, preserving dtypes."""
    row = details.copy()
    # build single-row DataFrame and cast dtypes
    df_row = pd.DataFrame([row])
    df_row = df_row.astype({
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
    # append without header
    df_row.to_csv(CSV_FILE, mode='a', header=False, index=False, quoting=csv.QUOTE_ALL)

def fetch_regex_details(regex_id):
    url = URL_TEMPLATE.format(regex_id=regex_id)
    response = requests.get(url)
    if response.status_code != 200:
        logging.warning(f"Failed to fetch details for ID {regex_id}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    invalid_expression = soup.select_one("#ctl00_ContentPlaceHolder1_InvalidExpression")
    if invalid_expression:
        logging.info(f"Invalid expression for ID {regex_id}")
        return None

    # Extract the regex pattern
    # Fields, title, expression, description, matches[], nonMatches[], author_source, rating
    # Title = ctl00_ContentPlaceHolder1_TitleLabel
    # Expression = ctl00_ContentPlaceHolder1_ExpressionLabel
    # Description = ctl00_ContentPlaceHolder1_DescriptionLabel
    # Matches = ctl00_ContentPlaceHolder1_MatchesLabel: it is a span contains matched string. Each string is seperated by <span class="separator">|</span>
    # NonMatches = ctl00_ContentPlaceHolder1_NonMatchesLabel: it is a span contains non-matched string. Each string is seperated by <span class="separator">|</span>
    # Author Source = ctl00_ContentPlaceHolder1_AuthorHyperlink
    # Rating is an img inside <span class="rating">: it is a star rating, each star is an img with src="App_Themes/Green/images/Rating3.png" or "App_Themes/Green/images/Rating4.png" If there is no img inside <span class="rating">, it means the regex has no rating, so rating is N/A or None
    title = soup.select_one("#ctl00_ContentPlaceHolder1_TitleLabel").get_text(strip=True)
    expression = soup.select_one("#ctl00_ContentPlaceHolder1_ExpressionLabel").get_text(strip=True)
    description = soup.select_one("#ctl00_ContentPlaceHolder1_DescriptionLabel").get_text(strip=True)
    matches = soup.select_one("#ctl00_ContentPlaceHolder1_MatchesLabel")
    non_matches = soup.select_one("#ctl00_ContentPlaceHolder1_NonMatchesLabel")
    author_source = soup.select_one("#ctl00_ContentPlaceHolder1_AuthorHyperlink").get_text(strip=True)
    rating_span = soup.select_one("span.rating")
    rating = None
    if rating_span:
        rating_imgs = rating_span.find_all("img")
        if rating_imgs:
            # Get the src of the first img to determine the rating
            rating_src = rating_imgs[0].get("src", "")
            rating = int(rating_src[-5])
    # extract matches by iterating children and splitting on separator spans
    matches_list = []
    for child in matches.children:
        if child.name == "a" and "__cf_email__" in child.get("class", []):
            # decode Cloudflare email protection
            encoded_email = child.get("data-cfemail", "")
            if encoded_email:
                email = decode_cfemail(encoded_email)
                matches_list.append(email)
        elif child.name == "span" and "separator" in child.get("class", []):
            # separator spans are used to split matches
            continue
        elif isinstance(child, str):
            # Split using this regex to handle various separator formats:
            # (?: \| )|(?:\| )|(?: \|)|(?:(?<=\S)\|(?=\S))
            to_append = re.split(r'(?: \| )|(?:\| )|(?: \|)|(?:(?<=\S)\|(?=\S))', child.strip())
            # Trim the first and last characters
            to_append2 = []
            for m in to_append:
                if m.startswith(' ') or m.startswith('|'):
                    m = m[1:]
                if m.endswith(' ') or m.endswith('|'):
                    m = m[:-1]
                to_append2.append(m)
            if to_append2:
                matches_list.extend([m.strip() for m in to_append2 if m.strip()])

    # extract non-matches similarly
    non_matches_list = []
    for child in non_matches.children:
        if child.name == "a" and "__cf_email__" in child.get("class", []):
            # decode Cloudflare email protection
            encoded_email = child.get("data-cfemail", "")
            if encoded_email:
                email = decode_cfemail(encoded_email)
                non_matches_list.append(email)
        elif child.name == "span" and "separator" in child.get("class", []):
            # separator spans are used to split non-matches
            continue
        elif isinstance(child, str):
            # Split using this regex to handle various separator formats:
            # (?: \| )|(?:\| )|(?: \|)|(?:(?<=\S)\|(?=\S))
            to_append = re.split(r'(?: \| )|(?:\| )|(?: \|)|(?:(?<=\S)\|(?=\S))', child.strip())
            # Trim the first and last characters
            to_append2 = []
            for m in to_append:
                if m.startswith(' ') or m.startswith('|'):
                    m = m[1:]
                if m.endswith(' ') or m.endswith('|'):
                    m = m[:-1]
                to_append2.append(m)
            if to_append2:
                non_matches_list.extend([m.strip() for m in to_append2 if m.strip()])

    # comment_count = number of <p> elements that contain <b>Title: </b> <b>Name: </b> <b>Date: </b> <b>Comment: </b>
    comment_count = len(soup.select("p:has(b:contains('Title: ')), p:has(b:contains('Name: ')), p:has(b:contains('Date: ')), p:has(b:contains('Comment: '))"))

    return {
        "id": regex_id,
        "title": title,
        "expression": expression,
        "description": description,
        "matches": matches_list,
        "non_matches": non_matches_list,
        "author_source": author_source,
        "rating": rating,
        "comment_count": comment_count,
        "category": None  # Category will be determined later
    }

def fetch_categories():
    for category_id, category in CATEGORIES.items():
        current_page = 1
        while True:
            url = SEARCH_TEMPLATE.format(category=category_id, page=current_page)
            response = requests.get(url)
            if response.status_code != 200:
                logging.warning(f"Failed to fetch categories for ID {category_id}")
                return None
            soup = BeautifulSoup(response.content, 'html.parser')

            current_page = int(soup.select_one("#ctl00_ContentPlaceHolder1_Pager1_CurrentPageLabel").get_text(strip=True))
            total_pages = int(soup.select_one("#ctl00_ContentPlaceHolder1_Pager1_TotalPagesLabel").get_text(strip=True))

            if current_page > total_pages:
                break

            # Get all tables with class searchResultsTable
            tables = soup.select("table.searchResultsTable")
            for table in tables:
                # Get tbody > tr class="title" > td > first a > href
                href = table.select_one("tr.title > td > a")
                regex_id = href.get("href").split("=")[1]
                category["ids"].append(int(regex_id))
            current_page += 1
    return CATEGORIES

def add_categories_to_csv(csv_file):
    df = pd.read_csv(csv_file, dtype={'id': 'Int64', 'title': 'string', 'expression': 'string',
                                       'description': 'string', 'matches': 'object',
                                       'non_matches': 'object', 'author_source': 'string',
                                       'rating': 'Int64', 'comment_count': 'Int64',
                                       'category': 'string'})
    for category_id, category in CATEGORIES.items():
        for regex_id in category["ids"]:
            df.loc[df["id"] == regex_id, "category"] = category["name"]
    df.to_csv(csv_file, header=True, index=False, quoting=csv.QUOTE_ALL)

def post_process_csv(csv_file):
    """Post-process the CSV to add categories based on regex patterns."""
    df = pd.read_csv(csv_file, dtype={'id': 'Int64', 'title': 'string', 'expression': 'string',
                                       'description': 'string', 'matches': 'object',
                                       'non_matches': 'object', 'author_source': 'string',
                                       'rating': 'Int64', 'comment_count': 'Int64',
                                       'category': 'string'})

    # Fix protected email addresses in descriptions
    for i, row in tqdm(df.iterrows(), total=len(df), desc="Post-processing CSV", unit="row", dynamic_ncols=False, file=sys.stderr):
        if (row["description"] is not pd.NA) and ("protected]" in row["description"]):
            url = URL_TEMPLATE.format(regex_id=row["id"])
            response = requests.get(url)
            if response.status_code != 200:
                logging.warning(f"Failed to fetch details for ID {row['id']} during post-processing")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            description = soup.select_one("#ctl00_ContentPlaceHolder1_DescriptionLabel")

            description_str = ""
            for child in description.children:
                if child.name == "a" and "__cf_email__" in child.get("class", []):
                    # decode Cloudflare email protection
                    encoded_email = child.get("data-cfemail", "")
                    if encoded_email:
                        email = decode_cfemail(encoded_email)
                        description_str += email
                elif isinstance(child, str):
                    description_str += child
            description_str = description_str.strip()

            df.at[i, "description"] = description_str

        # Remove newlines in all fields \n to \n\n
        if (row["description"] is not pd.NA):
            df.at[i, "description"] = str(df.at[i, "description"]).replace("\n", r"\\n")
            df.at[i, "description"] = str(df.at[i, "description"]).replace("\r", r"\\r")
            df.at[i, "description"] = str(df.at[i, "description"]).replace("\t", r"\\t")

        if (row["title"] is not pd.NA):
            df.at[i, "title"] = str(df.at[i, "title"]).replace("\n", r"\\n")
            df.at[i, "title"] = str(df.at[i, "title"]).replace("\r", r"\\r")
            df.at[i, "title"] = str(df.at[i, "title"]).replace("\t", r"\\t")

        if (row["expression"] is not pd.NA):
            df.at[i, "expression"] = str(df.at[i, "expression"]).replace("\n", r"\\n")
            df.at[i, "expression"] = str(df.at[i, "expression"]).replace("\r", r"\\r")
            df.at[i, "expression"] = str(df.at[i, "expression"]).replace("\t", r"\\t")

    # Output the post-processed DataFrame to a new CSV file
    df.to_csv(csv_file, header=True, index=False, quoting=csv.QUOTE_ALL)

def scrape_regexlib(start=SEARCH_START, end=SEARCH_END):
    init_csv()
    for regex_id in tqdm(range(start, end + 1), desc="Scraping regexlib", unit="id", dynamic_ncols=False, file=sys.stderr):
        details = fetch_regex_details(regex_id)
        if details:
            append_to_csv(details)
            logging.info(f"Appended details for ID {regex_id}: {details['title']}")
        else:
            logging.warning(f"Skipping ID {regex_id} due to errors or invalid expression.")

if __name__ == "__main__":
    global CSV_FILE

    parser = argparse.ArgumentParser(description="Scrape RegExLib regexes and output to CSV")
    parser.add_argument("--out-file", "-o", help="Output file", required=True)
    args = parser.parse_args()

    CSV_FILE = args.out_file

    # scrape_regexlib()
    fetch_categories()
    add_categories_to_csv(CSV_FILE)
    post_process_csv(CSV_FILE)
