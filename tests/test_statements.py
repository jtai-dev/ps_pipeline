import pytest
import spacy
import json
from pathlib import Path
from unidecode import unidecode
from transform.nlp import doc_attributed_sentences, Doc, Span


@pytest.fixture
def json_statements():
    fp = Path('data/statements.json')
    with open(fp, 'r') as f:
        data = json.load(f)
    return data


@pytest.fixture
def full_expected(nlp, json_statements):
    nlp = spacy.load('en_core_web_trf')

    for js in json_statements:
        doc = nlp(unidecode(js['full']))
        yield doc, js['expected']
        

def get_attributed_statements(full_expected):

    for doc, expected in full_expected:
        statements = doc_attributed_sentences(doc)

        for person, sentences in statements.items():
            assert person == expected['attributed']

            for spans in sentences.values():
                combined_span = doc[spans[0].start: spans[-1].end]
                assert combined_span.text == expected['text']
            
            