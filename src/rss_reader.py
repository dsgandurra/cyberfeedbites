import ssl
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timedelta, timezone
import feedparser
import threading

from utils import format_description, print_article, print_feed_details
from config import XMLURL_KEY, PUBLISHED_PARSED_KEY, UPDATED_PARSED_KEY, FEED_URL_KEY, BODY_KEY, OUTLINE_KEY, TEXT_KEY, TITLE_KEY, LINK_KEY, DESCRIPTION_KEY, PUBLISHED_DATE_KEY, CHANNEL_IMAGE_KEY, ICON_URL_KEY, FEED_TITLE_KEY

# Read OPML and extract feed URLs
def read_opml(file_path):
    """Reads OPML file and extracts feed URLs and icons."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The OPML file at {file_path} does not exist.")
    
    tree = ET.parse(file_path)
    root = tree.getroot()

    body = root.find(BODY_KEY)
    top_outline = body.find(OUTLINE_KEY) if body is not None else None
    top_text = top_outline.attrib.get(TEXT_KEY) if top_outline is not None else None
    top_title = top_outline.attrib.get(TITLE_KEY) if top_outline is not None else None
    
    feeds = []
    icon_map = {}
    
    for outline in root.findall('.//outline[@xmlUrl]'):
        title = outline.attrib.get(TITLE_KEY)
        url = outline.attrib.get(XMLURL_KEY)
        icon = outline.attrib.get(ICON_URL_KEY)
        feeds.append((title, url))
        
        if title and icon:
            icon_map[title] = icon
    
    return feeds, icon_map, top_text, top_title

# Fetch articles from RSS feed
def fetch_recent_articles(feed_url, earliest_date):
    """Fetches articles from an RSS feed."""
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context

    feed = feedparser.parse(feed_url)

    channel_updated = feed.feed.get(UPDATED_PARSED_KEY)
    if channel_updated:
        channel_updated_date = datetime(*channel_updated[:6], tzinfo=timezone.utc)
        if channel_updated_date <= earliest_date:
            return []
    
    image_info = feed.feed.get('image') or feed.feed.get('icon') or feed.feed.get('logo') or {}
    channel_image = None

    if isinstance(image_info, dict):
        channel_image = image_info.get('href') or image_info.get('url')
    elif isinstance(image_info, str):
        channel_image = image_info

    recent_articles = []

    for entry in feed.entries:
        published = entry.get(PUBLISHED_PARSED_KEY) or entry.get(UPDATED_PARSED_KEY)

        if published:
            published_date = datetime(*published[:6], tzinfo=timezone.utc)
            if earliest_date < published_date:
                truncated_plain_text_description = format_description(entry)
                recent_articles.append((entry.title, entry.link, truncated_plain_text_description, published_date))

    entries = []

    for title, link, description, published_date in recent_articles:
        entry = {
            FEED_URL_KEY: feed_url,
            TITLE_KEY: title,
            LINK_KEY: link,
            DESCRIPTION_KEY: description,
            PUBLISHED_DATE_KEY: published_date,
            CHANNEL_IMAGE_KEY : channel_image
        }
        entries.append(entry)
        
    return entries

# Process individual RSS feed sources
def process_feed(feedtitle, feed_url, earliest_date, lock, all_entries_queue):
    """Processes a feed source, and fetches and checks all its recent articles."""
    try:
        recent_articles = fetch_recent_articles(feed_url, earliest_date)
        if recent_articles:
            print_feed_details(feedtitle, feed_url, recent_articles, lock)
            for entry in recent_articles:
                entry[FEED_TITLE_KEY] = feedtitle 
                all_entries_queue.put(entry)
            return recent_articles
        else:
            print_feed_details(feedtitle, feed_url, recent_articles, lock)
            return []
    except Exception as e:
        print(f"Failed to fetch feed: {e}, {feed_url}")
        return []