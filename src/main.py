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
import sys
from collections import defaultdict

from .rss_reader import process_rss_feed, FeedOptions
from .output_writer import write_feed_to_html, write_feed_to_csv, write_feed_to_json, convert_feed_to_json_obj
from .config import (
    MAX_DAYS_BACK,
    MAX_START_DAYS,
    MAX_END_DAYS,
    OPML_FILENAME,
    HTML_REPORT_FOLDER,
    CSV_REPORT_FOLDER,
    JSON_REPORT_FOLDER,
    DEFAULT_START,
    DEFAULT_END,
    TEXT_DATE_FORMAT_FILE,
    TEXT_DATE_FORMAT_PRINT,
    TEXT_DATE_FORMAT_JSON,
    FEED_SEPARATOR,
    TIMEZONE_PRINT,
    MAX_LENGTH_DESCRIPTION,
    MAX_ALLOWED_LENGTH_DESCRIPTION,
    EXCLUDE_KEYWORDS,
    FEED_TITLE_KEY,
    FEED_URL_KEY,
    CYBERSECURITY_KEYWORDS
)
from .utils import print_feed_details

def validate_start(value):
    """Ensure that start is less than or equal to MAX_DAYS_BACK to limit output."""
    value = int(value)
    if value > MAX_START_DAYS:
        raise argparse.ArgumentTypeError(f"Start day offset must be less than or equal to {MAX_START_DAYS}.")
    return value

def validate_end(value):
    """Ensure that the number of days is less than or equal to MAX_DAYS_BACK to limit output."""
    value = int(value)
    if value > MAX_END_DAYS:
        raise argparse.ArgumentTypeError(f"End day offset must be less than or equal to {MAX_END_DAYS}.")
    return value

def validate_max_length_description(value):
    value = int(value)
    if value <= 0 or value > MAX_ALLOWED_LENGTH_DESCRIPTION:
        raise argparse.ArgumentTypeError(f"max-length-description must be between 1 and {MAX_ALLOWED_LENGTH_DESCRIPTION}.")
    return value

def parse_arguments(argv=None):
    description = (
        "Cyberfeedbites collects and summarises the latest cybersecurity news from "
        f"RSS feeds listed in the default OPML file ({OPML_FILENAME}), generating HTML, CSV, and JSON reports. "
        f"By default, reports are saved in these folders: HTML ({HTML_REPORT_FOLDER}), "
        f"CSV ({CSV_REPORT_FOLDER}), and JSON ({JSON_REPORT_FOLDER})."
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--start",
        type=validate_start,
        default=DEFAULT_START,
        help=f"Start day offset (days ago) to look back from today. Default is {DEFAULT_START}."
    )

    parser.add_argument(
        "--end",
        type=validate_end,
        default=DEFAULT_END,
        help=f"End day offset (days ago) to end looking back. Default is {DEFAULT_END} (today)."
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
        default="html",
        help="Comma-separated list of output formats to generate: html, csv, json. Default is html."
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

    parser.add_argument(
        "--align-end-to-midnight",
        action="store_true",
        help="Align the end date to 23:59:59 of the end day instead of current time."
    )

    parser.add_argument(
        "--html-img",
        action="store_true",
        default=False,
        help="Include images in the HTML output. Default is False."
    )

    parser.add_argument(
        "--max-length-description",
        type=validate_max_length_description,
        default=MAX_LENGTH_DESCRIPTION,
        help=f"Maximum length for RSS feed descriptions. Default is {MAX_LENGTH_DESCRIPTION}."
    )

    parser.add_argument(
        "--exclude-keywords",
        action="store_true",
        default=False,
        help="Enable exclusion of articles containing specific keywords. Default is False."
    )

    parser.add_argument(
        "--exclude-keywords-file",
        type=str,
        default=None,
        help="Path to a file containing keywords to exclude, one per line. If provided, overrides default keywords."
    )

    parser.add_argument(
        "--aggressive-filtering",
        action="store_true",
        default=False,
        help="Enable removal of articles that do NOT include any security keywords."
    )

    parser.add_argument(
        "--aggressive-keywords-file",
        type=str,
        default=None,
        help="Path to a file containing security keywords to keep, one per line. Overrides default cybersecurity keywords."
    )

    parser.add_argument(
        "--print-retrieved",
        action="store_true",
        default=False,
        help="Print retrieved articles at the end of processing. Default is False."
    )

    parser.add_argument(
        "--print-skipped",
        action="store_true",
        default=False,
        help="Print skipped articles at the end of processing. Default is False."
    )

    parser.add_argument(
        "--order-by",
        type=str,
        choices=["date", "title_date"],
        default="date",
        help="Order for HTML output: 'date' (default) or 'title_date'."
    )

    parser.add_argument(
        "--ignore-cache",
        action="store_true",
        default=False,
        help="Disable cache completely (always fetch online). Default is False."
    )

    parser.add_argument(
        "--no-conditional-cache",
        action="store_false",
        default=True,
        help="Always use cached copy without conditional headers (If-Modified-Since / ETag). Default is True."
    )

    args = parser.parse_args(argv)

    if args.start < args.end:
        raise argparse.ArgumentTypeError("Start day offset must be greater than or equal to end day offset.")

    if (args.start - args.end) > MAX_DAYS_BACK:
        raise argparse.ArgumentTypeError(f"Difference between start and end cannot exceed {MAX_DAYS_BACK} days.")

    return args

def prepare_output_folder(folder_path):
    if folder_path:
        os.makedirs(folder_path, exist_ok=True)

def print_summary(
    start_date_print,
    end_date_print,
    opml_filename,
    entries,
    skipped_entries,
    print_retrieved_entries,
    print_skipped_entries,
    html_outfilename,
    csv_outfilename,
    json_outfilename,
    errors,
    start_time,
    end_time
):
    """Prints a summary of the run."""
    print(f"{FEED_SEPARATOR}")
    print("Summary")
    print(f"{FEED_SEPARATOR}")

    print(f"Time range: {start_date_print} {TIMEZONE_PRINT} to {end_date_print} {TIMEZONE_PRINT}")
    print(f"\nOPML file: {opml_filename}")

    print(f"\nRetrieved articles: {len(entries)}")
    if print_retrieved_entries:
        grouped_entries = defaultdict(list)
        for entry in entries:
            key = (entry[FEED_TITLE_KEY], entry[FEED_URL_KEY])
            grouped_entries[key].append(entry)

        for (feedtitle, feed_url) in sorted(grouped_entries.keys()):
            articles = grouped_entries[(feedtitle, feed_url)]
            print_feed_details(feedtitle, feed_url, articles)

    print(f"\nSkipped articles: {len(skipped_entries)}")
    if print_skipped_entries:
        grouped_skipped_entries = defaultdict(list)
        for skipped in skipped_entries:
            key = (skipped[FEED_TITLE_KEY], skipped[FEED_URL_KEY])
            grouped_skipped_entries[key].append(skipped)

        for (feedtitle, feed_url) in sorted(grouped_skipped_entries.keys()):
            articles = grouped_skipped_entries[(feedtitle, feed_url)]
            print_feed_details(feedtitle, feed_url, articles)

    if html_outfilename:
        print(f"\nHTML written to file: {html_outfilename}")
    if csv_outfilename:
        print(f"\nCSV written to file: {csv_outfilename}")
    if json_outfilename:
        print(f"\njson written to file: {json_outfilename}")

    if errors:
        print("\nFeeds that failed to fetch:")
        for feedtitle, feed_url, exception in errors:
            print(f"\t- {feedtitle}: {feed_url}")

    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")
    print(f"{FEED_SEPARATOR}")

def run_cyberfeedbites(argv=None, return_raw_json=False):
    """
    Entry point for in-process invocation.
    argv: list of strings, e.g. ["--opml", "file.opml", "--start", "1"]
    """
    try:
        args = parse_arguments(argv)
        return run_main_logic(args, return_raw_json)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return 1  # non-zero exit code

def run_main_logic(args, return_raw_json=False):
    try:
        opml_filename = args.opml
        max_length_description = args.max_length_description
        output_formats = {fmt.strip().lower() for fmt in args.output_format.split(",")}
        # Decide output folders (use defaults if not provided)
        html_folder = args.output_html_folder or HTML_REPORT_FOLDER
        csv_folder = args.output_csv_folder or CSV_REPORT_FOLDER
        json_folder = args.output_json_folder or JSON_REPORT_FOLDER

        aggressive_filtering = args.aggressive_filtering
        aggressive_keywords = []

        if aggressive_filtering:
            if args.aggressive_keywords_file:
                try:
                    with open(args.aggressive_keywords_file, "r", encoding="utf-8") as f:
                        aggressive_keywords = [line.strip().lower() for line in f if line.strip()]
                except Exception as e:
                    print(f"Error reading aggressive keywords file '{args.aggressive_keywords_file}': {e}")
                    return 1
            else:
                aggressive_keywords = [kw.lower() for kw in CYBERSECURITY_KEYWORDS]
        else:
            aggressive_keywords = []

        exclude_keywords = []
        if args.exclude_keywords:
            if args.exclude_keywords_file:
                try:
                    with open(args.exclude_keywords_file, "r", encoding="utf-8") as f:
                        exclude_keywords = [line.strip().lower() for line in f if line.strip()]
                except Exception as e:
                    print(f"Error reading exclude keywords file '{args.exclude_keywords_file}': {e}")
                    return 1
            else:
                # Use default EXCLUDE_KEYWORDS from config if no file provided
                exclude_keywords = [kw.lower() for kw in EXCLUDE_KEYWORDS]

        print_retrieved_entries = args.print_retrieved
        print_skipped_entries = args.print_skipped
        order_by = args.order_by
        ignore_cache = args.ignore_cache
        no_conditional_cache = args.no_conditional_cache

        start_time = time.time()
        current_date = datetime.now(timezone.utc)        
        start_date = current_date - timedelta(days=args.start)
        end_date = current_date - timedelta(days=args.end)

        if args.align_start_to_midnight:
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        if args.align_end_to_midnight:
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        current_date_string_filename_suffix = current_date.strftime(TEXT_DATE_FORMAT_FILE)

        start_date_string_print = start_date.strftime(TEXT_DATE_FORMAT_PRINT)
        end_date_string_print = end_date.strftime(TEXT_DATE_FORMAT_PRINT)

        current_date_string_print_json = current_date.strftime(TEXT_DATE_FORMAT_JSON) 
        start_date_string_print_json = start_date.strftime(TEXT_DATE_FORMAT_JSON)
        end_date_string_print_json =  end_date.strftime(TEXT_DATE_FORMAT_JSON)

        options = FeedOptions(
            start_date=start_date,
            end_date=end_date,
            max_length_description=max_length_description,
            exclude_keywords=exclude_keywords,
            aggressive_keywords=aggressive_keywords,
            ignore_cache=ignore_cache,
            no_conditional_cache=no_conditional_cache
        )

        all_entries, skipped_entries, icon_map, opml_text, opml_title, opml_category, errors = process_rss_feed(opml_filename, options)

        base = opml_category or opml_text
        if not base:
            raise ValueError("Missing both 'category' and 'text' fields — cannot generate prefix.")
        out_filename_prefix = re.sub(r'[^a-zA-Z0-9_]', '', base.lower())

        html_outfilename = None
        csv_outfilename = None
        json_outfilename = None

        json_data = None

        if "json" in output_formats or return_raw_json:
            json_data = convert_feed_to_json_obj(
                all_entries,
                current_date_string_print_json,
                start_date_string_print_json,
                end_date_string_print_json,
                opml_text,
                opml_title,
                opml_category
            )

        if "html" in output_formats:
            prepare_output_folder(html_folder)
            html_outfilename = os.path.join(html_folder, f"{out_filename_prefix}_{current_date_string_filename_suffix}.html")

        if "csv" in output_formats:
            prepare_output_folder(csv_folder)
            csv_outfilename = os.path.join(csv_folder, f"{out_filename_prefix}_{current_date_string_filename_suffix}.csv")

        if "json" in output_formats:
            prepare_output_folder(json_folder)
            json_outfilename = os.path.join(json_folder, f"{out_filename_prefix}_{current_date_string_filename_suffix}.json")

        if "html" in output_formats:
            include_images = args.html_img
            write_feed_to_html(
            all_entries,
            html_outfilename,
            start_date_string_print,
            end_date_string_print,
            icon_map,
            opml_text,
            opml_title,
            opml_category,
            order_by,
            include_images
        )

        if "csv" in output_formats:
            write_feed_to_csv(
            all_entries, 
            csv_outfilename, 
            start_date_string_print,
            end_date_string_print,  
            opml_text, 
            opml_title,
            opml_category
        )

        if "json" in output_formats:
            write_feed_to_json(
            json_data,
            all_entries,
            json_outfilename,
            current_date_string_print_json,
            start_date_string_print_json,
            end_date_string_print_json,
            opml_text, 
            opml_title,
            opml_category
        )  

        end_time = time.time()

        print_summary(
            start_date_print = start_date_string_print,
            end_date_print = end_date_string_print,
            opml_filename = opml_filename,
            entries = all_entries,
            skipped_entries = skipped_entries,
            print_retrieved_entries = print_retrieved_entries,
            print_skipped_entries = print_skipped_entries,
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
        return 1
    
    if return_raw_json:
        return json_data
    return 0

if __name__ == "__main__":
    sys.exit(run_cyberfeedbites())