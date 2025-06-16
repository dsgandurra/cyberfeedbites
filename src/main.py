import sys
import time
import os
import argparse
from datetime import datetime, timezone

from rss_processor import process_rss_feed
from output_writer import write_all_rss_to_html
from config import MAX_DAYS_BACK, OPML_FILENAME, HTML_REPORT_FOLDER, HTML_OUT_FILENAME_PREFIX, DAYS_BACK, TEXT_DATE_FORMAT_FILE, TEXT_DATE_FORMAT_PRINT, FEED_SEPARATOR, TIMEZONE_PRINT

def validate_days(value):
    """Ensure that the number of days is less than or equal to MAX_DAYS_BACK to limit output."""
    value = int(value)
    if value > MAX_DAYS_BACK:
        raise argparse.ArgumentTypeError(f"Number of days must be less than or equal to {MAX_DAYS_BACK}.")
    return value

def parse_arguments():
    description = (
        "Cyberfeedbites collects and summarises the latest cybersecurity news from "
        "RSS feeds listed in an OPML file, generating an HTML report."
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--days", 
        type=validate_days,  # Use the custom validation function
        default=DAYS_BACK, 
        help=f"Number of days back to look for entries. Default is {DAYS_BACK}."
    )
        
    parser.add_argument(
        "--opml", 
        type=str, 
        default=OPML_FILENAME, 
        help=f"Path to the OPML file. Default is '{OPML_FILENAME}'."
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    days_back = args.days
    opml_filename = args.opml
    
    # To add a timestamp to the filename
    current_date = datetime.now(timezone.utc)
    current_date_string_file = current_date.strftime(TEXT_DATE_FORMAT_FILE)
    current_date_string_print = current_date.strftime(TEXT_DATE_FORMAT_PRINT)
    
    # Check if the report folder exists, if not, create it
    if not os.path.exists(HTML_REPORT_FOLDER):
        os.makedirs(HTML_REPORT_FOLDER)
        print(f"Created the folder: {HTML_REPORT_FOLDER}")

    html_outfilename = os.path.join(HTML_REPORT_FOLDER, f"{HTML_OUT_FILENAME_PREFIX}_{current_date_string_file}.html")
    all_entries = []

    start_time = time.time()
    # Run the main processing function
    all_entries, earliest_date, icon_map = process_rss_feed(opml_filename, days_back)
    earliest_date_string_print = earliest_date.strftime(TEXT_DATE_FORMAT_PRINT)
    # Write the output to HTML
    write_all_rss_to_html(all_entries, html_outfilename, current_date_string_print, earliest_date_string_print, icon_map)
    end_time = time.time()

    # Print execution details
    print(f"\n{FEED_SEPARATOR}")
    print("Summary")
    print(f"{FEED_SEPARATOR}")
    print(f"Days back: {days_back}")
    print(f"Time range: {earliest_date_string_print} {TIMEZONE_PRINT} to {current_date_string_print} {TIMEZONE_PRINT}")
    print(f"OPML file: {opml_filename}")
    print(f"Total entries: {len(all_entries)}")
    print(f"News written to file: {html_outfilename}")
    print(f"Total execution time: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    main()