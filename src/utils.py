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
from datetime import datetime, timezone
import re
import tldextract
import os
from typing import Any, Dict, Optional
import yaml

from .config import (
    FEED_SEPARATOR, SUMMARY_KEY, TITLE_KEY, LINK_KEY, FEED_URL_KEY, CHANNEL_IMAGE_KEY,
    DESCRIPTION_KEY, PUBLISHED_DATE_KEY, SKIPPED_REASON, MAX_FEEDTITLE_LEN_PRINT,
    CONTENT_KEY, MAX_LENGTH_TITLE, MAX_LENGTH_LINK, MAX_LENGTH_FEED_URL, 
    MAX_LENGTH_SKIPPED_REASON, PUBLISHED_PARSED_KEY, UPDATED_PARSED_KEY, MAX_LENGTH_CHANNEL_IMAGE
)

def get_published_date(entry, fallback_to_now=False):
    parsed = entry.get(PUBLISHED_PARSED_KEY) or entry.get(UPDATED_PARSED_KEY)
    if parsed:
        try:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass
    if fallback_to_now:
        return datetime.now(timezone.utc)
    return None


def html_to_plain_text(html_str):
    """Converts HTML to plain text using BeautifulSoup, only if input looks like HTML."""
    try:
        if not re.search(r'<[^>]+>', html_str):
            return html_str
        soup = BeautifulSoup(html_str, 'html.parser')
        return soup.get_text()
    except Exception as e:
        print(f"Error converting HTML to plain text: {e}")
        return ""

def truncate_string(text, max_length):
    if text is None:
        print("Error: 'text' is None in truncate_string()")

    if not isinstance(text, str):
        print(f"Error: Expected string but got {type(text).__name__} in truncate_string()")

    if len(text) > max_length:
        return text[:max_length].rsplit(' ', 1)[0] + "..."
    return text

def get_description(entry):
    description = entry.get(DESCRIPTION_KEY)

    if not description:
        description = entry.get(SUMMARY_KEY)

    if not description:
        content = entry.get(CONTENT_KEY)
        if isinstance(content, list) and content:
            description = content[0].get('value', '')

    if not description:
        return ""

    return html_to_plain_text(description).strip().replace('\n', ' ')

def truncate_description(plain_text_description, max_length_description):
    truncated_plain_text_description = ""
           
    if plain_text_description:
        truncated_plain_text_description = truncate_string(plain_text_description, max_length_description)
        
    return truncated_plain_text_description

def clean_articles(articles: list[dict], max_length_description: int) -> list[dict]:
    cleaned = []
    for article in articles:
        title = article.get(TITLE_KEY, '') or ''
        link = article.get(LINK_KEY, '') or ''
        description = article.get(DESCRIPTION_KEY, '') or ''
        skipped_reason = article.get(SKIPPED_REASON, None)
        published_date = article.get(PUBLISHED_DATE_KEY)
        feed_url = article.get(FEED_URL_KEY, '') or ''
        channel_image = article.get(CHANNEL_IMAGE_KEY, '') or ''

        cleaned_article = {
            TITLE_KEY: truncate_string(title.strip(), MAX_LENGTH_TITLE),
            LINK_KEY: truncate_string(link.strip(), MAX_LENGTH_LINK),
            DESCRIPTION_KEY: truncate_description(description.strip(), max_length_description),
            FEED_URL_KEY: truncate_string(feed_url.strip(), MAX_LENGTH_FEED_URL),
            CHANNEL_IMAGE_KEY: truncate_string(channel_image.strip(), MAX_LENGTH_CHANNEL_IMAGE),
            PUBLISHED_DATE_KEY: published_date  # Keep unmodified
        }

        if skipped_reason is not None:
            cleaned_article[SKIPPED_REASON] = truncate_string(skipped_reason.strip(), MAX_LENGTH_SKIPPED_REASON)

        cleaned.append(cleaned_article)

    return cleaned

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
    try:
        ext = tldextract.extract(url)
        # domain + suffix forms the registered domain
        return ext.domain + '.' + ext.suffix
    except Exception as e:
        print(f"Error parsing URL {url}: {e}")
        return "Unknown"

def print_feed_details(feedtitle, feed_url, recent_articles):
    print(f"\n{FEED_SEPARATOR}")
    print(f"[{feedtitle}] [{feed_url}]")
    if recent_articles:
        print(f"{FEED_SEPARATOR}")
        for article in recent_articles:
            print_article(article)

    print(f"{FEED_SEPARATOR}")

def print_article(entry):
    if(not entry[SKIPPED_REASON]):
        print(f"\t[{entry[TITLE_KEY]}] [{entry[DESCRIPTION_KEY]}] [{entry[LINK_KEY]}] [{entry[PUBLISHED_DATE_KEY]}]")
    else:
        print(f"\t[{entry[TITLE_KEY]}] [{entry[DESCRIPTION_KEY]}] [{entry[LINK_KEY]}] [{entry[PUBLISHED_DATE_KEY]}] [{entry[SKIPPED_REASON]}]")

def format_title_for_print(title):
    if len(title) > MAX_FEEDTITLE_LEN_PRINT:
        return title[:MAX_FEEDTITLE_LEN_PRINT - 1] + '…'
    return title.ljust(MAX_FEEDTITLE_LEN_PRINT)

def load_yaml_config(
    path: Optional[str] = None,
    user_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Load YAML config from 'path' and ensure all keys match allowed USER_OPTIONS.yaml_name.

    :param path: Path to YAML file.
    :param user_options: dict of UserOption objects (keys are macro names).
    :return: dict with YAML settings.
    """
    result: Dict[str, Any] = {}

    if not path:
        print("No YAML path provided; using defaults.")
        return result

    expanded = os.path.expanduser(path)
    abspath = os.path.abspath(expanded)

    if not os.path.isfile(abspath):
        print(f"YAML file does not exist at: {abspath}; using defaults.")
        return result

    try:
        with open(abspath, "r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh) or {}

        if not isinstance(loaded, dict):
            raise ValueError(f"Top-level structure in YAML must be a mapping/object: {abspath}")

        # --- Validation ---
        if user_options:
            valid_keys = {opt.yaml_name for opt in user_options.values() if opt.yaml_name}
            invalid_keys = [k for k in loaded.keys() if k not in valid_keys]
            if invalid_keys:
                raise ValueError(
                    f"Unrecognised YAML option(s): {', '.join(invalid_keys)}\n"
                    f"Valid options are: {', '.join(sorted(valid_keys))}"
                )

        result.update(loaded)

        # --- Debug info ---
        print(f"Loaded YAML configuration from: {abspath}")
        for key, value in loaded.items():
            print(f"  {key}: {value}")
        print(f"End loaded values from YAML file")

        return result

    except yaml.YAMLError as ye:
        raise ValueError(f"Failed to parse YAML file {abspath}: {ye}") from ye