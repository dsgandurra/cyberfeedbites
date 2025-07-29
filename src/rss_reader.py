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

import xml.etree.ElementTree as ET
import os
from datetime import datetime, timezone
import aiohttp
import asyncio
import feedparser
import ssl
import requests
import re
from asyncio.proactor_events import _ProactorBasePipeTransport

from utils import get_description, clean_articles, format_title_for_print, get_published_date
from config import (
    XMLURL_KEY, UPDATED_PARSED_KEY, FEED_URL_KEY, BODY_KEY, OUTLINE_KEY, 
    TEXT_KEY, TITLE_KEY, LINK_KEY, DESCRIPTION_KEY, PUBLISHED_DATE_KEY, 
    CHANNEL_IMAGE_KEY, ICON_URL_KEY, FEED_TITLE_KEY, IMAGE_KEY, ICON_KEY, 
    LOGO_KEY, HREF_KEY, URL_KEY, CATEGORY_KEY, DEFAULT_REQUEST_HEADERS, 
    HTTP_REQUEST_TIMEOUT, KEYWORD_EXCEPTIONS, SKIPPED_REASON, CYBERSECURITY_KEYWORDS
)

_original_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

def process_rss_feed(opml_filename, start_date, end_date, max_length_description, exclude_keywords, aggressive_keywords):
    """Handles the RSS feed processing asynchronously via run_feeds."""
    try:
        feeds, icon_map, opml_text, opml_title, opml_category = read_opml(opml_filename)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"The OPML file '{opml_filename}' does not exist.") from e
    except ET.ParseError as e:
        msg = f"The OPML file '{opml_filename}' is not well-formed XML: {e}"
        raise ET.ParseError(msg) from e
    except Exception as e:
        raise RuntimeError(f"Error reading OPML file '{opml_filename}': {e}") from e

    sorted_feeds = sorted(feeds, key=lambda feed: feed[0])
    
    # Call async runner
    all_entries, skipped_entries, errors = asyncio.run(
        process_all_feeds (sorted_feeds, start_date, end_date, max_length_description, exclude_keywords, aggressive_keywords)
    )
    
    return all_entries, skipped_entries, icon_map, opml_text, opml_title, opml_category, errors

def _patched_call_connection_lost(self, exc):
    try:
        _original_call_connection_lost(self, exc)
    except OSError:
        # Ignore OSError from shutdown if socket already closed
        pass

_ProactorBasePipeTransport._call_connection_lost = _patched_call_connection_lost

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

def matches_aggressive_keywords(tags, combined_text, aggressive_keywords):
    """
    Returns True if any aggressive keyword is found in tags or combined_text,
    or if aggressive_keywords is empty (no filtering needed).
    """
    if not aggressive_keywords:
        return True

    aggressive_keywords_lower = {kw.lower() for kw in aggressive_keywords}

    # Check tags: any aggressive keyword in any tag's 'term' (case-insensitive)
    if any(
        keyword in tag.get('term', '').lower()
        for tag in tags
        for keyword in aggressive_keywords_lower
    ):
        return True

    # Check combined_text for any aggressive keyword
    combined_text_lower = combined_text.lower()
    if any(keyword in combined_text_lower for keyword in aggressive_keywords_lower):
        return True

    return False

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

def process_feed_entries(feed, feed_url, start_date, end_date, exclude_keywords, aggressive_keywords, max_length_description):
    channel_updated = feed.feed.get(UPDATED_PARSED_KEY)
    if channel_updated:
        channel_updated_date = datetime(*channel_updated[:6], tzinfo=timezone.utc)
        if channel_updated_date < start_date:
            return [], []

    image_info = feed.feed.get(IMAGE_KEY) or feed.feed.get(ICON_KEY) or feed.feed.get(LOGO_KEY) or {}
    channel_image = None
    if isinstance(image_info, dict):
        channel_image = image_info.get(HREF_KEY) or image_info.get(URL_KEY)
    elif isinstance(image_info, str):
        channel_image = image_info

    recent_articles = []
    skipped_articles = []

    for entry in feed.entries:
        published_date = get_published_date(entry, fallback_to_now=False)
        if published_date and start_date <= published_date <= end_date:
            title = entry.get(TITLE_KEY, '')
            link = entry.get(LINK_KEY, '')
            category = entry.get(CATEGORY_KEY, '')
            full_text_description = get_description(entry)
            combined_text = (title + " " + category + " " + full_text_description).lower()
            tags = entry.get('tags', [])
            matched_keyword = matches_exclude_keywords(combined_text, exclude_keywords, KEYWORD_EXCEPTIONS)
            aggressive_keyword = matches_aggressive_keywords(tags, combined_text, aggressive_keywords)

            article_data = {
                FEED_URL_KEY: feed_url,
                TITLE_KEY: title,
                LINK_KEY: link,
                DESCRIPTION_KEY: full_text_description,
                PUBLISHED_DATE_KEY: published_date,
                CHANNEL_IMAGE_KEY: channel_image
            }

            if not aggressive_keyword:
                article_data[SKIPPED_REASON] = f"Not cybersecurity keyword found:"
                skipped_articles.append(article_data)
            elif matched_keyword:
                article_data[SKIPPED_REASON] = f"Matched keyword: {matched_keyword}"
                skipped_articles.append(article_data)
            else:
                recent_articles.append(article_data)

    recent_articles_cleaned = clean_articles(recent_articles, max_length_description)
    skipped_articles_cleaned = clean_articles(skipped_articles, max_length_description)

    return recent_articles_cleaned, skipped_articles_cleaned

def handle_asyncio_exception(loop, context):
    msg = context.get("message", "")
    if "ProactorBasePipeTransport" in msg:
        # Suppress this specific warning
        return
    loop.default_exception_handler(context)

loop = asyncio.get_event_loop()
loop.set_exception_handler(handle_asyncio_exception)

async def fetch_articles_async(session, feed_url, start_date, end_date, max_length_description, exclude_keywords=None, aggressive_keywords=None):
    exclude_keywords = set(k.lower() for k in exclude_keywords or [])
    headers = DEFAULT_REQUEST_HEADERS

    try:
        async with session.get(feed_url, headers=headers) as response:
            response.raise_for_status()
            content = await response.read()
        cleaned_content = clean_feed_content(content)
        feed = feedparser.parse(cleaned_content)
        if feed.bozo:
            raise RuntimeError(f"Feed parsing error: {feed.bozo_exception}")

    except aiohttp.ClientResponseError as e:
        if e.status == 403:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, fetch_articles_sync_fallback, feed_url, start_date, end_date, max_length_description, exclude_keywords, aggressive_keywords)
        else:
            raise RuntimeError(f"Failed to fetch or parse feed {feed_url}: {e}")

    return process_feed_entries(feed, feed_url, start_date, end_date, exclude_keywords, aggressive_keywords, max_length_description)


def fetch_articles_sync_fallback(feed_url, start_date, end_date, max_length_description, exclude_keywords, aggressive_keywords):
    headers = DEFAULT_REQUEST_HEADERS
    timeout = HTTP_REQUEST_TIMEOUT
    exclude_keywords = set(k.lower() for k in exclude_keywords or [])
    aggressive_keywords = set(k.lower() for k in aggressive_keywords or [])

    def try_parse_feed(url):
        feed = feedparser.parse(url)
        if feed.bozo:
            # fallback to requests + cleaning
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            cleaned_content = clean_feed_content(response.content)
            feed = feedparser.parse(cleaned_content)
            if feed.bozo:
                raise RuntimeError(f"Cleaned feed parsing error: {feed.bozo_exception}")
        return feed

    try:
        feed = try_parse_feed(feed_url)
        return process_feed_entries(feed, feed_url, start_date, end_date, exclude_keywords, aggressive_keywords, max_length_description)

    except ssl.SSLError as e:
        if feed_url.startswith("https://"):
            fallback_url = "http://" + feed_url[len("https://"):]
            try:
                feed = try_parse_feed(fallback_url)
                return process_feed_entries(feed, fallback_url, start_date, end_date, exclude_keywords, aggressive_keywords, max_length_description)
            except Exception:
                # final fallback: requests + cleaning on original URL
                try:
                    response = requests.get(feed_url, headers=headers, timeout=timeout)
                    response.raise_for_status()
                    cleaned_content = clean_feed_content(response.content)
                    feed = feedparser.parse(cleaned_content)
                    if feed.bozo:
                        raise RuntimeError(f"Requests fallback feed parsing error: {feed.bozo_exception}")
                    return process_feed_entries(feed, feed_url, start_date, end_date, exclude_keywords, aggressive_keywords, max_length_description)
                except Exception as req_e:
                    raise RuntimeError(f"SSL error on {feed_url}, fallback to {fallback_url} and requests fallback all failed: {e}; {req_e}")
        else:
            raise RuntimeError(f"SSL error while accessing {feed_url}: {e}")

    except Exception as e:
        raise RuntimeError(f"Fallback sync fetch failed for {feed_url}: {e}")


async def process_feed_async(session, feedtitle, feed_url, start_date, end_date, max_length_description, exclude_keywords, aggressive_keywords):
    try:
        recent_articles, skipped_articles = await fetch_articles_async(
            session,
            feed_url,
            start_date,
            end_date,
            max_length_description,
            exclude_keywords,
            aggressive_keywords
        )

        for entry in recent_articles:
            entry[FEED_TITLE_KEY] = feedtitle
            entry[FEED_URL_KEY] = feed_url

        for entry in skipped_articles:
            entry[FEED_TITLE_KEY] = feedtitle
            entry[FEED_URL_KEY] = feed_url

        print(f"Processed {format_title_for_print(feedtitle)} {len(recent_articles)} article{'s' if len(recent_articles) != 1 else ''}")
        return recent_articles, skipped_articles, None

    except ConnectionResetError:
        print(f"Connection reset while processing: {feedtitle} ({feed_url})")
        return [], [], (feedtitle, feed_url, ConnectionResetError("Connection reset"))

    except Exception as e:
        print(f"Error processing: {feedtitle} ({feed_url})")
        return [], [], (feedtitle, feed_url, e)

async def process_all_feeds(feeds, start_date, end_date, max_length_description, exclude_keywords, aggressive_keywords, max_concurrent=10):
    semaphore = asyncio.Semaphore(max_concurrent)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HTTP_REQUEST_TIMEOUT)) as session:

        async def sem_task(feedtitle, feed_url):
            async with semaphore:
                return await process_feed_async(session, feedtitle, feed_url, start_date, end_date, max_length_description, exclude_keywords, aggressive_keywords)

        tasks = [sem_task(title, url) for title, url in feeds]
        results = await asyncio.gather(*tasks)

    all_entries = []
    skipped_entries = []
    errors = []

    for recent, skipped, error in results:
        all_entries.extend(recent)
        skipped_entries.extend(skipped)
        if error is not None:
            errors.append(error)

    return all_entries, skipped_entries, errors