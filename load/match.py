# Built-ins
import json
from pathlib import Path

# External Packages & Libraries
import pg8000
from rapidfuzz import fuzz

# Internal Packages & Libraries
if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

from json_model import TransformedArticles
from tabular_matcher.tabular_matcher.matcher import TabularMatcher


def connect_to_database():
    PACKAGE_DIR = Path(__file__).parent.parent
    CONNECTION_INFO_FILEPATH = PACKAGE_DIR / 'connection_info.json'

    with open(CONNECTION_INFO_FILEPATH, 'r') as f:
        connection_info = json.load(f)

    return pg8000.connect(**connection_info, timeout=10)


def query_from_database(query: str, connection: pg8000.Connection):
    cursor = connection.cursor()
    cursor.execute(query)
    headers = [str(k[0]) for k in cursor.description]
    return {index: dict(zip(headers, row)) for index, row in enumerate(cursor.fetchall())}


def load_query_string(query_filename: Path):
    PACKAGE_DIR = Path(__file__).parent
    with open(PACKAGE_DIR / 'queries' / query_filename, 'r') as f:
        query_string = f.read()

    return query_string


def get_names(transformed_json: TransformedArticles):
    set_of_names = set()

    for record in transformed_json.all:

        for statement in record.statements.all:
            set_of_names.update(statement.attributed)

    return {i: {'name': name} for i, name in enumerate(set_of_names)}


def match(names, queryset):

    tb_matcher = TabularMatcher()
    tb_matcher.x_records = names
    tb_matcher.y_records = queryset

    tb_config = tb_matcher.config

    tb_config.scorers_by_column.SCORERS.update({
        'token_set_ratio': lambda x, y: fuzz.token_set_ratio(str(x).lower(), str(y.lower()))
    })
    tb_config.scorers_by_column.default = 'token_set_ratio'
    tb_config.thresholds_by_column.default = 85

    tb_config.populate()

    tb_config.columns_to_match['name'] = 'candidate_name'
    tb_config.columns_to_get['candidate_id'] = 'candidate_id'
    tb_config.columns_to_get['candidate_name'] = 'candidate_name'

    tb_matcher.required_threshold = 75
    tb_matcher.duplicate_threshold = 100

    records_matched, _ = tb_matcher.match()

    for record in records_matched.values():
        record['candidate_id'] = [record['candidate_id']] if record['candidate_id'] else []
        record['candidate_name'] = [record['candidate_name']] if record['candidate_name'] else []
        
        if record['match_status'] == 'AMBIGUOUS':
            for i in record['row(s)_matched'].split(','):
                record['candidate_id'].append(queryset[int(i.strip())]['candidate_id'])
                record['candidate_name'].append(queryset[int(i.strip())]['candidate_name'])

    for k,v in records_matched.items():
        print(k,v)

    return {record['name']: record for record in records_matched.values()}


def main(articlejson):

    vs_db_connection = connect_to_database()
    query = load_query_string('office-candidates-active.sql')
    records_query = query_from_database(query, vs_db_connection)

    return match(get_names(articlejson), records_query)
