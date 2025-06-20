# CyberFeedBites – Lightweight Cybersecurity RSS Reader
# Copyright (C) 2024–2025 Daniele Sgandurra
#
# This file is part of CyberFeedBites.
#
# CyberFeedBites is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CyberFeedBites is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import re
import time
from datetime import datetime, timezone
import argparse

from rss_processor import process_rss_feed
from output_writer import write_all_rss_to_html
from config import (
    MAX_DAYS_BACK,
    OPML_FILENAME,
    HTML_REPORT_FOLDER,
    DAYS_BACK,
    TEXT_DATE_FORMAT_FILE,
    TEXT_DATE_FORMAT_PRINT,
    FEED_SEPARATOR,
    TIMEZONE_PRINT
)

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

def parse_args():
    """Returns parsed command-line arguments as simple values."""
    args = parse_arguments()
    return args.days, args.opml

def prepare_output_folder(folder_path):
    """Creates the output folder if it does not exist."""
    os.makedirs(folder_path, exist_ok=True)

def run_processing(opml_filename, days_back):
    """Processes the RSS feed and returns the results needed for output."""
    all_entries, earliest_date, icon_map, top_text, top_title, errors = process_rss_feed(opml_filename, days_back)
    earliest_date_string_print = earliest_date.strftime(TEXT_DATE_FORMAT_PRINT)
    return all_entries, earliest_date_string_print, icon_map, top_text, top_title, errors

def print_summary(days_back, earliest_date_string_print, current_date_string_print, opml_filename, total_entries, html_outfilename, errors, start_time, end_time):
    """Prints a summary of the run."""
    print(f"\n{FEED_SEPARATOR}")
    print("Summary")
    print(f"{FEED_SEPARATOR}")
    print(f"Days back: {days_back}")
    print(f"Time range: {earliest_date_string_print} {TIMEZONE_PRINT} to {current_date_string_print} {TIMEZONE_PRINT}")
    print(f"OPML file: {opml_filename}")
    print(f"Total entries: {total_entries}")
    print(f"News written to file: {html_outfilename}")

    if errors:
        print("Feeds that failed to fetch (check individual entries log for more info):")
        for feedtitle, feed_url in errors:
            print(f"\t- {feedtitle}: {feed_url}")

    print(f"Total execution time: {end_time - start_time:.4f} seconds")
    print(f"{FEED_SEPARATOR}")

def main():
    days_back, opml_filename = parse_args()

    current_date = datetime.now(timezone.utc)
    current_date_string_file = current_date.strftime(TEXT_DATE_FORMAT_FILE)
    current_date_string_print = current_date.strftime(TEXT_DATE_FORMAT_PRINT)

    prepare_output_folder(HTML_REPORT_FOLDER)

    start_time = time.time()
    all_entries, earliest_date_string_print, icon_map, top_text, top_title, errors = run_processing(opml_filename, days_back)
    
    html_out_filename_prefix = re.sub(r'[^a-zA-Z0-9_]', '', (top_text or "").lower())
    html_outfilename = os.path.join(HTML_REPORT_FOLDER, f"{html_out_filename_prefix}_{current_date_string_file}.html")
    
    write_all_rss_to_html(
        all_entries,
        html_outfilename,
        current_date_string_print,
        earliest_date_string_print,
        icon_map,
        top_text,
        top_title
    )   
    end_time = time.time()

    print_summary(
        days_back,
        earliest_date_string_print,
        current_date_string_print,
        opml_filename,
        len(all_entries),
        html_outfilename,
        errors,
        start_time,
        end_time
    )

if __name__ == "__main__":
    main()