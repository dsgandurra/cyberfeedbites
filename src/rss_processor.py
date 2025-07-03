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

import queue
import threading
import concurrent.futures
import xml.etree.ElementTree as ET

from rss_reader import process_feed, read_opml
from config import MAX_THREAD_WORKERS, MAX_DAYS_BACK

def process_rss_feed(opml_filename, start_date, end_date, max_length_description):
    """Handles the RSS feed processing."""
    all_entries_queue = queue.Queue()
    lock = threading.Lock()

    try:
        feeds, icon_map, opml_text, opml_title = read_opml(opml_filename)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"The OPML file '{opml_filename}' does not exist.") from e
    except ET.ParseError as e:
        msg = f"The OPML file '{opml_filename}' is not well-formed XML: {e}"
        raise ET.ParseError(msg) from e
    except Exception as e:
        raise RuntimeError(f"Error reading OPML file '{opml_filename}': {e}") from e

    sorted_feeds = sorted(feeds, key=lambda feed: feed[0])

    errors = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREAD_WORKERS) as executor:
        future_to_feed = {
            executor.submit(process_feed, feedtitle, feed_url, start_date, end_date, max_length_description, lock, all_entries_queue): (feedtitle, feed_url)
            for feedtitle, feed_url in sorted_feeds
        }

        for future in concurrent.futures.as_completed(future_to_feed):
            feedtitle, feed_url = future_to_feed[future]
            try:
                entries, error = future.result()
                if error is not None:
                    errors.append(error)
            except Exception as e:
                print(f"Error processing {feedtitle} ({feed_url}): {e}")
                errors.append((feedtitle, feed_url))

    all_entries = []
    while not all_entries_queue.empty():
        all_entries.append(all_entries_queue.get())

    return all_entries, icon_map, opml_text, opml_title, errors