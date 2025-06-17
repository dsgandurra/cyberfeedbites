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

from rss_reader import process_feed, read_opml
from utils import get_last_time
from config import MAX_THREAD_WORKERS, MAX_DAYS_BACK

def process_rss_feed(opml_filename, max_days):
    """Handles the RSS feed processing."""
    all_entries = []
    all_entries_queue = queue.Queue()
    lock = threading.Lock()
    
    # Get the earliest time to look back in the feeds
    earliest_date = get_last_time(max_days)
    
    # Read and sort the RSS feed URLs from the OPML file
    feeds, icon_map, top_text, top_title = read_opml(opml_filename)
    sorted_feeds = sorted(feeds, key=lambda feed: feed[0])

    # Using ThreadPoolExecutor to process feeds concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREAD_WORKERS) as executor:
        future_to_feed = {
            executor.submit(process_feed, feedtitle, feed_url, earliest_date, lock, all_entries_queue): (feedtitle, feed_url)
            for feedtitle, feed_url in sorted_feeds
        }

        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(future_to_feed):
            feedtitle, feed_url = future_to_feed[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error processing {feedtitle} ({feed_url}): {e}")
    
    # Collect all processed entries from the queue
    all_entries = []
    while not all_entries_queue.empty():
        all_entries.append(all_entries_queue.get())

    return all_entries, earliest_date, icon_map, top_text, top_title