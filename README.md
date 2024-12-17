# CyberFeedBites: A Lightweight Cybersecurity RSS Feed Reader

CyberFeedBites is a lightweight Python tool that collects the latest cybersecurity news from RSS feeds specified in an OPML file and generates an HTML file with titles, brief descriptions, and links to articles, sorted by date, providing a quick overview of the latest cybersecurity news. CyberFeedBites is customisable to include different feed sources and fetch news from the past 'X' days.

## Features

- Collects and processes cybersecurity news from various RSS feeds (list included).
- Fetches cybersecurity news from the past 'X' days
- Generates an HTML file with titles, brief descriptions, and links to articles, sorted by date, for a quick overview of the latest cybersecurity news.
- Includes a sample OPML file with a list of notable cybersecurity RSS sources.

## TLDR;
CyberFeedBites is ready to use once the dependencies are installed. To run it as is, follow these steps to fetch the latest 24-hour articles from the sources in the provided `cybersecnews-sources.opml` file and generate a summary in an HTML file saved in the `data/html_reports/` directory.

1. Clone the repository: `git clone https://github.com/dsgandurra/cyberfeedbites.git`
2. Move to the root folder: `cd cyberfeedbites`
3. Install dependencies: `pip install -r requirements.txt`
4. Run CyberFeedBites: `python src/main.py`
5. Check the generated HTML file in the `data/html_reports/` directory

## Installation

1. Clone this repository:

```bash
git clone https://github.com/dsgandurra/cyberfeedbites.git
cd cyberfeedbites
```
2. Before running CyberFeedBites, it's recommended to use a virtual environment to keep your project's dependencies isolated. To do so, create and activate a virtual environment:

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
3. Install the required dependencies:

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

2. Run CyberFeedBites with optional parameters:

```bash
python src/main.py [--days <days_back>] [--opml <opml_file_path>]
```
- `--days`: Specify the number of days to fetch news from (e.g., `--days 2`). Defaults to the `DAYS_BACK` value set in `config.py`.
- `--opml`: Provide a custom path to an OPML file (e.g., `--opml data/rss_sources/custom.opml`). Defaults to the OPML file specified by `OPML_FILENAME` in `config.py`.

Examples:
- Fetch news from the last 3 days:
  ```bash
  python src/main.py --days 3
  ```
- Use a custom OPML file:
  ```bash
  python src/main.py --opml data/rss_sources/custom.opml
  ```
- Combine both:
  ```bash
  python src/main.py --days 5 --opml data/rss_sources/another_file.opml

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

- You can modify the default number of days for news retrieval by changing the `DAYS_BACK` parameter in the `config.py` file. Depending on the number of RSS feeds, it is best to keep this number small to make the output manageable (e.g., with the current feeds, around 100-150 entries are generated with the default value of 1 day). The `MAX_DAYS_BACK` parameter in the `config.py` file limits the maximum number of days that can be retrieved (default is 7 days). You can edit this variable in `config.py` if you want to increase this limit.
- You can also add or remove RSS feed sources by editing directly the `cybersecnews-sources.opml` file.
- CyberFeedBites uses a template for the HTML output, which can be customised by editing the `template.html` file located in the `data/templates` folder, along with a simple `style.css` file. Note that if you choose a different directory to store the report, make sure to reference the css.

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- CyberFeedBites uses the `feedparser` library for parsing RSS feeds.
- The `beautifulsoup4` library is used for HTML parsing and sanitising descriptions.