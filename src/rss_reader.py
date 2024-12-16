import ssl
import xml.etree.ElementTree as ET
import os
from datetime import datetime
import feedparser
import threading

from utils import format_description, print_article, print_feed_details
from config import XMLURL_KEY, PUBLISHED_PARSED_KEY, UPDATED_PARSED_KEY, FEED_URL_KEY, TITLE_KEY, LINK_KEY, DESCRIPTION_KEY, PUBLISHED_DATE_KEY

# Read OPML and extract feed URLs
def read_opml(file_path):
    """Reads OPML file and extracts feed URLs."""
    # Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The OPML file at {file_path} does not exist.")
    
    # Parse the OPML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    feeds = []
    for outline in root.findall('.//outline[@xmlUrl]'):
        feeds.append((outline.attrib[TITLE_KEY], outline.attrib[XMLURL_KEY]))
    
    return feeds

# Fetch articles from RSS feed
def fetch_recent_articles(feed_url, earliest_time):
    """Fetches articles from an RSS feed."""
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context

    feed = feedparser.parse(feed_url)
    recent_articles = []

    for entry in feed.entries:
        published = entry.get(PUBLISHED_PARSED_KEY) or entry.get(UPDATED_PARSED_KEY)

        if published:
            published_date = datetime(*published[:6])
            if earliest_time < published_date:
                truncated_plain_text_description = format_description(entry)
                recent_articles.append((entry.title, entry.link, truncated_plain_text_description, published_date))

    return recent_articles

# Filter and process articles to match time range
def check_recent_articles(feed_url, recent_articles, earliest_time, lock):
    """Filters and checks if articles are within the allowed time range."""
    entries = []

    for title, link, description, published_date in recent_articles:
        entry = {
            FEED_URL_KEY: feed_url,
            TITLE_KEY: title,
            LINK_KEY: link,
            DESCRIPTION_KEY: description,
            PUBLISHED_DATE_KEY: published_date
        }

        if earliest_time < published_date:
            print_article(title, description, link, published_date, lock)
        entries.append(entry)

    return entries

# Process individual RSS feed
def process_feed(feedtitle, feed_url, earliest_time, lock, all_entries_queue):
    """Processes a single feed, fetches and checks recent articles."""
    try:
        recent_articles = fetch_recent_articles(feed_url, earliest_time)
        if recent_articles:
            print_feed_details(feedtitle, feed_url, lock)
            entries = check_recent_articles(feed_url, recent_articles, earliest_time, lock)
            for entry in entries:
                all_entries_queue.put(entry)
            return entries
        else:
            print_feed_details(feedtitle, feed_url, lock)
            return []
    except Exception as e:
        print(f"Failed to fetch feed: {e}, {feed_url}")
        return []
