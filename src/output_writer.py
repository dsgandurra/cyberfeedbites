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

import os
import csv

from config import (
    TEMPLATE_HTML_FILE, TITLE_KEY, LINK_KEY, DESCRIPTION_KEY, PUBLISHED_DATE_KEY,
    CHANNEL_IMAGE_KEY, FEED_TITLE_KEY, TEXT_DATE_FORMAT_PRINT, TIMEZONE_PRINT
)
from utils import sanitize_for_html, get_website_name

def write_all_rss_to_html(posts_to_print, outfilename, current_date, earliest_date, icon_map, top_text, top_title):
    """Writes all RSS feed entries to an HTML file."""
    
    sorted_posts = sorted(posts_to_print, key=lambda post: post[PUBLISHED_DATE_KEY])
    total_posts = len(sorted_posts)
    
    table_rows = []
    for id_post, post in enumerate(sorted_posts, start=1):
        website_name = get_website_name(post[LINK_KEY])
        
        # Resolve image URL safely
        image_url = post.get(CHANNEL_IMAGE_KEY) or (icon_map.get(post[FEED_TITLE_KEY]) if icon_map else "")
        image_html = f"<img src='{sanitize_for_html(image_url)}' alt='' class='channel-image'>" if image_url else ""

        published_date_string_print = post[PUBLISHED_DATE_KEY].strftime(TEXT_DATE_FORMAT_PRINT)
        title_row = sanitize_for_html(post[TITLE_KEY]).strip('"')
        description_row = sanitize_for_html(post[DESCRIPTION_KEY]).strip('"')
        safe_post_link = sanitize_for_html(post[LINK_KEY])

        row_td = (
            f"<td>{id_post}/{total_posts}</td>"
            f"<td>{published_date_string_print}</td>"
            f"<td><b>{website_name}</b></td>"
            f"<td>{image_html}</td>"
            f"<td>{title_row}</td>"
            f"<td class='italic-cell'>{description_row}</td>"
            f"<td><a href='{safe_post_link}' target='_blank'>{safe_post_link}</a></td>"
        )
        table_rows.append(f"<tr>{row_td}</tr>")

    try:
        with open(TEMPLATE_HTML_FILE) as file:
            template = file.read()
        html_output = template.format(
            earliest_date=earliest_date,
            current_date=current_date,
            timezone_print=TIMEZONE_PRINT,
            rows="".join(table_rows),
            top_text=top_text,
            top_title=top_title
        )
    except FileNotFoundError:
        print(f"Template file {TEMPLATE_HTML_FILE} not found.")
        return
    except Exception as e:
        print(f"Error reading template file: {e}")
        return

    try:
        with open(outfilename, 'w', encoding='utf-8', newline='') as file:
            file.write(html_output)
    except Exception as e:
        print(f"Error writing output file: {e}")

import csv

def write_all_rss_to_csv(posts_to_print, outfilename, current_date, earliest_date, top_text, top_title):
    """Writes all RSS feed entries to a CSV file."""
    
    # Sort posts by published date
    sorted_posts = sorted(posts_to_print, key=lambda post: post[PUBLISHED_DATE_KEY])

    # Prepare CSV header
    csv_header = [
        'Date (UTC)', 'Website', 'Title', 'Description', 'Link'
    ]

    # Prepare the CSV content
    csv_rows = []
    for post in sorted_posts:
        website_name = get_website_name(post[LINK_KEY])

        published_date_string_print = post[PUBLISHED_DATE_KEY].strftime(TEXT_DATE_FORMAT_PRINT)
        title_row = sanitize_for_html(post[TITLE_KEY]).strip()  # Strip leading/trailing spaces
        description_row = sanitize_for_html(post[DESCRIPTION_KEY]).strip()  # Strip leading/trailing spaces
        safe_post_link = sanitize_for_html(post[LINK_KEY]).strip()  # Strip leading/trailing spaces

        # Add row for CSV
        csv_rows.append([
            published_date_string_print,
            website_name,
            title_row,
            description_row,
            safe_post_link
        ])

    try:
        # Write to CSV file
        with open(outfilename, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            
            # Write metadata
            writer.writerow([f"Time range: {earliest_date} to {current_date}"])
            writer.writerow([f"Report Title: {top_title}"])
            writer.writerow([f"Report Description: {top_text}"])
            
            # Write the header for the CSV data
            writer.writerow([])  # Blank line before header
            writer.writerow(csv_header)  # Write header
            writer.writerows(csv_rows)   # Write all rows
    except Exception as e:
        print(f"Error writing CSV output file: {e}")
