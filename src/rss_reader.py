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

import ssl
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timezone
import feedparser
import traceback

from utils import format_description, print_article, print_feed_details
from config import (
    XMLURL_KEY, PUBLISHED_PARSED_KEY, UPDATED_PARSED_KEY, FEED_URL_KEY,
    BODY_KEY, OUTLINE_KEY, TEXT_KEY, TITLE_KEY, LINK_KEY, DESCRIPTION_KEY,
    PUBLISHED_DATE_KEY, CHANNEL_IMAGE_KEY, ICON_URL_KEY, FEED_TITLE_KEY, 
    IMAGE_KEY, ICON_KEY, LOGO_KEY, HREF_KEY, URL_KEY
)

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
        text = outline.attrib.get(TEXT_KEY)
        url = outline.attrib.get(XMLURL_KEY)
        icon = outline.attrib.get(ICON_URL_KEY)
        feeds.append((text, url))
        
        if text and icon:
            icon_map[text] = icon
    
    return feeds, icon_map, top_text, top_title


def fetch_recent_articles(feed_url, earliest_date):
    """Fetches articles from an RSS feed from the earliest date."""
    try:
        feed = feedparser.parse(feed_url)
        # 'bozo' is True if the feed is malformed or could not be parsed correctly (e.g., network or XML errors)
        if feed.bozo:
            raise RuntimeError(f"Feed parsing error: {feed.bozo_exception}")
    except ssl.SSLError as e:
        if feed_url.startswith("https://"):
            fallback_url = "http://" + feed_url[len("https://"):]
            try:
                feed = feedparser.parse(fallback_url)
                if feed.bozo:
                    raise RuntimeError(f"Fallback feed parsing error: {feed.bozo_exception}")
                feed_url = fallback_url
            except Exception:
                raise RuntimeError(f"SSL error on {feed_url} and fallback to {fallback_url} also failed: {e}")
        else:
            raise RuntimeError(f"SSL error while accessing {feed_url}: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch feed {feed_url}: {e}")
    
    channel_updated = feed.feed.get(UPDATED_PARSED_KEY)
    if channel_updated:
        channel_updated_date = datetime(*channel_updated[:6], tzinfo=timezone.utc)
        if channel_updated_date <= earliest_date:
            return []
    
    image_info = feed.feed.get(IMAGE_KEY) or feed.feed.get(ICON_KEY) or feed.feed.get(LOGO_KEY) or {}
    channel_image = None

    if isinstance(image_info, dict):
        channel_image = image_info.get(HREF_KEY) or image_info.get(URL_KEY)
    elif isinstance(image_info, str):
        channel_image = image_info

    recent_articles = []

    for entry in feed.entries:
        published = entry.get(PUBLISHED_PARSED_KEY) or entry.get(UPDATED_PARSED_KEY)
        if published:
            published_date = datetime(*published[:6], tzinfo=timezone.utc)
            if earliest_date < published_date:
                title = entry.get('title', 'No title')
                link = entry.get('link', '')
                truncated_plain_text_description = format_description(entry)
                recent_articles.append((title, link, truncated_plain_text_description, published_date))

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

def process_feed(feedtitle, feed_url, earliest_date, lock, all_entries_queue):
    """Processes a feed source and fetches its recent articles."""
    try:
        recent_articles = fetch_recent_articles(feed_url, earliest_date)
        print_feed_details(feedtitle, feed_url, recent_articles, lock)
        if recent_articles:
            for entry in recent_articles:
                entry[FEED_TITLE_KEY] = feedtitle 
                all_entries_queue.put(entry)
        return recent_articles or [], None
    except Exception as e:
        print_feed_details(feedtitle, feed_url, [], lock)  # lock acquired internally
        with lock:
            print(f"\nFailed to fetch feed: {feedtitle} ({feed_url})")
            print(f"Error: {e}")
        return [], (feedtitle, feed_url)