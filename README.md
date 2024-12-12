# CyberFeedBites: A Quick Cybersecurity RSS Feed Reader

CyberFeedBites is a lightweight Python script that collects the latest cybersecurity news from RSS feeds specified in an OPML file and generates an HTML table with titles, brief descriptions, and links to articles, sorted by date, for a quick overview of the latest cybersecurity news. The script is customisable to include different feed sources and fetch news from the past 'X' days (configurable). The generated HTML file is saved with a timestamp for easy reference.

## Features

- Collects and processes cybersecurity news from various RSS feeds (list included and expandable).
- Fetches cybersecurity news from the past 'X' days (configurable).
- Generates an HTML table with titles, brief descriptions, and links to articles, sorted by date, for a quick overview of the latest cybersecurity news.
- Saves the generated HTML file with a timestamp for easy reference.
- Includes a sample OPML file with a list of notable cybersecurity RSS sources.

## TLDR;
CyberFeedBites is ready to use once the requirements are installed. It will fetch the latest 24h articles from the sources in the provided `cybersecnews-sources.opml` file and write the summary to an HTML file under `data/html_reports`. Follow these steps:

1. Clone the repository: `git clone https://github.com/dsgandurra/cyberfeedbites.git`
2. Install dependencies: `pip install -r requirements.txt`
3. (Optional) Configure `config.py`
4. Run the script: `python src/main.py`
5. Check the generated HTML file in `data/html_reports`

## Installation and Usage Overview

1. Clone this repository:

```bash
git clone https://github.com/dsgandurra/cyberfeedbites.git
cd cyberfeedbites
```

2. Install the required Python dependencies (see below Requirements).

3. (Optional) Configure the settings in `config.py` as needed (e.g., changing the number of days for news retrieval or updating the RSS feed sources). If you keep the default values, it will fetch the latest 24h articles from the sources in the provided `cybersecnews-sources.opml` file.

4. Run the program (see below Usage). An output HTML file will be generated with a list of recent cybersecurity news retrieved (see below, Output).

## Requirements

Before running the script, ensure that you have the required dependencies installed. It's recommended to use a virtual environment to keep your project's dependencies isolated.

1. Create and activate a virtual environment:

   On **Linux/macOS**:
   ```bash
   python3 -m venv myenv
   source myenv/bin/activate
   ```

   On **Windows**:
   ```bash
   python -m venv myenv
   .\myenv\Scripts\activate
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

The required packages are:

- `feedparser`: For parsing RSS feeds.
- `beautifulsoup4`: For HTML parsing and manipulation.

## Usage

1. Navigate to the root folder of the project:

```bash
cd path/to/cyberfeedbites
```

2. Run the script:

```bash
python src/main.py
```

This will process the RSS feeds specified in the OPML file (`data/rss_sources/cybersecnews-sources.opml`), retrieve news from the past 'X' days (as defined in the config), and generate an HTML file.

## Output

The resulting HTML file, which lists the news from the past few days, will be saved in the `data/html_reports` folder. The filename will be in the following format:

`securitynews_YYYY-MM-DD_HH-MM-SS.html`

Each HTML file contains a table with the following columns:

- **ID**: The article's position in the list.
- **Date**: The date the article was published.
- **Website**: The name of the website from the link.
- **Title**: The title of the article.
- **Description**: A brief description of the article.
- **Link**: The URL to the full article.

## Sample OPML File

The repository includes a sample OPML file (`data/rss_sources/cybersecnews-sources.opml`) with a curated list of relevant RSS sources. You can edit this file to add or remove feed URLs according to your preferences.

## Customization

You can modify the number of days of news to retrieve by changing the `DAYS_BACK` parameter in the `config.py` file. Depending on the number of RSS feeds, it is best to keep this number to a minimum (e.g., with the current feeds, around 100-150 entries are generated with the default value of 1 day). The `MAX_DAYS_BACK` parameter in the `config.py` file limits the maximum number of days that can be retrieved (default, 7 days).
- You can also add or remove RSS feed sources by editing the `cybersecnews-sources.opml` file.
- The script uses a template for the HTML output, which can be customised by editing the `template.html` file located in the `data/templates` folder, together with a simple `style.css` file.

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- This script uses the `feedparser` library for parsing RSS feeds.
- The `beautifulsoup4` library is used for HTML parsing and sanitising descriptions.