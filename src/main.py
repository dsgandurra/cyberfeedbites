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
from output_writer import split_and_write_public_json, write_feed_to_html, write_feed_to_csv, write_feed_to_json
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
    TODAY_FEED_JSON_FILE
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
        help=f"Number of days to look back for entries in the RSS feeds. Default is {DAYS_BACK}."
    )
        
    parser.add_argument(
        "--opml", 
        type=str, 
        default=OPML_FILENAME, 
        help=f"Path to the OPML file. Default is '{OPML_FILENAME}'."
    )

    parser.add_argument(
        "--public-json",
        type=str,
        help="Output folder for JSON files intended for public sharing. If specified, two JSON files covering the period from yesterday 00:00 UTC to now are generated in the specified folder. All other outputs (HTML, CSV, internal JSON) are disabled in this mode."
    )

    args = parser.parse_args()

    if args.public_json is not None and args.public_json.strip() == "":
        parser.error("--public-json cannot be empty if provided.")

    return args

def parse_args():
    """Returns parsed command-line arguments as simple values."""
    return parse_arguments()

def prepare_output_folder(html_folder_path, csv_folder_path, json_folder_path):
    """Creates the output folders if they do not exist."""
    os.makedirs(html_folder_path, exist_ok=True)
    os.makedirs(csv_folder_path, exist_ok=True)
    os.makedirs(json_folder_path, exist_ok=True)

def run_processing(opml_filename, start_date, end_date):
    """Processes the RSS feed and returns the results needed for output."""
    all_entries, icon_map, opml_text, opml_title, errors = process_rss_feed(opml_filename, start_date, end_date)
    return all_entries, icon_map, opml_text, opml_title, errors

def print_summary(
    is_internal_mode,
    days_back,
    start_date_print,
    end_date_print,
    opml_filename,
    total_entries,
    html_outfilename,
    csv_outfilename,
    json_outfilename,
    json_yesterday_filename,
    json_today_filename,
    errors,
    start_time,
    end_time
):
    """Prints a summary of the run."""
    print(f"\n{FEED_SEPARATOR}")
    print("Summary")
    print(f"{FEED_SEPARATOR}")
    
    if is_internal_mode:
        print(f"Days back: {days_back}")
    
    print(f"Time range: {start_date_print} {TIMEZONE_PRINT} to {end_date_print} {TIMEZONE_PRINT}")
    print(f"OPML file: {opml_filename}")
    print(f"Total entries: {total_entries}")

    if json_yesterday_filename or json_today_filename:
        if json_yesterday_filename:
            print(f"Yesterday JSON: {json_yesterday_filename}")
        if json_today_filename:
            print(f"Today JSON: {json_today_filename}")
    else:
        print(f"News written to file: {html_outfilename}")
        print(f"CSV written to file: {csv_outfilename}")
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
        public_json = args.public_json
        
        current_date = datetime.now(timezone.utc)
        start_time = time.time()
        
        if public_json:
            # Public json: From start of yesterday to now (i.e. covers yesterday + today's partial feed)
            start_date = datetime.combine((current_date - timedelta(days=1)).date(), dt_time(0, 0), tzinfo=timezone.utc)
            end_date = current_date

        else:
            # For internal: Use past N days
            end_date = current_date
            start_date = current_date - timedelta(days=days_back)

        current_date_string_file = end_date.strftime(TEXT_DATE_FORMAT_FILE)
        current_date_string_print = end_date.strftime(TEXT_DATE_FORMAT_PRINT)
        earliest_date_string_print = start_date.strftime(TEXT_DATE_FORMAT_PRINT) #TODO: to check

        all_entries, icon_map, opml_text, opml_title, errors = run_processing(opml_filename, start_date, end_date)
        
        out_filename_prefix = re.sub(r'[^a-zA-Z0-9_]', '', (opml_text or "").lower())
        html_outfilename = None
        csv_outfilename = None
        json_outfilename = None
        json_yesterday_filename = None
        json_today_filename = None
        json_yesterday_full_path_filename = None
        json_today_full_path_filename = None

        if public_json:
            yesterday_date = (current_date - timedelta(days=1)).strftime(TEXT_DATE_FORMAT_FILE_SHORT)
            json_yesterday_filename = f"{out_filename_prefix}_{yesterday_date}.json"
            json_today_filename = TODAY_FEED_JSON_FILE
            public_json_output_folder = os.path.join(public_json, out_filename_prefix)
            json_yesterday_full_path_filename = os.path.join(public_json_output_folder, json_yesterday_filename)
            json_today_full_path_filename = os.path.join(public_json_output_folder, json_today_filename)

            split_and_write_public_json(
                all_entries,
                public_json_output_folder,
                json_yesterday_filename,
                json_today_filename,
                yesterday_date,
                current_date.strftime(TEXT_DATE_FORMAT_FILE_SHORT),
                opml_title,
                opml_text
            )

        else:
            prepare_output_folder(HTML_REPORT_FOLDER, CSV_REPORT_FOLDER, JSON_REPORT_FOLDER)
            html_outfilename = os.path.join(HTML_REPORT_FOLDER, f"{out_filename_prefix}_{current_date_string_file}.html")
            csv_outfilename = os.path.join(CSV_REPORT_FOLDER, f"{out_filename_prefix}_{current_date_string_file}.csv")
            json_outfilename = os.path.join(JSON_REPORT_FOLDER, f"{out_filename_prefix}_{current_date_string_file}.json")

            write_feed_to_html(
                all_entries,
                html_outfilename,
                earliest_date_string_print,
                current_date_string_print,
                icon_map,
                opml_text,
                opml_title,
            )

            write_feed_to_csv(
                all_entries, 
                csv_outfilename, 
                earliest_date_string_print,
                current_date_string_print,  
                opml_text, 
                opml_title
            )

            write_feed_to_json(
                all_entries,
                json_outfilename,
                current_date.strftime(TEXT_DATE_FORMAT_FILE_SHORT),
                opml_text, 
                opml_title
            )

        end_time = time.time()

        print_summary(
            is_internal_mode = not public_json,
            days_back = days_back,
            start_date_print = earliest_date_string_print,
            end_date_print = current_date_string_print,
            opml_filename = opml_filename,
            total_entries = len(all_entries),
            html_outfilename = html_outfilename,
            csv_outfilename = csv_outfilename,
            json_outfilename = json_outfilename,
            json_yesterday_filename = json_yesterday_full_path_filename,
            json_today_filename = json_today_full_path_filename,
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