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

# Maximum number of threads for concurrent processing
MAX_THREAD_WORKERS = 5

# File paths and template settings
DATA_FOLDER = "data"
TEMPLATE_FOLDER = os.path.join(DATA_FOLDER, "templates")
TEMPLATE_HTML_FILE = os.path.join(TEMPLATE_FOLDER, "template.html")
HTML_REPORT_FOLDER = os.path.join(DATA_FOLDER, "html_reports")
CSV_REPORT_FOLDER = os.path.join(DATA_FOLDER, "csv_reports")
PUBLIC_REPORT_FOLDER = "docs"
PUBLIC_REPORT_INDEX_FILE = "index.html"
PUBLIC_REPORT_CSS_FILE = "style.css"
PUBLIC_REPORT_INDEX_FILE_TITLE = "CyberFeedBites: Daily Cybersecurity News Reports"
PUBLIC_REPORT_INDEX_TEMPLATE="index_template.html"
HTML_OUT_FILENAME_PREFIX = "cybersecuritynews"
RSS_SOURCES = os.path.join(DATA_FOLDER, "rss_sources")
OPML_FILENAME = os.path.join(RSS_SOURCES, "cybersecnews-sources.opml")

# RSS feed settings
DAYS_BACK = 1
MAX_DAYS_BACK = 7 #limits how many days back to search
FEED_SEPARATOR = "-" * 40

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
IMAGE_KEY = "image"
ICON_KEY = "icon"
LOGO_KEY = "logo"
HREF_KEY = "href"
URL_KEY = "url"

# Maximum length for RSS feed description
MAX_LENGTH_DESCRIPTION = 200

# Timezone
TIMEZONE_PRINT = "UTC"

# Format of the date for filename or used as text
TEXT_DATE_FORMAT_FILE = "%Y-%m-%d_%H-%M-%S"
TEXT_DATE_FORMAT_FILE_SHORT = "%Y-%m-%d"
TEXT_DATE_FORMAT_PRINT = "%A, %d %B %Y %H:%M"
TEXT_DATE_FORMAT_PRINT_SHORT = "%d %b %Y %H:%M"