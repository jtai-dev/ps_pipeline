from pathlib import Path

# External Packages & Libraries
from rapidfuzz import fuzz
from dateutil.parser import parse as datetimeparse
from collections import defaultdict
from record_matcher.matcher import RecordMatcher

from ps_pipeline.json_model import TransformedArticle


def query_as_records(query: str, connection, **params) -> dict[int, dict[str, str]]:
    """Converts query results into records"""
    cursor = connection.cursor()
    cursor.execute(query, params)
    headers = [str(k[0]) for k in cursor.description]
    return {
        index: dict(zip(headers, row)) for index, row in enumerate(cursor.fetchall())
    }


def query_as_reference(query: str, connection, **params) -> dict[str, int]:
    """A two column query result that can be turn into a reference"""
    cursor = connection.cursor()
    cursor.execute(query, params)
    return {name: ids for ids, name in cursor.fetchall()}


def load_query_string(filename: Path) -> str:
    """Reads from a .sql file to be executed"""
    package_dir = Path(__file__).parent.parent
    with open(package_dir / "queries" / f"{filename}.sql", "r") as f:
        query_string = f.read()

    return query_string


def match_records(records_x, records_y) -> dict[int, dict[str, str]]:

    tb_matcher = RecordMatcher()
    tb_matcher.x_records = records_x
    tb_matcher.y_records = records_y

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

    tb_matcher.required_threshold = 80
    tb_matcher.duplicate_threshold = 100

    # records_matched =
    # {0: {name:..., candidate_id:..., 'match_status':...,  'row(s)_matched':..., 'match_score':...}}

    records_matched, match_info = tb_matcher.match()
    max_key_length = max(match_info, key=lambda x: len(x)) if match_info else 0

    for k, v in match_info.items():
        print(f"{k.rjust(len(max_key_length)+4)}:", v)

    return records_matched


def match_json_names(
    articles_transformed: list[TransformedArticle],
    vsdb_connection,
) -> dict[str, dict[str, str]]:

    unique_names = set()

    for article in articles_transformed:
        unique_names.update(article.nlp_extracts.all_attributed)

    records_name = {i: {"name": name} for i, name in enumerate(unique_names)}
    records_query = query_as_records(
        load_query_string("office-candidates-active"), vsdb_connection
    )

    # records_matched =
    # {0: {name:..., candidate_id:..., 'match_status':...,  'row(s)_matched':..., 'match_score':...}}
    records_matched = match_records(records_name, records_query)

    name_to_records = defaultdict(list)

    for record in records_matched.values():
        for i in record["row(s)_matched"].split(","):
            name = record["name"]
            if i:
                record_query = records_query.get(int(i.strip()))
                name_to_records[name].append(
                    {
                        "candidate_id": record_query.get("candidate_id"),
                        "match_status": record.get("match_status"),
                        "match_score": record.get("match_score"),
                    }
                )

    return name_to_records


def harvest_json(
    articles_transformed: list[TransformedArticle],
    vsdb_connection,
):

    name_to_records = match_json_names(articles_transformed, vsdb_connection)
    speechtype_ref = query_as_reference(
        load_query_string("speechtypes"), vsdb_connection
    )

    for article in articles_transformed:

        harvest_article = {
            "candidate_ids": None,
            "speechtype_id": None,
            "title": article.title,
            "speechdate": datetimeparse(article.timestamp).strftime("%Y-%m-%d"),
            "location": article.publish_location,
            "url": article.url,
            "speechtext": None,
            "review": False,
            "review_msg": None,
        }

        # A candidate can make multiple statements that are separated in an article
        harvests_by_candidates = defaultdict(list)

        for nlp_extract in article.nlp_extracts.all:

            vsdb_records = name_to_records.get(nlp_extract.attributed)

            if vsdb_records is None:
                continue

            # Make a copy of the harvest article, so that it doesn't override one another
            _harvest_article = harvest_article | {
                "speechtype_id": (
                    speechtype_ref.get(nlp_extract.classification)
                    if speechtype_ref.get(nlp_extract.classification) is not None
                    else speechtype_ref.get("Other")
                ),
                "speechtext": nlp_extract.text,
            }

            _harvest_article["candidate_ids"] = []

            # Applying name match to the matching name records
            for record in vsdb_records:
                review_dict = {}
                if record["match_status"] == "REVIEW":
                    review_dict.update(
                        {
                            "review": True,
                            "review_msg": "This candidate may not have said this.",
                        }
                    )
                # One statement may be attributed to multiple candidates,
                # when there is ambiguity in the matches
                elif record["match_status"] == "AMBIGUOUS":
                    review_dict.update(
                        {
                            "review": True,
                            "review_msg": "The text may have been spoken by another candidate",
                        }
                    )

                candidate_id = record["candidate_id"]
                _harvest_article["candidate_ids"].append(candidate_id)

                harvests_by_candidates[candidate_id].append(
                    _harvest_article | review_dict
                )

        # Treats each speechtext by speechtype as a separate entry
        for _, harvests in harvests_by_candidates.items():
            harvest_by_speechtype = defaultdict(lambda: harvest_article)

            # Group and combine the text by speechtype_ids
            for h in harvests:
                st_id = h.get("speechtype_id")
                if st_id not in harvest_by_speechtype:
                    harvest_by_speechtype[st_id] = h
                else:
                    harvest_by_speechtype[st_id]["speechtext"] += "\n\n" + h.get(
                        "speechtext"
                    )

            # Finally, assign each harvest dict their ids
            for speechtype_id, harvest in harvest_by_speechtype.items():
                harvest |= {
                    "speechtype_id": speechtype_id,
                }
                yield harvest
