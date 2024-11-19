"""
Main module that executes the transformation pipeline on command.
"""

__author__ = "Johanan Tai"

import argparse
import json
import os

from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

from ps_pipeline.transform import pipe
from ps_pipeline.json_model import Articles, TransformedArticles


"""
JSON DATA MODEL:
[
    {
    'article_title': ...,
    'article_timestamp': ...,
    'article_url': ...,
    'publish_location':...,
    'article_text:...,
    'statements': [
            {
                'attributed': ...,
                'text': ...
            },
            ...
        ],
    }
]
"""


def main():

    load_dotenv()

    parser = argparse.ArgumentParser(prog="ps_pipeline_transform")

    parser.add_argument(
        "-c",
        "--candidate_id",
        required=True,
        help="Candidate ID",
    )

    parser.add_argument(
        "-fp",
        "--filepath",
        type=Path,
        help="Specify filepath to the file",
    )

    parser.add_argument(
        "-n",
        "--articles_n",
        type=int,
        help="Limit the number of articles to process",
    )

    args = parser.parse_args()

    data_directory = Path(os.getenv("DATA_FILES_DIRECTORY"))
    extract_path = data_directory / args.candidate_id / "EXTRACT_FILES"
    transformed_path = data_directory / args.candidate_id / "TRANSFORMED_FILES"
    
    if args.filepath is None:
        extract_files = filter(lambda f: f.name.endswith(".json"), extract_path.iterdir())
        sorted_extract_files = sorted(
        extract_files, key=lambda x: x.stat().st_mtime, reverse=True
        )
        with open(sorted_extract_files[0], "r") as f:
            json_articles = Articles(json.load(f))
    else:
        if not args.filepath.exists():
            print("Cannot find extract file.")
            exit()

        with open(args.filepath, "r") as f:
            json_articles = Articles(json.load(f))

    articles = (
        json_articles.all[:args.articles_n]
        if args.articles_n
        else json_articles.all
    )

    progress_bar = tqdm(total=len(articles), desc="Processing")

    transformed_data = []
    for transformed_article in pipe.transform_json(articles):
        transformed_data.append(transformed_article)
        progress_bar.update(1)

    
    TransformedArticles(transformed_data).save(transformed_path)


if __name__ == "__main__":
    main()
