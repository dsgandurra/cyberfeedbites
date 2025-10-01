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

# File paths and template settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # base path
DATA_FOLDER = os.path.join(BASE_DIR, "..", "data")

TEMPLATE_FOLDER = os.path.join(DATA_FOLDER, "templates")
TEMPLATE_HTML_FILE = os.path.join(TEMPLATE_FOLDER, "template.html")
HTML_REPORT_FOLDER = os.path.join(DATA_FOLDER, "html_reports")
CSV_REPORT_FOLDER = os.path.join(DATA_FOLDER, "csv_reports")
JSON_REPORT_FOLDER = os.path.join(DATA_FOLDER, "json_reports")
CONFIG_FOLDER = os.path.join(DATA_FOLDER, "config")
SETTINGS_YAML = os.path.join(CONFIG_FOLDER, "settings.yaml")
RSS_SOURCES = os.path.join(DATA_FOLDER, "rss_sources")
OPML_FILENAME = os.path.join(RSS_SOURCES, "cybersecnews-sources.opml")
CACHE_FOLDER = os.path.join(DATA_FOLDER, "cache")

TEMPLATE_HTML_FILE = os.path.abspath(TEMPLATE_HTML_FILE)
HTML_REPORT_FOLDER = os.path.abspath(HTML_REPORT_FOLDER)
CSV_REPORT_FOLDER = os.path.abspath(CSV_REPORT_FOLDER)
JSON_REPORT_FOLDER = os.path.abspath(JSON_REPORT_FOLDER)
OPML_FILENAME = os.path.abspath(OPML_FILENAME)
SETTINGS_YAML = os.path.abspath(SETTINGS_YAML)

# Default start and end offsets (in days) relative to today
DEFAULT_START = 1
DEFAULT_END = 0  # 0 means today
# Limits how many days back to search
MAX_DAYS_BACK = 7
# Limits how many days back to start the search
MAX_START_DAYS = 31
# Limits how many days back to end the search
MAX_END_DAYS = 31
# Maximum length for RSS feed description
MAX_LENGTH_DESCRIPTION = 200
MAX_ALLOWED_LENGTH_DESCRIPTION = 1000
MAX_LENGTH_FEED_URL = 200
MAX_LENGTH_TITLE = 100
MAX_LENGTH_LINK = 200
MAX_LENGTH_CHANNEL_IMAGE = 200
MAX_LENGTH_SKIPPED_REASON = 500
FEED_SEPARATOR = "-" * 40
MAX_FEEDTITLE_LEN_PRINT = 40
MAX_CONCURRENT_TASKS = 15
CACHE_MAX_AGE_SECONDS = 600  # 10 minutes
STALE_DAYS_THRESHOLD = 30
PRINT_RSS_PROCESSING_STATUS = False
SINGLE_FEED_CHECK = None

DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Connection': 'keep-alive',
    'Referer': 'https://www.google.com',
}
HTTP_REQUEST_TIMEOUT = 10  # seconds

EXCLUDE_KEYWORDS = [
    'sponsored',
    'advertisement',
    'giveaway',
    'clickbait',
    'advertorial',
    'paid content'
]

KEYWORD_EXCEPTIONS = {
    'sponsored': ['state-sponsored']
}

CYBERSECURITY_KEYWORDS = {
    'security'
}

#default options for args
PRINT_RETRIEVED = False
PRINT_SKIPPED = False
CHECK_FEEDS = False
ORDER_BY = "date"
OUTPUT_FORMAT = "html"
ALIGN_START_TO_MIDNIGHT = False
ALIGN_END_TO_MIDNIGHT = False
EXCLUDE_KEYWORDS = False
EXCLUDE_KEYWORDS_FILE = None
AGGRESSIVE_FILTERING = False
AGGRESSIVE_KEYWORDS_FILE = None
HTML_IMG = False
IGNORE_CACHE = False
NO_CONDITIONAL_CACHE = True

# Keys used in RSS feed entries
SUMMARY_KEY = "summary"
PUBLISHED_PARSED_KEY = "published_parsed"
UPDATED_PARSED_KEY = "updated_parsed"
FEED_URL_KEY = "feed_url"
XMLURL_KEY = "xmlUrl"
TITLE_KEY = "title"
BODY_KEY = "body"
OUTLINE_KEY = "outline"
TEXT_KEY = "text"
FEED_TITLE_KEY = "feed_title"
ICON_URL_KEY = "iconUrl"
LINK_KEY = "link"
DESCRIPTION_KEY = "description"
PUBLISHED_DATE_KEY = "published_date"
CHANNEL_IMAGE_KEY = "channel_image"
SKIPPED_REASON = "skipped_reason"
IMAGE_KEY = "image"
ICON_KEY = "icon"
LOGO_KEY = "logo"
HREF_KEY = "href"
URL_KEY = "url"
CATEGORY_KEY = "category"
CONTENT_KEY = "content"

# Timezone
TIMEZONE_PRINT = "UTC"

# Format of the date for filename or used as text
TEXT_DATE_FORMAT_FILE = "%Y-%m-%d_%H-%M-%S"
TEXT_DATE_FORMAT_JSON = "%Y-%m-%d %H:%M:%S"
TEXT_DATE_FORMAT_FILE_SHORT = "%Y-%m-%d"
TEXT_DATE_FORMAT_PRINT = "%A, %d %B %Y %H:%M"
TEXT_DATE_FORMAT_PRINT_SHORT = "%d %b %Y %H:%M"

class UserOption:
    def __init__(self, macro_name, default, yaml_name, cli_name, cli_only=False, yaml_only=False):
        self.macro_name = macro_name      # e.g., OUTPUT_HTML_FOLDER
        self.default = default            # original default
        self.value = default              # current active value
        self.yaml_name = yaml_name        # key in YAML
        self.cli_name = cli_name          # CLI argument name
        self.cli_only = cli_only          # True → never load from YAML
        self.yaml_only = yaml_only        # True → never exposed as CLI

    def set_from_yaml(self, yaml_dict):
        if not self.cli_only and self.yaml_name in yaml_dict:
            self.value = yaml_dict[self.yaml_name]

    def reset(self):
        self.value = self.default


def build_user_options():
    """Return a fresh dictionary of all configurable UserOption objects."""
    # Each UserOption contains:
    #   - macro_name: the internal constant/macro name used in code (e.g., OUTPUT_HTML_FOLDER)
    #   - value: the current active value (default unless overridden by YAML or CLI)
    #   - yaml_name: the key used in YAML configuration files
    #   - cli_name: the command-line flag name used when running the program (e.g., --output-html-folder)

    return {
        "DEFAULT_START": UserOption("DEFAULT_START", DEFAULT_START, "start", "start"),
        "DEFAULT_END": UserOption("DEFAULT_END", DEFAULT_END, "end", "end"),
        "OPML_FILENAME": UserOption("OPML_FILENAME", OPML_FILENAME, "opml_filename", "opml-filename"),
        "OUTPUT_FORMAT": UserOption("OUTPUT_FORMAT", OUTPUT_FORMAT, "output_format", "output-format"),
        "HTML_REPORT_FOLDER": UserOption("HTML_REPORT_FOLDER", HTML_REPORT_FOLDER, "output_html_folder", "output-html-folder"),
        "CSV_REPORT_FOLDER": UserOption("CSV_REPORT_FOLDER", CSV_REPORT_FOLDER, "output_csv_folder", "output-csv-folder"),
        "JSON_REPORT_FOLDER": UserOption("JSON_REPORT_FOLDER", JSON_REPORT_FOLDER, "output_json_folder", "output-json-folder"),
        "ALIGN_START_TO_MIDNIGHT": UserOption("ALIGN_START_TO_MIDNIGHT", ALIGN_START_TO_MIDNIGHT, "align_start_to_midnight", "align-start-to-midnight"),
        "ALIGN_END_TO_MIDNIGHT": UserOption("ALIGN_END_TO_MIDNIGHT", ALIGN_END_TO_MIDNIGHT, "align_end_to_midnight", "align-end-to-midnight"),
        "HTML_IMG": UserOption("HTML_IMG", HTML_IMG, "html_img", "html-img"),
        "MAX_LENGTH_DESCRIPTION": UserOption("MAX_LENGTH_DESCRIPTION", MAX_LENGTH_DESCRIPTION, "max_length_description", "max-length-description"),
        "EXCLUDE_KEYWORDS": UserOption("EXCLUDE_KEYWORDS", EXCLUDE_KEYWORDS, "exclude_keywords", "exclude-keywords"),
        "EXCLUDE_KEYWORDS_FILE": UserOption("EXCLUDE_KEYWORDS_FILE", EXCLUDE_KEYWORDS_FILE, "exclude_keywords_file", "exclude-keywords-file"),
        "AGGRESSIVE_FILTERING": UserOption("AGGRESSIVE_FILTERING", AGGRESSIVE_FILTERING, "aggressive_filtering", "aggressive-filtering"),
        "AGGRESSIVE_KEYWORDS_FILE": UserOption("AGGRESSIVE_KEYWORDS_FILE", AGGRESSIVE_KEYWORDS_FILE, "aggressive_keywords_file", "aggressive-keywords-file"),
        "PRINT_RETRIEVED": UserOption("PRINT_RETRIEVED", PRINT_RETRIEVED, "print_retrieved", "print-retrieved"),
        "PRINT_SKIPPED": UserOption("PRINT_SKIPPED", PRINT_SKIPPED, "print_skipped", "print-skipped"),
        "ORDER_BY": UserOption("ORDER_BY", ORDER_BY, "order_by", "order-by"),
        "IGNORE_CACHE": UserOption("IGNORE_CACHE", IGNORE_CACHE, "ignore_cache", "ignore-cache"),
        "NO_CONDITIONAL_CACHE": UserOption("NO_CONDITIONAL_CACHE", NO_CONDITIONAL_CACHE, "no_conditional_cache", "no-conditional-cache"),
        "CHECK_FEEDS": UserOption("CHECK_FEEDS", CHECK_FEEDS, "check_feeds", "check-feeds", cli_only=True),
        "PRINT_RSS_PROCESSING_STATUS": UserOption("PRINT_RSS_PROCESSING_STATUS", PRINT_RSS_PROCESSING_STATUS, "print_rss_processing_status", "print-rss-processing-status"),
        "SINGLE_FEED_CHECK": UserOption("SINGLE_FEED_CHECK", SINGLE_FEED_CHECK, "single_feed_check", "single-feed-check", cli_only=True),
        "SETTINGS_YAML": UserOption("SETTINGS_YAML", SETTINGS_YAML, "settings_yaml", "settings-yaml", cli_only=True),
        "MAX_CONCURRENT_TASKS": UserOption("MAX_CONCURRENT_TASKS", MAX_CONCURRENT_TASKS, "max_concurrent_tasks", None, yaml_only=True)
    }