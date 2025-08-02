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
RSS_SOURCES = os.path.join(DATA_FOLDER, "rss_sources")
OPML_FILENAME = os.path.join(RSS_SOURCES, "cybersecnews-sources.opml")

TEMPLATE_HTML_FILE = os.path.abspath(TEMPLATE_HTML_FILE)
HTML_REPORT_FOLDER = os.path.abspath(HTML_REPORT_FOLDER)
CSV_REPORT_FOLDER = os.path.abspath(CSV_REPORT_FOLDER)
JSON_REPORT_FOLDER = os.path.abspath(JSON_REPORT_FOLDER)
OPML_FILENAME = os.path.abspath(OPML_FILENAME)

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