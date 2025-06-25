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
from datetime import datetime, time as dt_time, timezone, timedelta
import time
import argparse
import traceback

from rss_processor import process_rss_feed
from output_writer import write_rss_to_public_html, write_rss_to_internal_html, write_rss_to_internal_csv
from config import (
    MAX_DAYS_BACK,
    OPML_FILENAME,
    HTML_REPORT_FOLDER,
    CSV_REPORT_FOLDER,
    DAYS_BACK,
    TEXT_DATE_FORMAT_FILE,
    TEXT_DATE_FORMAT_FILE_SHORT,
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
        "RSS feeds listed in an OPML file, generating an HTML and CSV reports."
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--days", 
        type=validate_days,  # Use the custom validation function
        default=DAYS_BACK, 
        help=f"Number of days to look back for entries in the RSS feeds. Default is {DAYS_BACK}."
    )
        
    parser.add_argument(
        "--opml", 
        type=str, 
        default=OPML_FILENAME, 
        help=f"Path to the OPML file. Default is '{OPML_FILENAME}'."
    )

    parser.add_argument(
        "--public-folder",
        type=str,
        help="Path to the local folder where the public HTML report and JSON will be saved. If set, exports the report for the previous day's 24-hour period."
    )

    args = parser.parse_args()

    if args.public_folder is not None and args.public_folder.strip() == "":
        parser.error("--public-folder cannot be empty if provided.")

    return args

def parse_args():
    """Returns parsed command-line arguments as simple values."""
    return parse_arguments()

def prepare_output_folder(html_folder_path, csv_folder_path):
    """Creates the output folders if they do not exist."""
    os.makedirs(html_folder_path, exist_ok=True)
    os.makedirs(csv_folder_path, exist_ok=True)

def run_processing(opml_filename, start_date, end_date):
    """Processes the RSS feed and returns the results needed for output."""
    all_entries, icon_map, top_text, top_title, errors = process_rss_feed(opml_filename, start_date, end_date)
    return all_entries, icon_map, top_text, top_title, errors

def print_summary(days_back, earliest_date_string_print, current_date_string_print, opml_filename, total_entries, html_outfilename, html_public_outfilename, csv_outfilename, errors, start_time, end_time):
    """Prints a summary of the run."""
  
    print(f"\n{FEED_SEPARATOR}")
    print("Summary")
    print(f"{FEED_SEPARATOR}")
    print(f"Days back: {days_back}")
    print(f"Time range: {earliest_date_string_print} {TIMEZONE_PRINT} to {current_date_string_print} {TIMEZONE_PRINT}")
    print(f"OPML file: {opml_filename}")
    print(f"Total entries: {total_entries}")
    if html_public_outfilename:
        print(f"News written to public file: {html_public_outfilename}")
    else:
        print(f"News written to file: {html_outfilename}")
        print(f"CSV written to file: {csv_outfilename}")

    if errors:
        print("Feeds that failed to fetch (check individual entries log for more info):")
        for feedtitle, feed_url in errors:
            print(f"\t- {feedtitle}: {feed_url}")

    print(f"Total execution time: {end_time - start_time:.4f} seconds")
    print(f"{FEED_SEPARATOR}")

def main():
    try:
        args = parse_args()
        days_back = args.days
        opml_filename = args.opml
        public_folder = args.public_folder
        
        current_date = datetime.now(timezone.utc)
        start_time = time.time()
        
        if public_folder:
            # For public: use full 24h of previous day
            end_date = datetime.combine((current_date - timedelta(days=1)).date(), dt_time(23, 59, 59), tzinfo=timezone.utc)
            start_date = datetime.combine(end_date.date(), dt_time(0, 0), tzinfo=timezone.utc)
        else:
            # For internal: use past N days
            end_date = current_date
            start_date = current_date - timedelta(days=days_back)

        current_date_string_file = end_date.strftime(TEXT_DATE_FORMAT_FILE)
        current_date_string_file_public = end_date.strftime(TEXT_DATE_FORMAT_FILE_SHORT)
        current_date_string_print = end_date.strftime(TEXT_DATE_FORMAT_PRINT)
        earliest_date_string_print = start_date.strftime(TEXT_DATE_FORMAT_PRINT) #TODO: to check

        all_entries, icon_map, top_text, top_title, errors = run_processing(opml_filename, start_date, end_date)
        
        out_filename_prefix = re.sub(r'[^a-zA-Z0-9_]', '', (top_text or "").lower())
        html_outfilename = None
        html_public_outfilename = None
        csv_outfilename = None

        if public_folder:
            html_public_outfilename = (
            os.path.join(public_folder, f"{out_filename_prefix}_{current_date_string_file_public}.html") if public_folder else None
            )
        
            write_rss_to_public_html(
            all_entries,
            html_public_outfilename,
            earliest_date_string_print,
            current_date_string_print,
            icon_map,
            top_text,
            top_title,
            current_date_string_file_public
        )
        else:
            prepare_output_folder(HTML_REPORT_FOLDER, CSV_REPORT_FOLDER)
            html_outfilename = os.path.join(HTML_REPORT_FOLDER, f"{out_filename_prefix}_{current_date_string_file}.html")
            csv_outfilename = os.path.join(CSV_REPORT_FOLDER, f"{out_filename_prefix}_{current_date_string_file}.csv")

            write_rss_to_internal_html(
                all_entries,
                html_outfilename,
                earliest_date_string_print,
                current_date_string_print,
                icon_map,
                top_text,
                top_title,
            )

            write_rss_to_internal_csv(
            all_entries, 
            csv_outfilename, 
            earliest_date_string_print,
            current_date_string_print,  
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
            html_public_outfilename,
            csv_outfilename,
            errors,
            start_time,
            end_time
        )
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()