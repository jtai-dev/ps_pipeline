"""
General logic for the extraction pipeline combining parser and scraper.
"""

__author__ = "Johanan Tai"

import json
from tqdm import tqdm

from ps_pipeline.json_model import Articles


def get_latest_article(extract_files):
    latest_list = []

    for file in extract_files:
        with open(file, "r") as f:
            latest_list.append(Articles(json.load(f)).latest)

    return max(latest_list) if latest_list else None


def webscrape(web_parser, web_scraper, **kwargs) -> list[dict[str, str]]:

    if kwargs.get("compare"):
        last_collected = get_latest_article(kwargs.get("extract_files"))

    articles_extracted = web_scraper.scrape(
        kwargs.get("url"),
        web_parser,
        kwargs.get("html_path"),
        last_collected,
    )

    return articles_extracted


def html_filescrape(web_parser, html_path) -> list[dict[str, str]]:

    html_files = filter(lambda f: f.name.endswith(".html"), html_path.iterdir())
    sorted_html_files = sorted(
        html_files, key=lambda x: x.stat().st_mtime, reverse=False
    )

    articles_extracted = []

    for file in tqdm(sorted_html_files):
        with open(file, "r", encoding="utf-8") as f:
            try:
                # Reads the file as a ArticleSoup object
                article = web_parser.ArticleSoup(f.read())
                articles_extracted.append(article.extract())
            except UnicodeDecodeError:
                pass

    return articles_extracted


def soup_to_inserts():
    pass
