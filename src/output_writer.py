import os

from config import TEMPLATE_HTML_FILE, TITLE_KEY, LINK_KEY, DESCRIPTION_KEY, PUBLISHED_DATE_KEY, CHANNEL_IMAGE_KEY, FEED_TITLE_KEY
from utils import sanitize_text, get_website_name

def write_all_rss_to_html(posts_to_print, outfilename, current_date, earliest_time, icon_map):
    """Writes all RSS feed entries to an HTML file."""
    
    sorted_posts = sorted(posts_to_print, key=lambda post: post[PUBLISHED_DATE_KEY])
    total_posts = len(sorted_posts)
    
    table_rows = []
    for id_post, post in enumerate(sorted_posts, start=1):
        website_name = get_website_name(post[LINK_KEY])
        channel_image_url = post.get(CHANNEL_IMAGE_KEY)
        if channel_image_url:
            safe_url = sanitize_text(channel_image_url)
            image_html = f"<img src='{channel_image_url}' alt='Channel Image' class='channel-image'>"
        elif icon_map:
            channel_image_url = icon_map.get(post[FEED_TITLE_KEY])
            image_html = f"<img src='{channel_image_url}' alt='Channel Image' class='channel-image'>" if channel_image_url else ""
        else:
            image_html = ""
        row_td = (
            f"<td>{id_post} / {total_posts}</td>"
            f"<td>{post[PUBLISHED_DATE_KEY]}</td>"
            f"<td><b>{website_name}</b></td>"
            f"<td>{image_html}</td>"
            f"<td>{sanitize_text(post[TITLE_KEY])}</td>"
            f"<td>{sanitize_text(post[DESCRIPTION_KEY])}</td>"
            f"<td><a href='{post[LINK_KEY]}' target='_blank'>{post[LINK_KEY]}</a></td>"
        )
        table_rows.append(f"<tr>{row_td}</tr>\n")

    table_rows = "".join(table_rows)

    try:
        with open(TEMPLATE_HTML_FILE) as file:
            template = file.read()
        html_output = template.format(earliest_time=earliest_time,current_date=current_date, rows=table_rows)
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