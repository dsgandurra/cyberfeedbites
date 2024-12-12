import sys
import time
import os
from datetime import datetime

from rss_processor import process_rss_feed
from output_writer import write_all_rss_to_html
from config import OPML_FILENAME, HTML_REPORT_FOLDER, HTML_OUT_FILENAME_PREFIX, DAYS_BACK, TEXT_DATE_FORMAT

def main():
    """Main entry point to set up the paths and call the processing function."""
    
    # To add a timestamp to the filename
    current_date = datetime.now()
    current_date_string = current_date.strftime(TEXT_DATE_FORMAT) #this format can be used in filenames

    
# Check if the report folder exists, if not, create it
    if not os.path.exists(HTML_REPORT_FOLDER):
        os.makedirs(HTML_REPORT_FOLDER)
        print(f"Created the folder: {HTML_REPORT_FOLDER}")

    # Use os.path.join for cross-platform compatibility
    html_outfilename = os.path.join(HTML_REPORT_FOLDER, f"{HTML_OUT_FILENAME_PREFIX}_{current_date_string}.html")
    all_entries = []

    start_time = time.time()
    # Run the main processing function
    all_entries, earliest_time = process_rss_feed(OPML_FILENAME, DAYS_BACK)
    earliest_time_string = earliest_time.strftime(TEXT_DATE_FORMAT)
    # Write the output to HTML
    write_all_rss_to_html(all_entries, html_outfilename, current_date_string, earliest_time_string)
    end_time = time.time()

    # Print execution details
    print(f"Entries from: {earliest_time_string} to {current_date_string}")
    print(f"Total entries: {len(all_entries)}")
    print(f"News written to file: {html_outfilename}")
    print(f"Total execution time: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    main()