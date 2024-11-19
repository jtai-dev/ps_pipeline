"""
Main module that executes the extraction pipeline on command.
"""

__author__ = "Johanan Tai"

import os
import json
import argparse
from pathlib import Path

from dotenv import load_dotenv
from importlib import import_module

from ps_pipeline.json_model import Articles


SOURCE = {
    "53279": {
        "url": "https://www.whitehouse.gov/briefing-room/",
        "parser": "soup_0",
        "scraper": "sel_1",
    },
    "120012": {
        "url": "https://www.whitehouse.gov/briefing-room/",
        "parser": "soup_0",
        "scraper": "sel_1",
    },
    "11701": {
        "url": "https://www.capito.senate.gov/news/press-releases",
        "parser": "soup_1",
        "scraper": "sel_1",
    },
    "76151": {
        "url": "https://www.booker.senate.gov/news/press",
        "parser": "soup_1",
        "scraper": "sel_1",
    },
    "70114": {
        "url": "https://aguilar.house.gov/category/congress_press_release/",
        "parser": "soup_10",
        "scraper": "sel_1",
    },
    "28918": {
        "url": "https://www.speaker.gov/news/",
        "parser": "soup_11",
        "scraper": "sel_3",
    },
    "3470": {
        "url": "https://www.baldwin.senate.gov/news/press-releases",
        "parser": "soup_2",
        "scraper": "sel_1",
    },
    "17852": {
        "url": "https://www.schatz.senate.gov/news/press-releases/",
        "parser": "soup_2",
        "scraper": "sel_1",
    },
    "128583": {
        "url": "https://www.ernst.senate.gov/news/press-releases",
        "parser": "soup_2",
        "scraper": "sel_1",
    },
    "26976": {
        "url": "https://www.schumer.senate.gov/newsroom/press-releases",
        "parser": "soup_2",
        "scraper": "sel_1",
    },
    "141272": {
        "url": "https://www.warren.senate.gov/newsroom/press-releases",
        "parser": "soup_3",
        "scraper": "sel_1",
    },
    "26847": {
        "url": "https://www.durbin.senate.gov/newsroom/press-releases",
        "parser": "soup_3",
        "scraper": "sel_1",
    },
    "69579": {
        "url": "https://www.cortezmasto.senate.gov/news/press-releases",
        "parser": "soup_3",
        "scraper": "sel_1",
    },
    "515": {
        "url": "https://www.stabenow.senate.gov/news",
        "parser": "soup_3",
        "scraper": "sel_1",
    },
    "7547": {
        "url": "https://www.manchin.senate.gov/newsroom/press-releases",
        "parser": "soup_3",
        "scraper": "sel_1",
    },
    "65092": {
        "url": "https://www.klobuchar.senate.gov/public/index.cfm/news-releases",
        "parser": "soup_4",
        "scraper": "sel_1",
    },
    "53298": {
        "url": "https://www.mcconnell.senate.gov/public/index.cfm/pressreleases",
        "parser": "soup_4",
        "scraper": "sel_1",
    },
    "398": {
        "url": "https://www.thune.senate.gov/public/index.cfm/press-releases",
        "parser": "soup_4",
        "scraper": "sel_1",
    },
    "52662": {
        "url": "https://www.barrasso.senate.gov/public/index.cfm/news-releases",
        "parser": "soup_4",
        "scraper": "sel_1",
    },
    "35858": {
        "url": "https://katherineclark.house.gov/press-releases",
        "parser": "soup_4",
        "scraper": "sel_1",
    },
    "152539": {
        "url": "https://stefanik.house.gov/media-center",
        "parser": "soup_4",
        "scraper": "sel_1",
    },
    "27110": {
        "url": "https://www.sanders.senate.gov/media/press-releases/",
        "parser": "soup_5",
        "scraper": "sel_1",
    },
    "53358": {
        "url": "https://www.murray.senate.gov/category/press-releases/",
        "parser": "soup_5",
        "scraper": "sel_1",
    },
    "135720": {
        "url": "https://www.daines.senate.gov/news/press-releases/",
        "parser": "soup_5",
        "scraper": "sel_1",
    },
    "9026": {
        "url": "https://www.majorityleader.gov/news/documentquery.aspx",
        "parser": "soup_6",
        "scraper": "sel_2",
    },
    "38894": {
        "url": "https://www.majoritywhip.gov/news/documentquery.aspx",
        "parser": "soup_6",
        "scraper": "sel_2",
    },
    "146274": {
        "url": "https://palmer.house.gov/media-center",
        "parser": "soup_7",
        "scraper": "sel_2",
    },
    "55285": {
        "url": "https://democraticleader.house.gov/media",
        "parser": "soup_7",
        "scraper": "sel_2",
    },
    "535": {
        "url": "https://www.warner.senate.gov/public/index.cfm/pressreleases",
        "parser": "soup_8",
        "scraper": "sel_1",
    },
    "27066": {
        "url": "https://clyburn.house.gov/press-releases",
        "parser": "soup_9",
        "scraper": "sel_1",
    },
}


def extract_from_files(web_parser, html_path):
    from tqdm import tqdm

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


def main():

    load_dotenv()

    parser = argparse.ArgumentParser(prog="ps_pipeline_webscrape")

    parser.add_argument(
        "-c",
        "--candidate_id",
        required=True,
        help="Candidate ID",
    )

    parser.add_argument(
        "-e",
        "--extract_from_files",
        action="store_true",
        help="Extract from HTML files",
    )

    parser.add_argument(
        "-ce",
        "--compare",
        action="store_false",
        help="Compare with older extract",
    )

    args = parser.parse_args()
    candidate_source = SOURCE.get(args.candidate_id)

    if candidate_source is None:
        print("Candidate not found.")
        exit()

    data_directory = Path(os.getenv("DATA_FILES_DIRECTORY"))
    html_path = data_directory / args.candidate_id / "HTML_FILES"
    extract_path = data_directory / args.candidate_id / "EXTRACT_FILES"

    webparser = import_module(
        f"ps_pipeline.extract.web.parser.{candidate_source.get('parser')}"
    )

    if not args.extract_from_files:
        webscraper = import_module(
            f"ps_pipeline.extract.web.scraper.{candidate_source.get('scraper')}"
        )
        extract_files = filter(
            lambda f: f.name.endswith(".json"), extract_path.iterdir()
        )

        latest_list = []

        if args.compare:
            for file in extract_files:
                with open(file, "r") as f:
                    latest_list.append(Articles(json.load(f)).latest)

        articles_extracted = webscraper.scrape(
            candidate_source.get("url"),
            webparser,
            html_path,
            max(latest_list) if latest_list else None,
        )

    else:
        if not html_path.exists():
            print("Could not find HTML files to extract")
            exit()

        articles_extracted = extract_from_files(webparser, html_path)

    articles_json = Articles(articles_extracted)
    articles_json.save(
        filename=candidate_source.get("parser"), export_path=extract_path
    )


if __name__ == "__main__":
    main()
