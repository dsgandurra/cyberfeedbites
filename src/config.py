import os

# Maximum number of threads for concurrent processing
MAX_THREAD_WORKERS = 5

# File paths and template settings
DATA_FOLDER = "data"
TEMPLATE_FOLDER = os.path.join(DATA_FOLDER, "templates")
TEMPLATE_HTML_FILE = os.path.join(TEMPLATE_FOLDER, "template.html")
HTML_REPORT_FOLDER = os.path.join(DATA_FOLDER, "html_reports")
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

# Maximum length for RSS feed description
MAX_LENGTH_DESCRIPTION = 200

# Timezone
TIMEZONE_PRINT = "UTC"

# Format of the date for filename or used as text
TEXT_DATE_FORMAT_FILE = "%Y-%m-%d_%H-%M-%S"
TEXT_DATE_FORMAT_PRINT = "%A, %d %B %Y %H:%M"