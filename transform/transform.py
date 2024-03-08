
import sys
import json
from pathlib import Path
from dateutil.parser import parse as datetimeparser


import spacy
from spacy.language import Language
from tqdm import tqdm
from unidecode import unidecode

if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Importing the modified Doc and Span classes (ignore greyed out)
from transform.nlp import Doc, Span
from json_model import Articles, TransformedArticles


"""
TRANSFORM JSON MODEL:
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
    ]
    
    }
"""

def pipe(articlejson:Articles):
    
    @Language.component("set_custom_boundaries")
    def _set_custom_boundaries(doc):
        for token in doc[:-1]:
                if token.text == '\n':
                        doc[token.i + 1].is_sent_start = True
        return doc

    nlp = spacy.load('en_core_web_trf')
    nlp.add_pipe("set_custom_boundaries", before="parser")

    data = []

    for record in tqdm(articlejson.all, desc='Processing...'):
        asciified_text = unidecode(record.text)
        doc = nlp(asciified_text)

        data.append({
            'article_title': unidecode(record.title),
            'article_timestamp': str(datetimeparser(record.timestamp)),
            'article_url': record.url,
            'article_text': asciified_text,
            'publish_location': record.publish_location if record.publish_location else doc._.publish_location,
            'statements': doc._.attributed_statements,
            # 'letters': None,
            # 'speech': None,
            # 'interview': None,
        })

    return TransformedArticles(data)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(prog='ps_automation_transform')
    parser.add_argument('filepath')

    args = parser.parse_args()

    working_dir = Path(args.filepath).parent.parent

    with open(Path(args.filepath), 'r') as f:
        articlejson = Articles(json.load(f))

    transformed = pipe(articlejson)
    transformed.save('transformed', working_dir / 'TRANSFORMED_FILES')