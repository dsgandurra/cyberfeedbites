import html
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from config import MAX_LENGTH_DESCRIPTION, FEED_SEPARATOR, SUMMARY_KEY, DESCRIPTION_KEY
from config import XMLURL_KEY, PUBLISHED_PARSED_KEY, UPDATED_PARSED_KEY, FEED_URL_KEY, TITLE_KEY, LINK_KEY, DESCRIPTION_KEY, PUBLISHED_DATE_KEY

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

def get_last_time(max_days):
    """Gets the earliest UTC time based on the maximum number of days to look back."""
    max_look_back_period = timedelta(days=max_days)
    now = datetime.now(timezone.utc)
    earliest_time = now - max_look_back_period

    return earliest_time

def format_description(entry):
    """Formats the description of the RSS entry."""
    description = entry.get(DESCRIPTION_KEY)
    
    if not description:
        description = entry.get(SUMMARY_KEY, DESCRIPTION_KEY)
        truncated_plain_text_description = ""
           
    if description:
        plain_text_description = html_to_plain_text(description).strip().replace('\n', ' ')
        truncated_plain_text_description = truncate_string(plain_text_description, MAX_LENGTH_DESCRIPTION)
        
    return truncated_plain_text_description

def sanitize_text(text):
    """Sanitises the text output."""
    text = html.escape(text)
    
    # Replace newlines with <br> to preserve the breaks, and carriage returns with an empty string
    text = text.replace('\n', '<br>').replace('\r', '')
    
    # If the text contains commas, double quotes, or newlines, enclose it in double quotes
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

def print_feed_details(feedtitle, feed_url, recent_articles, lock):
    """Helper function to print feed details."""
    with lock:
        print(f"\n{FEED_SEPARATOR}")
        print(f"[{feedtitle}] [{feed_url}]")
        if recent_articles:
            print(f"{FEED_SEPARATOR}")
            for article in recent_articles:
                print_article(article)
        print(f"{FEED_SEPARATOR}")

def print_article(entry):
    """Helper function to print article details."""
    print(f"\t[{entry[TITLE_KEY]}] [{entry[DESCRIPTION_KEY]}] [{entry[LINK_KEY]}] [{entry[PUBLISHED_DATE_KEY]}]")