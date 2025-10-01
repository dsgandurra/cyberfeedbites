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
from urllib.parse import urlparse

from .rss_reader import process_rss_feed, check_rss_health, check_single_feed, FeedOptions
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
    CYBERSECURITY_KEYWORDS,
    OUTPUT_FORMAT,
    ALIGN_START_TO_MIDNIGHT,
    ALIGN_END_TO_MIDNIGHT,
    HTML_IMG,
    EXCLUDE_KEYWORDS_FILE,
    AGGRESSIVE_FILTERING,
    AGGRESSIVE_KEYWORDS_FILE,
    PRINT_RETRIEVED,
    PRINT_SKIPPED,
    ORDER_BY,
    IGNORE_CACHE,
    NO_CONDITIONAL_CACHE,
    CHECK_FEEDS,
    SETTINGS_YAML,
    build_user_options
)
from .utils import print_feed_details, load_yaml_config

def validate_start(value):
    value = int(value)
    if value > MAX_START_DAYS:
        raise argparse.ArgumentTypeError(f"Start day offset must be less than or equal to {MAX_START_DAYS}.")
    return value

def validate_end(value):
    value = int(value)
    if value > MAX_END_DAYS:
        raise argparse.ArgumentTypeError(f"End day offset must be less than or equal to {MAX_END_DAYS}.")
    return value

def validate_max_length_description(value):
    value = int(value)
    if value <= 0 or value > MAX_ALLOWED_LENGTH_DESCRIPTION:
        raise argparse.ArgumentTypeError(f"max-length-description must be between 1 and {MAX_ALLOWED_LENGTH_DESCRIPTION}.")
    return value

def validate_feed_url(value: str) -> str:
    """Ensure the provided feed URL is a non-empty, valid URL."""
    if not value:
        raise argparse.ArgumentTypeError("Feed URL cannot be empty.")
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        raise argparse.ArgumentTypeError(f"Invalid URL: {value}")
    return value

def parse_arguments(user_options, argv=None):
    description = (
        "Cyberfeedbites collects and summarises the latest cybersecurity news from "
        f"RSS feeds listed in the default OPML file ({user_options['OPML_FILENAME'].value}), generating HTML, CSV, and JSON reports. "
        f"By default, reports are saved in these folders: HTML ({user_options['HTML_REPORT_FOLDER'].value}), "
        f"CSV ({user_options['CSV_REPORT_FOLDER'].value}), and JSON ({user_options['JSON_REPORT_FOLDER'].value})."
    )
    parser = argparse.ArgumentParser(description=description)

    def output_format_type(value):
        if value is None or value.lower() == "none":
            return None
        return value

    parser.add_argument(
        f"--{user_options['DEFAULT_START'].cli_name}",
        type=validate_start,
        default=user_options['DEFAULT_START'].value,
        help=f"Start day offset (days ago) to look back from today. Default is {user_options['DEFAULT_START'].value}."
    )

    parser.add_argument(
        f"--{user_options['DEFAULT_END'].cli_name}",
        type=validate_end,
        default=user_options['DEFAULT_END'].value,
        help=f"End day offset (days ago) to end looking back. Default is {user_options['DEFAULT_END'].value} (today)."
    )

    parser.add_argument(
        f"--{user_options['OPML_FILENAME'].cli_name}",
        type=str,
        default=user_options['OPML_FILENAME'].value,
        help=f"Path to the OPML file. Default is '{user_options['OPML_FILENAME'].value}'."
    )

    parser.add_argument(
        f"--{user_options['OUTPUT_FORMAT'].cli_name}",
        type=output_format_type,
        nargs='?',
        const=None,
        default=user_options['OUTPUT_FORMAT'].value,
        help=f"Comma-separated list of output formats to generate: html, csv, json. "
             f"Use 'None' or omit value for no output. Default is {user_options['OUTPUT_FORMAT'].value}."
    )

    parser.add_argument(
        f"--{user_options['HTML_REPORT_FOLDER'].cli_name}",
        type=str,
        default=user_options['HTML_REPORT_FOLDER'].value,
        help=f"Output folder for HTML reports. Default is {user_options['HTML_REPORT_FOLDER'].value}."
    )

    parser.add_argument(
        f"--{user_options['CSV_REPORT_FOLDER'].cli_name}",
        type=str,
        default=user_options['CSV_REPORT_FOLDER'].value,
        help=f"Output folder for CSV reports. Default is {user_options['CSV_REPORT_FOLDER'].value}."
    )

    parser.add_argument(
        f"--{user_options['JSON_REPORT_FOLDER'].cli_name}",
        type=str,
        default=user_options['JSON_REPORT_FOLDER'].value,
        help=f"Output folder for JSON reports. Default is {user_options['JSON_REPORT_FOLDER'].value}."
    )

    parser.add_argument(
        f"--{user_options['ALIGN_START_TO_MIDNIGHT'].cli_name}",
        action="store_true",
        default=user_options['ALIGN_START_TO_MIDNIGHT'].value,
        help="Align the start date to midnight of the first day instead of counting exact hours back."
    )

    parser.add_argument(
        f"--{user_options['ALIGN_END_TO_MIDNIGHT'].cli_name}",
        action="store_true",
        default=user_options['ALIGN_END_TO_MIDNIGHT'].value,
        help="Align the end date to 23:59:59 of the end day instead of current time."
    )

    parser.add_argument(
        f"--{user_options['HTML_IMG'].cli_name}",
        action="store_true",
        default=user_options['HTML_IMG'].value,
        help=f"Include images in the HTML output. Default is {user_options['HTML_IMG'].value}."
    )

    parser.add_argument(
        f"--{user_options['MAX_LENGTH_DESCRIPTION'].cli_name}",
        type=validate_max_length_description,
        default=user_options['MAX_LENGTH_DESCRIPTION'].value,
        help=f"Maximum length for RSS feed descriptions. Default is {user_options['MAX_LENGTH_DESCRIPTION'].value}."
    )

    parser.add_argument(
        f"--{user_options['EXCLUDE_KEYWORDS'].cli_name}",
        action="store_true",
        default=user_options['EXCLUDE_KEYWORDS'].value,
        help=f"Enable exclusion of articles containing specific keywords. Default is {user_options['EXCLUDE_KEYWORDS'].value}."
    )

    parser.add_argument(
        f"--{user_options['EXCLUDE_KEYWORDS_FILE'].cli_name}",
        type=str,
        default=user_options['EXCLUDE_KEYWORDS_FILE'].value,
        help=f"Path to a file containing keywords to exclude, one per line. Default is {user_options['EXCLUDE_KEYWORDS_FILE'].value}."
    )

    parser.add_argument(
        f"--{user_options['AGGRESSIVE_FILTERING'].cli_name}",
        action="store_true",
        default=user_options['AGGRESSIVE_FILTERING'].value,
        help=f"Enable removal of articles that do NOT include any security keywords. Default is {user_options['AGGRESSIVE_FILTERING'].value}."
    )

    parser.add_argument(
        f"--{user_options['AGGRESSIVE_KEYWORDS_FILE'].cli_name}",
        type=str,
        default=user_options['AGGRESSIVE_KEYWORDS_FILE'].value,
        help=f"Path to a file containing security keywords to keep, one per line. Default is {user_options['AGGRESSIVE_KEYWORDS_FILE'].value}."
    )

    parser.add_argument(
        f"--{user_options['PRINT_RETRIEVED'].cli_name}",
        action="store_true",
        default=user_options['PRINT_RETRIEVED'].value,
        help=f"Print retrieved articles at the end of processing. Default is {user_options['PRINT_RETRIEVED'].value}."
    )

    parser.add_argument(
        f"--{user_options['PRINT_SKIPPED'].cli_name}",
        action="store_true",
        default=user_options['PRINT_SKIPPED'].value,
        help=f"Print skipped articles at the end of processing. Default is {user_options['PRINT_SKIPPED'].value}."
    )

    parser.add_argument(
        f"--{user_options['ORDER_BY'].cli_name}",
        type=str,
        choices=["date", "title_date"],
        default=user_options['ORDER_BY'].value,
        help=f"Order for HTML output: 'date' (default) or 'title_date'. Default is {user_options['ORDER_BY'].value}."
    )

    parser.add_argument(
        f"--{user_options['IGNORE_CACHE'].cli_name}",
        action="store_true",
        default=user_options['IGNORE_CACHE'].value,
        help=f"Disable cache completely (always fetch online). Default is {user_options['IGNORE_CACHE'].value}."
    )

    parser.add_argument(
        f"--{user_options['NO_CONDITIONAL_CACHE'].cli_name}",
        action="store_false",
        default=user_options['NO_CONDITIONAL_CACHE'].value,
        help=f"Always use cached copy without conditional headers (If-Modified-Since / ETag). Default is {user_options['NO_CONDITIONAL_CACHE'].value}."
    )

    parser.add_argument(
        f"--{user_options['CHECK_FEEDS'].cli_name}",
        action="store_true",
        default=user_options['CHECK_FEEDS'].value,
        help=f"Perform a quick RSS health check. Default is {user_options['CHECK_FEEDS'].value}."
    )

    parser.add_argument(
        f"--{user_options['PRINT_RSS_PROCESSING_STATUS'].cli_name}",
        action="store_true",
        default=user_options['PRINT_RSS_PROCESSING_STATUS'].value,
        help=f"Print status of RSS processing for each entry. Default is {user_options['PRINT_RSS_PROCESSING_STATUS'].value}."
    )

    parser.add_argument(
        f"--{user_options['SETTINGS_YAML'].cli_name}",
        type=str,
        default=user_options['SETTINGS_YAML'].value,
        help=f"Path to a YAML configuration file. Default is '{user_options['SETTINGS_YAML'].value}'."
    )

    parser.add_argument(
        f"--{user_options['SINGLE_FEED_CHECK'].cli_name}",
        type=validate_feed_url,
        default=user_options['SINGLE_FEED_CHECK'].value,
        metavar="FEED_URL",
        help=(
            "Perform a quick health check for a single RSS feed URL. "
            "Provide the feed URL as argument. Example: "
            "--single-feed-check https://example.com/feed"
        )
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

    print(f"Time range: {start_date_print} {TIMEZONE_PRINT} to {end_date_print} {TIMEZONE_PRINT}")
    print(f"OPML file: {opml_filename}")

    print(f"Retrieved articles: {len(entries)}")
    if print_retrieved_entries:
        grouped_entries = defaultdict(list)
        for entry in entries:
            key = (entry[FEED_TITLE_KEY], entry[FEED_URL_KEY])
            grouped_entries[key].append(entry)

        for (feedtitle, feed_url) in sorted(grouped_entries.keys()):
            articles = grouped_entries[(feedtitle, feed_url)]
            print_feed_details(feedtitle, feed_url, articles)

    print(f"Skipped articles: {len(skipped_entries)}")
    if print_skipped_entries:
        grouped_skipped_entries = defaultdict(list)
        for skipped in skipped_entries:
            key = (skipped[FEED_TITLE_KEY], skipped[FEED_URL_KEY])
            grouped_skipped_entries[key].append(skipped)

        for (feedtitle, feed_url) in sorted(grouped_skipped_entries.keys()):
            articles = grouped_skipped_entries[(feedtitle, feed_url)]
            print_feed_details(feedtitle, feed_url, articles)

    if html_outfilename:
        print(f"HTML written to file: {html_outfilename}")
    if csv_outfilename:
        print(f"CSV written to file: {csv_outfilename}")
    if json_outfilename:
        print(f"json written to file: {json_outfilename}")

    if errors:
        print("Feeds that failed to fetch:")
        for feedtitle, feed_url, exception in errors:
            print(f"\t- {feedtitle}: {feed_url}")

    print(f"Total execution time: {end_time - start_time:.2f} seconds")
    print(f"{FEED_SEPARATOR}")

def run_cyberfeedbites(argv=None, return_raw_json=False):
    try:
        user_options = build_user_options()

        # 1. Parse CLI arguments
        args = parse_arguments(user_options, argv)

        # 2. Determine OPML file and any “check” flags
        check_feeds_flag = getattr(args, "check_feeds", False)
        single_feed_url = getattr(args, "single_feed_check", None)

        if check_feeds_flag:
            opml_file = getattr(args, "opml_filename", user_options["OPML_FILENAME"].value)
            check_rss_health(opml_file)
            return 0

        if single_feed_url:
            check_single_feed(single_feed_url)
            return 0
        
        # 3. Load YAML config
        yaml_path = getattr(args, "settings_yaml", user_options["SETTINGS_YAML"].value)
        yaml_settings = load_yaml_config(yaml_path, user_options)

        # 4. Update user_options from YAML
        for option in user_options.values():
            if not option.cli_only and option.yaml_name in yaml_settings:
                option.set_from_yaml(yaml_settings)

        # 5. Override user_options with CLI arguments if explicitly passed
        cli_args = argv if argv is not None else sys.argv[1:]
        cli_flags = {arg.split("=")[0] for arg in cli_args if arg.startswith("--")}

        for option in user_options.values():
            if not option.yaml_only:
                cli_flag = f"--{option.cli_name}"
                if cli_flag in cli_flags:
                    option.value = getattr(args, option.yaml_name)

        # 6. Print resolved values
        """ for option in user_options.values():
            if option.yaml_only:
                # Print only if YAML actually changed it
                if option.value != option.default:
                    print(f"{option.macro_name}: {option.value}")
            else:
                print(f"{option.macro_name}: {option.value}") """

        # 7. Ensure OUTPUT_FORMAT is lowercased and comma-separated
        output_format_option = user_options['OUTPUT_FORMAT'].value
        if output_format_option:
            user_options['OUTPUT_FORMAT'].value = ",".join(fmt.strip().lower() for fmt in output_format_option.split(","))

        # 7. Run main logic
        return run_main_logic(user_options, return_raw_json)

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return 1

def run_main_logic(user_options, return_raw_json=False):
    try:
        opml_filename = user_options["OPML_FILENAME"].value

        max_length_description = user_options["MAX_LENGTH_DESCRIPTION"].value
        output_format_option = user_options["OUTPUT_FORMAT"].value
        if output_format_option is None:
            output_formats = set()
        else:
            output_formats = {fmt.strip().lower() for fmt in output_format_option.split(",")}

        html_folder = user_options["HTML_REPORT_FOLDER"].value or HTML_REPORT_FOLDER
        csv_folder = user_options["CSV_REPORT_FOLDER"].value or CSV_REPORT_FOLDER
        json_folder = user_options["JSON_REPORT_FOLDER"].value or JSON_REPORT_FOLDER

        aggressive_filtering = user_options["AGGRESSIVE_FILTERING"].value
        aggressive_keywords = []

        if aggressive_filtering:
            aggressive_file = user_options["AGGRESSIVE_KEYWORDS_FILE"].value
            if aggressive_file:
                try:
                    with open(aggressive_file, "r", encoding="utf-8") as f:
                        aggressive_keywords = [line.strip().lower() for line in f if line.strip()]
                except Exception as e:
                    print(f"Error reading aggressive keywords file '{aggressive_file}': {e}")
                    return 1
            else:
                aggressive_keywords = [kw.lower() for kw in CYBERSECURITY_KEYWORDS]

        exclude_keywords = []
        if user_options["EXCLUDE_KEYWORDS"].value:
            exclude_file = user_options["EXCLUDE_KEYWORDS_FILE"].value
            if exclude_file:
                try:
                    with open(exclude_file, "r", encoding="utf-8") as f:
                        exclude_keywords = [line.strip().lower() for line in f if line.strip()]
                except Exception as e:
                    print(f"Error reading exclude keywords file '{exclude_file}': {e}")
                    return 1
            else:
                exclude_keywords = [kw.lower() for kw in EXCLUDE_KEYWORDS]

        print_retrieved_entries = user_options["PRINT_RETRIEVED"].value
        print_skipped_entries = user_options["PRINT_SKIPPED"].value
        order_by = user_options["ORDER_BY"].value
        ignore_cache = user_options["IGNORE_CACHE"].value
        no_conditional_cache = user_options["NO_CONDITIONAL_CACHE"].value
        print_rss_processing_status = user_options["PRINT_RSS_PROCESSING_STATUS"].value

        start_time = time.time()
        current_date = datetime.now(timezone.utc)
        start_date = current_date - timedelta(days=user_options["DEFAULT_START"].value)
        end_date = current_date - timedelta(days=user_options["DEFAULT_END"].value)

        if user_options["ALIGN_START_TO_MIDNIGHT"].value:
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        if user_options["ALIGN_END_TO_MIDNIGHT"].value:
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        current_date_string_filename_suffix = current_date.strftime(TEXT_DATE_FORMAT_FILE)
        start_date_string_print = start_date.strftime(TEXT_DATE_FORMAT_PRINT)
        end_date_string_print = end_date.strftime(TEXT_DATE_FORMAT_PRINT)
        current_date_string_print_json = current_date.strftime(TEXT_DATE_FORMAT_JSON)
        start_date_string_print_json = start_date.strftime(TEXT_DATE_FORMAT_JSON)
        end_date_string_print_json = end_date.strftime(TEXT_DATE_FORMAT_JSON)

        feed_options = FeedOptions(
            start_date=start_date,
            end_date=end_date,
            max_length_description=max_length_description,
            exclude_keywords=exclude_keywords,
            aggressive_keywords=aggressive_keywords,
            ignore_cache=ignore_cache,
            no_conditional_cache=no_conditional_cache,
            print_rss_processing_status = print_rss_processing_status
        )

        all_entries, skipped_entries, icon_map, opml_text, opml_title, opml_category, errors = process_rss_feed(opml_filename, feed_options)

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
            include_images = user_options["HTML_IMG"].value
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
            start_date_print=start_date_string_print,
            end_date_print=end_date_string_print,
            opml_filename=opml_filename,
            entries=all_entries,
            skipped_entries=skipped_entries,
            print_retrieved_entries=print_retrieved_entries,
            print_skipped_entries=print_skipped_entries,
            html_outfilename=html_outfilename,
            csv_outfilename=csv_outfilename,
            json_outfilename=json_outfilename,
            errors=errors,
            start_time=start_time,
            end_time=end_time
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