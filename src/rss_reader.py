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
import requests
import re

from utils import get_description, truncate_description, print_feed_details
from config import (
    XMLURL_KEY, PUBLISHED_PARSED_KEY, UPDATED_PARSED_KEY, FEED_URL_KEY,
    BODY_KEY, OUTLINE_KEY, TEXT_KEY, TITLE_KEY, LINK_KEY, DESCRIPTION_KEY,
    PUBLISHED_DATE_KEY, CHANNEL_IMAGE_KEY, ICON_URL_KEY, FEED_TITLE_KEY, 
    IMAGE_KEY, ICON_KEY, LOGO_KEY, HREF_KEY, URL_KEY, CATEGORY_KEY,
    DEFAULT_REQUEST_HEADERS, HTTP_REQUEST_TIMEOUT, KEYWORD_EXCEPTIONS,
    SKIPPED_REASON
)

def read_opml(file_path):
    """Reads OPML file and extracts feed URLs and icons."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The OPML file at {file_path} does not exist.")
    
    tree = ET.parse(file_path)
    root = tree.getroot()

    body = root.find(BODY_KEY)
    top_outline = body.find(OUTLINE_KEY) if body is not None else None
    opml_text = top_outline.attrib.get(TEXT_KEY) if top_outline is not None else None
    opml_title = top_outline.attrib.get(TITLE_KEY) if top_outline is not None else None
    opml_category = top_outline.attrib.get(CATEGORY_KEY) if top_outline is not None else None
    
    feeds = []
    icon_map = {}
    
    for outline in root.findall('.//outline[@xmlUrl]'):
        text = outline.attrib.get(TEXT_KEY)
        url = outline.attrib.get(XMLURL_KEY)
        icon = outline.attrib.get(ICON_URL_KEY)
        feeds.append((text, url))
        
        if text and icon:
            icon_map[text] = icon
    
    return feeds, icon_map, opml_text, opml_title, opml_category

def clean_feed_content(content):
    text = content.decode('utf-8', errors='ignore')
    
    # Replace tabs with spaces (to avoid hidden tab issues)
    text = text.replace('\t', ' ')
    
    # Remove ASCII control characters except \n and \r (valid in XML)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', text)
    
    # Remove illegal unicode characters in XML 1.0
    text = re.sub(r'[\uFFFE\uFFFF\uD800-\uDFFF]', '', text)
    
    # Replace bare & not followed by valid entities with &amp;
    text = re.sub(r'&(?!amp;|lt;|gt;|apos;|quot;)', '&amp;', text)
    
    # Optionally normalise line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    return text.encode('utf-8')

def matches_exclude_keywords(text: str, exclude_keywords: set[str], exceptions: dict[str, list[str]] = None) -> str | None:
    """
    Returns the first matched keyword from exclude_keywords in text,
    considering exceptions (words or phrases that override exclusion).
    If no keyword matches, returns None.
    
    exceptions format: {keyword: [list of exception substrings]}
    e.g. {'sponsored': ['state-sponsored', 'self-sponsored']}
    """
    text_lower = text.lower()
    exceptions = exceptions or {}

    for keyword in exclude_keywords:
        if keyword in text_lower:
            # Check exceptions for this keyword
            exception_phrases = exceptions.get(keyword, [])
            if any(exc in text_lower for exc in exception_phrases):
                continue  # exception matched, skip exclusion for this keyword
            return keyword
    return None

def fetch_articles(feed_url, start_date, end_date, max_length_description, exclude_keywords=None):
    """Fetches articles from an RSS feed in the given time range."""
    headers = DEFAULT_REQUEST_HEADERS
    timeout = HTTP_REQUEST_TIMEOUT
    exclude_keywords = set(k.lower() for k in exclude_keywords or [])
    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            # fallback to requests + cleaning
            response = requests.get(feed_url, headers=headers, timeout=timeout)
            response.raise_for_status()
            cleaned_content = clean_feed_content(response.content)
            feed = feedparser.parse(cleaned_content)
            if feed.bozo:
                raise RuntimeError(f"Cleaned feed parsing error: {feed.bozo_exception}")

    except ssl.SSLError as e:
        if feed_url.startswith("https://"):
            fallback_url = "http://" + feed_url[len("https://"):]
            try:
                feed = feedparser.parse(fallback_url)
                if feed.bozo:
                    # fallback to requests + cleaning on fallback URL
                    response = requests.get(fallback_url, headers=headers, timeout=timeout)
                    response.raise_for_status()
                    cleaned_content = clean_feed_content(response.content)
                    feed = feedparser.parse(cleaned_content)
                    if feed.bozo:
                        raise RuntimeError(f"Fallback cleaned feed parsing error: {feed.bozo_exception}")
                feed_url = fallback_url
            except Exception:
                # final fallback: requests + cleaning on original URL
                try:
                    response = requests.get(feed_url, headers=headers, timeout=timeout)
                    response.raise_for_status()
                    cleaned_content = clean_feed_content(response.content)
                    feed = feedparser.parse(cleaned_content)
                    if feed.bozo:
                        raise RuntimeError(f"Requests fallback feed parsing error: {feed.bozo_exception}")
                except Exception as req_e:
                    raise RuntimeError(f"SSL error on {feed_url}, fallback to {fallback_url} and requests fallback all failed: {e}; {req_e}")
        else:
            raise RuntimeError(f"SSL error while accessing {feed_url}: {e}")

    except Exception as e:
        raise RuntimeError(f"Failed to fetch feed {feed_url}: {e}")

    channel_updated = feed.feed.get(UPDATED_PARSED_KEY)
    if channel_updated:
        channel_updated_date = datetime(*channel_updated[:6], tzinfo=timezone.utc)
        if channel_updated_date < start_date:
            return [], []  # No new updates since start_date, skip entries

    image_info = feed.feed.get(IMAGE_KEY) or feed.feed.get(ICON_KEY) or feed.feed.get(LOGO_KEY) or {}
    channel_image = None

    if isinstance(image_info, dict):
        channel_image = image_info.get(HREF_KEY) or image_info.get(URL_KEY)
    elif isinstance(image_info, str):
        channel_image = image_info

    recent_articles = []
    skipped_articles = []

    for entry in feed.entries:
        published = entry.get(PUBLISHED_PARSED_KEY) or entry.get(UPDATED_PARSED_KEY)
        if published:
            published_date = datetime(*published[:6], tzinfo=timezone.utc)
            if start_date <= published_date <= end_date:
                title = entry.get('title', 'No title')
                link = entry.get('link', '')
                full_text_description = get_description(entry)
                truncated_plain_text_description = truncate_description(full_text_description, max_length_description)
                combined_text = (title + " " + full_text_description).lower()
                matched_keyword = matches_exclude_keywords(combined_text, exclude_keywords, KEYWORD_EXCEPTIONS)
                skipped_reason = f"Matched keyword: {matched_keyword}"
                if matched_keyword:
                    skipped_articles.append((title, link, truncated_plain_text_description, published_date, skipped_reason))
                else:
                    recent_articles.append((title, link, truncated_plain_text_description, published_date))

    entries = []

    for title, link, description, published_date in recent_articles:
        entry = {
            FEED_URL_KEY: feed_url,
            TITLE_KEY: title.strip(),
            LINK_KEY: link,
            DESCRIPTION_KEY: description.strip(),
            PUBLISHED_DATE_KEY: published_date,
            CHANNEL_IMAGE_KEY: channel_image
        }
        entries.append(entry)

    skipped_entries = []

    for title, link, description, published_date, skipped_reason in skipped_articles:
        skipped_entry = {
            FEED_URL_KEY: feed_url,
            TITLE_KEY: title.strip(),
            LINK_KEY: link,
            DESCRIPTION_KEY: description.strip(),
            PUBLISHED_DATE_KEY: published_date,
            CHANNEL_IMAGE_KEY: channel_image,
            SKIPPED_REASON: skipped_reason
        }
        skipped_entries.append(skipped_entry)

    return entries, skipped_entries

def process_feed(feedtitle, feed_url, start_date, end_date, max_length_description, lock, all_entries_queue, skipped_entries_queue, exclude_keywords):
    """Processes a feed source and fetches its recent articles."""
    try:
        recent_articles, skipped_articles = fetch_articles(feed_url, start_date, end_date, max_length_description, exclude_keywords)
        print_feed_details(feedtitle, feed_url, recent_articles, skipped_articles, lock)
        if recent_articles:
            for entry in recent_articles:
                entry[FEED_TITLE_KEY] = feedtitle 
                all_entries_queue.put(entry)
        if skipped_articles:
            for skipped_entry in skipped_articles:
                skipped_entry[FEED_TITLE_KEY] = feedtitle
                skipped_entries_queue.put(skipped_entry)
        return recent_articles, skipped_articles or [], None
    except Exception as e:
        print_feed_details(feedtitle, feed_url, [], [], lock)  # lock acquired internally
        with lock:
            print(f"\nFailed to fetch feed: {feedtitle} ({feed_url})")
            print(f"Error: {e}")
        return [], (feedtitle, feed_url)