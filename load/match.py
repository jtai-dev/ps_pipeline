# Built-ins
import os
import json
from pathlib import Path

# External Packages & Libraries
import psycopg
from rapidfuzz import fuzz
from dotenv import load_dotenv

# Internal Packages & Libraries
if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))

from json_model import TransformedArticles
from record_matcher.matcher import RecordMatcher


def connect_to_database():
    PACKAGE_DIR = Path(__file__).parent.parent
    CONNECTION_INFO_FILEPATH = PACKAGE_DIR / "connection_info.json"

    with open(CONNECTION_INFO_FILEPATH, "r") as f:
        connection_info = json.load(f)

    return psycopg.connect(**connection_info)


def query_from_database(query, connection):
    cursor = connection.cursor()
    cursor.execute(query)
    headers = [str(k[0]) for k in cursor.description]
    return {
        index: dict(zip(headers, row)) for index, row in enumerate(cursor.fetchall())
    }

def load_query_string(query_filename):
    """Reads from a .sql file to be executed"""
    package_dir = Path(__file__).parent.parent
    with open(package_dir / "queries" / f"{query_filename}.sql", "r") as f:
        query_string = f.read()

    return query_string

def get_names_from_statements(transformed_json: TransformedArticles):
    set_of_names = set()

    for record in transformed_json.all:
        for statement in record.statements.all:
            set_of_names.update(statement.attributed)

    return {i: {"name": name} for i, name in enumerate(set_of_names)}


def match(names, queryset):
    tb_matcher = RecordMatcher()
    tb_matcher.x_records = names
    tb_matcher.y_records = queryset

    tb_config = tb_matcher.config
    tb_config.scorers_by_column.SCORERS.update(
        {
            "token_set_ratio": lambda x, y: fuzz.token_set_ratio(
                str(x).lower(), str(y.lower())
            )
        }
    )
    tb_config.scorers_by_column.default = "token_set_ratio"
    tb_config.thresholds_by_column.default = 85

    tb_config.populate()

    tb_config.columns_to_match["name"] = "candidate_name"
    tb_config.columns_to_get["candidate_id"] = "candidate_id"
    tb_config.columns_to_get["candidate_name"] = "candidate_name"

    tb_matcher.required_threshold = 75
    tb_matcher.duplicate_threshold = 100

    # records_matched =
    # {0: {name:..., candidate_name:..., candidate_id:..., 'match_status':...,  'row(s)_matched':..., 'match_score':...}}

    records_matched, match_info = tb_matcher.match()

    for record in records_matched.values():
        candidate_ids = []

        record["candidate_name"] = (
            [record["candidate_name"]] if record["candidate_name"] else []
        )

        if record["match_status"] == "AMBIGUOUS":
            candidate_ids = []
            for i in record["row(s)_matched"].split(","):
                candidate_ids.append(queryset[int(i.strip())]["candidate_id"])
                record["candidate_name"].append(
                    queryset[int(i.strip())]["candidate_name"]
                )

    max_key_length = max(match_info, key=lambda x: len(x)) if match_info else 0
    for k, v in match_info.items():
        print(f"{k.rjust(len(max_key_length)+4)}:", v)


    return {record["name"]: record for record in records_matched.values()}


def main(articlejson):
    load_dotenv()

    db_connection_info = {
        'host': os.getenv('VSDB_HOST'),
        'dbname': os.getenv('VSDB_DATABASE'),
        'port':os.getenv('VSDB_PORT'),
        'user':os.getenv('VSDB_USER'),
        'password':os.getenv('VSDB_PASSWORD'),
        }
    
    vs_db_connection = psycopg.connect()
    query = load_query_string("office-candidates-active.sql")
    records_query = query_from_database(query, vs_db_connection)

    return match(get_names_from_statements(articlejson), records_query)
