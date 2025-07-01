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

import csv
import json

from config import (
    TEMPLATE_HTML_FILE, TITLE_KEY, LINK_KEY, DESCRIPTION_KEY, PUBLISHED_DATE_KEY,
    CHANNEL_IMAGE_KEY, FEED_TITLE_KEY, TEXT_DATE_FORMAT_PRINT_SHORT, TIMEZONE_PRINT, TEXT_DATE_FORMAT_JSON
)
from utils import sanitize_for_html, get_website_name

def write_feed_to_json(posts, output_path, current_date, start_date, end_date, opml_title, opml_text):
    """Writes all RSS feed entries to a JSON file."""
    try:
        json_items = [
            {
                "title": post.get(TITLE_KEY, "").strip('"'),
                "link": post.get(LINK_KEY, ""),
                "published": post[PUBLISHED_DATE_KEY].strftime(TEXT_DATE_FORMAT_JSON),
                "source": get_website_name(post[LINK_KEY]),
                "description": post.get(DESCRIPTION_KEY, "").strip('"')
            }
            for post in sorted(posts, key=lambda p: p[PUBLISHED_DATE_KEY], reverse=True)
        ]

        data = {
            "start_date": start_date,
            "end_date" : end_date,
            "published": current_date,
            "title": opml_title,
            "text": opml_text,
            "items": json_items,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"Error writing {output_path}: {e}")

def write_feed_to_html(posts_to_print, outfilename, start_date_str, end_date_str, icon_map, opml_text, opml_title, include_images=True):
    """Writes all RSS feed entries to a HTML file."""

    sorted_posts = sorted(posts_to_print, key=lambda post: post[PUBLISHED_DATE_KEY], reverse=False)

    table_rows = []
    for post in sorted_posts:
        website_name = sanitize_for_html(get_website_name(post[LINK_KEY]))
        image_url = post.get(CHANNEL_IMAGE_KEY) or (icon_map.get(post[FEED_TITLE_KEY]) if icon_map else "")
        image_html = f"<img src='{sanitize_for_html(image_url)}' alt='{website_name}' class='channel-image'>" if (image_url and include_images) else ""

        published_date_string_print = post[PUBLISHED_DATE_KEY].strftime(TEXT_DATE_FORMAT_PRINT_SHORT)
        title_row = sanitize_for_html(post[TITLE_KEY]).strip('"')
        description_row = sanitize_for_html(post[DESCRIPTION_KEY]).strip('"')
        safe_post_link = sanitize_for_html(post[LINK_KEY])

        row_td = (
            f"<td>{published_date_string_print}</td>"
            f"<td><b>{website_name}</b></td>"
            f"<td>{image_html}</td>"
            f"<td><a href='{safe_post_link}' target='_blank'>{title_row}</a></td>"
            f"<td class='italic-cell'>{description_row}</td>"
        )
        table_rows.append(f"<tr>{row_td}</tr>\n")

    try:
        with open(TEMPLATE_HTML_FILE) as file:
            template = file.read()
        html_output = template.format(
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            timezone_print=TIMEZONE_PRINT,
            rows="".join(table_rows),
            opml_text=opml_text,
            opml_title=opml_title
        )
    except Exception as e:
        print(f"Error loading or formatting template: {e}")
        return

    try:
        with open(outfilename, 'w', encoding='utf-8', newline='') as file:
            file.write(html_output)
    except Exception as e:
        print(f"Error writing output file: {e}")

def write_feed_to_csv(posts_to_print, outfilename, start_date_str, end_date_str, opml_text, opml_title):
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
        
        published_date_string_print = post[PUBLISHED_DATE_KEY].strftime(TEXT_DATE_FORMAT_PRINT_SHORT)
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
            writer.writerow([f"Time range: {start_date_str} to {end_date_str}"])
            writer.writerow([f"Report Title: {opml_title}"])
            writer.writerow([f"Report Description: {opml_text}"])
            
            # Write the header for the CSV data
            writer.writerow([])  # Blank line before header
            writer.writerow(csv_header)  # Write header
            writer.writerows(csv_rows)   # Write all rows
    except Exception as e:
        print(f"Error writing CSV output file: {e}")