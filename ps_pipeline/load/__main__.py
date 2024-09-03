import argparse
import json
import psycopg
import os

from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

from ps_pipeline.load import pipe
from ps_pipeline.json_model import TransformedArticles, HarvestArticles


def main():

    load_dotenv()

    parser = argparse.ArgumentParser(prog="ps_automation_transform")

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
        help="Specify filepath to the extract file",
    )

    parser.add_argument(
        "-n",
        "--articles_n",
        type=int,
        help="Limit the number of articles to process",
    )

    args = parser.parse_args()

    vsdb_connection_info = {
        "host": os.getenv("VSDB_HOST"),
        "dbname": os.getenv("VSDB_DATABASE"),
        "port": os.getenv("VSDB_PORT"),
        "user": os.getenv("VSDB_USER"),
        "password": os.getenv("VSDB_PASSWORD"),
    }

    data_directory = Path(os.getenv("DATA_FILES_DIRECTORY"))
    transformed_path = data_directory / args.candidate_id / "TRANSFORMED_FILES"
    harvest_path = data_directory / args.candidate_id / "HARVEST_FILES"

    if args.filepath is None:
        transformed_files = filter(
            lambda f: f.name.endswith(".json"), transformed_path.iterdir()
        )
        sorted_transformed_files = sorted(
            transformed_files, key=lambda x: x.stat().st_mtime, reverse=True
        )
        with open(sorted_transformed_files[0], "r") as f:
            json_articles = TransformedArticles(json.load(f))
    else:
        if not args.filepath.exists():
            print("Cannot find transformed file.")
            exit()

        with open(args.filepath, "r") as f:
            json_articles = TransformedArticles(json.load(f))

    vsdb_connection = psycopg.connect(**vsdb_connection_info)

    transformed_articles = (
        json_articles.all[: args.articles_n] if args.articles_n else json_articles.all
    )

    progress_bar = tqdm(total=len(transformed_articles), desc="Processing")

    harvest_data = []
    for harvest_article in pipe.harvest_json(
        transformed_articles,
        vsdb_connection,
    ):
        if harvest_article not in harvest_data:
            harvest_data.append(harvest_article)
            progress_bar.update(1)

    HarvestArticles(harvest_data).save(harvest_path)


if __name__ == "__main__":
    main()
