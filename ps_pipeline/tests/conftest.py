import os
import json
from pathlib import Path

import pytest
import spacy
from dotenv import load_dotenv
from unidecode import unidecode

from ps_pipeline.transform import pipe as t_pipe
from ps_pipeline.json_model import Articles


load_dotenv()


def read_extract_file(candidate_id):
    data_directory = Path(os.getenv("DATA_FILES_DIRECTORY"))

    extract_path = data_directory / str(candidate_id) / "EXTRACT_FILES"
    extract_files = filter(lambda f: f.name.endswith(".json"), extract_path.iterdir())

    data = []

    for file in sorted(extract_files, key=lambda f: f.stat().st_mtime):
        with open(file, "r", encoding="utf-8") as f:
            data += json.load(f)

    articles = Articles(data)
    source_to_texts = {(candidate_id, a.url): a.text for a in articles.all}

    return source_to_texts


def read_test_data(filename):
    data_directory = Path(__file__).parent / "data"

    test_data_path = data_directory / filename

    with open(test_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_to_expected = {(d["candidate_id"], d["source"]): d["expected"] for d in data}

    return source_to_expected


def docs_to_expected_test_data(test_data: dict, nlp):

    docs_to_expected = []
    candidate_to_extract = {}

    for (candidate_id, source), expected in test_data.items():
        if candidate_id not in candidate_to_extract:
            extract_data = read_extract_file(candidate_id)
            candidate_to_extract[candidate_id] = extract_data
        else:
            extract_data = candidate_to_extract[candidate_id]

        doc = nlp(unidecode(extract_data[(candidate_id, source)]))
        docs_to_expected.append(((candidate_id, source, doc), expected))

    return docs_to_expected


@pytest.fixture(scope="module")
def nlp_attributed_statements():
    t_pipe.nlp_articles.register()
    t_pipe.nlp_attributed_statements.register()

    nlp_model = spacy.load("en_core_web_trf")
    nlp_model.add_pipe("sentencizer", before="parser")
    nlp_model.add_pipe("set_midquote_as_combined_sentence", after="sentencizer")
    nlp_model.add_pipe(
        "set_newline_as_sentence_start", after="set_midquote_as_combined_sentence"
    )
    return nlp_model


@pytest.fixture(scope="module")
def expected_attributed_statements():
    return read_test_data("attributed_statements.json")


@pytest.fixture(scope="module")
def docs_to_expected_attributed_statements(
    expected_attributed_statements, nlp_attributed_statements
):
    return docs_to_expected_test_data(
        expected_attributed_statements, nlp_attributed_statements
    )


def main():
    test_data = read_test_data("attributed_statements.json")

    t_pipe.nlp_articles.register()
    t_pipe.nlp_attributed_statements.register()

    nlp_model = spacy.load("en_core_web_trf")
    nlp_model.add_pipe("sentencizer", before="parser")
    nlp_model.add_pipe("set_midquote_as_combined_sentence", after="sentencizer")
    nlp_model.add_pipe(
        "set_newline_as_sentence_start", after="set_midquote_as_combined_sentence"
    )

    docs_to_expected = docs_to_expected_test_data(test_data, nlp_model)


if __name__ == "__main__":
    main()
