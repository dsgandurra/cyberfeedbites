import os

# Maximum number of threads for concurrent processing
MAX_THREAD_WORKERS = 5

# File paths and template settings
DATA_FOLDER = "data"
TEMPLATE_FOLDER = os.path.join(DATA_FOLDER, "templates")
TEMPLATE_HTML_FILE = os.path.join(TEMPLATE_FOLDER, "template.html")
HTML_REPORT_FOLDER = os.path.join(DATA_FOLDER, "html_reports")
HTML_OUT_FILENAME_PREFIX = "securitynews"
RSS_SOURCES = os.path.join(DATA_FOLDER, "rss_sources")
OPML_FILENAME = os.path.join(RSS_SOURCES, "cybersecnews-sources.opml")

# RSS feed settings
DAYS_BACK = 1
MAX_DAYS_BACK = 7 #limits how many days back to search
FEED_SEPARATOR = "-" * 40

# Keys used in RSS feed entries
FEED_URL_KEY = "feed_url"
TITLE_KEY = "title"
LINK_KEY = "link"
DESCRIPTION_KEY = "description"
PUBLISHED_DATE_KEY = "published_date"

# Maximum length for RSS feed description
MAX_LENGTH_DESCRIPTION = 200

# Format of the date for filename or used as text
TEXT_DATE_FORMAT = "%Y-%m-%d_%H-%M-%S"