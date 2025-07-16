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

import html
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from config import (
    FEED_SEPARATOR, SUMMARY_KEY, TITLE_KEY, LINK_KEY, 
    DESCRIPTION_KEY, PUBLISHED_DATE_KEY, SKIPPED_REASON, 
    CONTENT_KEY
)

def html_to_plain_text(html_str):
    """Converts HTML to plain text using BeautifulSoup."""
    try:
        soup = BeautifulSoup(html_str, 'html.parser')
        return soup.get_text()
    except Exception as e:
        print(f"Error converting HTML to plain text: {e}")
        return ""

def truncate_string(text, max_length):
    """Truncates the string to a maximum length."""
    if len(text) > max_length:
        return text[:max_length].rsplit(' ', 1)[0] + "..."
    return text

def get_description(entry):
    """
    Returns the plain description.
    Falls back to summary if description is missing,
    and finally extracts plain text from HTML content if both are unavailable.
    """
    description = entry.get(DESCRIPTION_KEY) or entry.get(SUMMARY_KEY)

    if not description:
        content = entry.get(CONTENT_KEY)
        if isinstance(content, list) and content:
            content = content[0].get('value', '')
        description = content or ""

    plain_text = html_to_plain_text(description).strip().replace('\n', ' ')

    return plain_text

def truncate_description(plain_text_description, max_length_description):
    """Formats the description of the RSS entry."""
    truncated_plain_text_description = ""
           
    if plain_text_description:
        truncated_plain_text_description = truncate_string(plain_text_description, max_length_description)
        
    return truncated_plain_text_description

def sanitize_for_html(text):
    """Escapes text for safe HTML display and preserves line breaks."""
    text = html.escape(text)
    text = text.replace('\n', '<br>').replace('\r', '')
    return text

def sanitize_for_csv(text):
    """Escapes text for CSV output by enclosing in quotes if needed."""
    if any(char in text for char in [',', '"', '\n']):
        text = '"' + text.replace('"', '""') + '"'
    return text

def get_website_name(url):
    """Extracts the website name from a URL."""
    try:
        parsed_url = urlparse(url)
        return parsed_url.netloc
    except Exception as e:
        print(f"Error parsing URL {url}: {e}")
        return "Unknown"

def print_feed_details(feedtitle, feed_url, recent_articles, skipped_articles, lock):
    """Helper function to print feed details."""
    with lock:
        print(f"\n{FEED_SEPARATOR}")
        print(f"[{feedtitle}] [{feed_url}]")
        if recent_articles:
            print(f"{FEED_SEPARATOR}")
            for article in recent_articles:
                print_article(article)

        if skipped_articles:
            print(f"\n")
            for skipped_article in skipped_articles:
                print_skipped_article(skipped_article)
        print(f"{FEED_SEPARATOR}")


def print_article(entry):
    """Helper function to print article details."""
    print(f"\t[{entry[TITLE_KEY]}] [{entry[DESCRIPTION_KEY]}] [{entry[LINK_KEY]}] [{entry[PUBLISHED_DATE_KEY]}]")

def print_skipped_article(entry):
    """Helper function to print skipped article details."""
    print(f"\t***Skipped entry due to {entry[SKIPPED_REASON]}: [{entry[TITLE_KEY]}] [{entry[TITLE_KEY]}] [{entry[DESCRIPTION_KEY]}] [{entry[LINK_KEY]}] [{entry[PUBLISHED_DATE_KEY]}]")