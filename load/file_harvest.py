import json
import pg8000

from pathlib import Path

from collections import defaultdict
from datetime import datetime

if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

from json_model import CondensedHarvests


def insert_into_speech(cursor: pg8000.Cursor, *values):
    cursor.execute(
        "INSERT INTO speech (speechtype_id, title, speechdate, location, speechtext, url, created)"
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        "RETURNING speech_id",
        values),

    return cursor.fetchone()


def insert_into_speech_candidate(cursor: pg8000.Cursor, *values):

    cursor.execute(
        "INSERT INTO speech_candidate (speech_id, candidate_id, created)"
        "VALUES (%s, %s, %s)"
        "RETURNING speech_candidate_id",
        values)

    return cursor.fetchone()


def main(harvest_json: CondensedHarvests):

    connection = pg8000.connect(host='localhost',
                                port='5432',
                                database='test_pvs',
                                user='jtai')

    cursor = connection.cursor()

    speech_to_candidate = defaultdict(set)

    for harvest in harvest_json.all:
        speech_id = insert_into_speech(cursor,
                                       harvest.speechtype_id,
                                       harvest.title,
                                       harvest.speechdate,
                                       harvest.location,
                                       harvest.speechtext if harvest.speechtext else "",
                                       harvest.url,
                                       str(datetime.now()))[0]
        speech_to_candidate[speech_id].add(harvest.candidate_id)

    speech_candidate_ids = set()

    for speech_id, candidate_ids in speech_to_candidate.items():
        for candidate_id in candidate_ids:
            speech_candidate_ids.update(insert_into_speech_candidate(cursor,
                                                                     speech_id,
                                                                     candidate_id,
                                                                     str(datetime.now())))

    connection.commit()

    return speech_candidate_ids


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(prog='ps_automation_harvest')
    parser.add_argument('filepath')

    args = parser.parse_args()

    working_dir = Path(args.filepath).parent.parent
    with open(Path(args.filepath), 'r') as f:
        harvest_json = CondensedHarvests(json.load(f))
    main(harvest_json)
