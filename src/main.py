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
from output_writer import write_feed_to_html, write_feed_to_csv, write_feed_to_json
from config import (
    MAX_DAYS_BACK,
    OPML_FILENAME,
    HTML_REPORT_FOLDER,
    CSV_REPORT_FOLDER,
    JSON_REPORT_FOLDER,
    DAYS_BACK,
    TEXT_DATE_FORMAT_FILE,
    TEXT_DATE_FORMAT_FILE_SHORT,
    TEXT_DATE_FORMAT_PRINT,
    FEED_SEPARATOR,
    TIMEZONE_PRINT,
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
        f"RSS feeds listed in the default OPML file ({OPML_FILENAME}), generating HTML, CSV, and JSON reports. "
        f"By default, reports are saved in these folders: HTML ({HTML_REPORT_FOLDER}), "
        f"CSV ({CSV_REPORT_FOLDER}), and JSON ({JSON_REPORT_FOLDER})."
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--days", 
        type=validate_days,  # Use the custom validation function
        default=DAYS_BACK, 
        help=f"Number of days to look back for entries in the RSS feeds, ending today. Default is {DAYS_BACK}. If --align-start-to-midnight is set, using, e.g., '2' means today and yesterday, otherwise 48 hours."
    )
        
    parser.add_argument(
        "--opml", 
        type=str, 
        default=OPML_FILENAME, 
        help=f"Path to the OPML file. Default is '{OPML_FILENAME}'."
    )

    parser.add_argument(
        "--output-format",
        type=str,
        default="html,csv,json",
        help="Comma-separated list of output formats to generate: html, csv, json. Default is all."
    )

    parser.add_argument(
        "--output-html-folder",
        type=str,
        default=HTML_REPORT_FOLDER,
        help="Output folder for HTML reports. Default is configured default folder."
    )

    parser.add_argument(
        "--output-csv-folder",
        type=str,
        default=CSV_REPORT_FOLDER,
        help="Output folder for CSV reports. Default is configured default folder."
    )

    parser.add_argument(
        "--output-json-folder",
        type=str,
        default=JSON_REPORT_FOLDER,
        help="Output folder for JSON reports. Default is configured default folder."
    )

    parser.add_argument(
    "--align-start-to-midnight",
    action="store_true",
    help="Align the start date to midnight of the first day instead of counting exact hours back."
    )

    args = parser.parse_args()
    return args

def parse_args():
    """Returns parsed command-line arguments as simple values."""
    return parse_arguments()

def prepare_output_folder(folder_path):
    if folder_path:
        os.makedirs(folder_path, exist_ok=True)

def run_processing(opml_filename, start_date, end_date):
    """Processes the RSS feed and returns the results needed for output."""
    all_entries, icon_map, opml_text, opml_title, errors = process_rss_feed(opml_filename, start_date, end_date)
    return all_entries, icon_map, opml_text, opml_title, errors

def print_summary(
    days_back,
    align_start_to_midnight,
    start_date_print,
    end_date_print,
    opml_filename,
    total_entries,
    html_outfilename,
    csv_outfilename,
    json_outfilename,
    errors,
    start_time,
    end_time
):
    """Prints a summary of the run."""
    print(f"\n{FEED_SEPARATOR}")
    print("Summary")
    print(f"{FEED_SEPARATOR}")
    if align_start_to_midnight:
        print(f"Days back: {days_back} (aligned to midnight)")
    else:
        print(f"Days back: {days_back} (rolling {days_back * 24} hours)")
    print(f"Time range: {start_date_print} {TIMEZONE_PRINT} to {end_date_print} {TIMEZONE_PRINT}")
    print(f"OPML file: {opml_filename}")
    print(f"Total entries: {total_entries}")

    if html_outfilename:
        print(f"News written to file: {html_outfilename}")
    if csv_outfilename:
        print(f"CSV written to file: {csv_outfilename}")
    if json_outfilename:
        print(f"json written to file: {json_outfilename}")

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
        output_formats = {fmt.strip().lower() for fmt in args.output_format.split(",")}
        # Decide output folders (use defaults if not provided)
        html_folder = args.output_html_folder or HTML_REPORT_FOLDER
        csv_folder = args.output_csv_folder or CSV_REPORT_FOLDER
        json_folder = args.output_json_folder or JSON_REPORT_FOLDER

        start_time = time.time()

        current_date = datetime.now(timezone.utc)        
        end_date = current_date

        if args.align_start_to_midnight:
            aligned_start = current_date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_back - 1)
            start_date = aligned_start
        else:
            start_date = current_date - timedelta(days=days_back)

        current_date_string_file = end_date.strftime(TEXT_DATE_FORMAT_FILE)
        current_date_string_print = end_date.strftime(TEXT_DATE_FORMAT_PRINT)
        earliest_date_string_print = start_date.strftime(TEXT_DATE_FORMAT_PRINT) #TODO: to check

        all_entries, icon_map, opml_text, opml_title, errors = run_processing(opml_filename, start_date, end_date)
        
        out_filename_prefix = re.sub(r'[^a-zA-Z0-9_]', '', (opml_text or "").lower())
        html_outfilename = None
        csv_outfilename = None
        json_outfilename = None

        if "html" in output_formats:
            prepare_output_folder(html_folder)
            html_outfilename = os.path.join(html_folder, f"{out_filename_prefix}_{current_date_string_file}.html")

        if "csv" in output_formats:
            prepare_output_folder(csv_folder)
            csv_outfilename = os.path.join(csv_folder, f"{out_filename_prefix}_{current_date_string_file}.csv")

        if "json" in output_formats:
            prepare_output_folder(json_folder)
            json_outfilename = os.path.join(json_folder, f"{out_filename_prefix}_{current_date_string_file}.json")

        if "html" in output_formats:
            write_feed_to_html(
            all_entries,
            html_outfilename,
            earliest_date_string_print,
            current_date_string_print,
            icon_map,
            opml_text,
            opml_title,
        )

        if "csv" in output_formats:
            write_feed_to_csv(
            all_entries, 
            csv_outfilename, 
            earliest_date_string_print,
            current_date_string_print,  
            opml_text, 
            opml_title
        )

        if "json" in output_formats:
            write_feed_to_json(
            all_entries,
            json_outfilename,
            current_date.strftime(TEXT_DATE_FORMAT_FILE_SHORT),
            opml_text, 
            opml_title
        )  

        end_time = time.time()

        print_summary(
            days_back = days_back,
            align_start_to_midnight = args.align_start_to_midnight,
            start_date_print = earliest_date_string_print,
            end_date_print = current_date_string_print,
            opml_filename = opml_filename,
            total_entries = len(all_entries),
            html_outfilename = html_outfilename,
            csv_outfilename = csv_outfilename,
            json_outfilename = json_outfilename,
            errors = errors,
            start_time = start_time,
            end_time = end_time
        )

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()