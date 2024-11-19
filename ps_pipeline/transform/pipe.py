"""
General logic for the loading pipeline, matching persons and harvest file creation.
"""

__author__ = "Johanan Tai"

import re
from datetime import datetime
from dateutil.parser import parse as datetimeparse

# External packages and libraries
import spacy
from unidecode import unidecode as asciify

from ps_pipeline.transform.nlp import (
    attributed_statements as nlp_attributed_statements,
    articles as nlp_articles,
)
from ps_pipeline.json_model import Articles


datetime_ISO = re.compile(
    r"^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:[\-\+]\d{2}:\d{2}|Z)?)?$"
)
mm_dd_yyyy = re.compile(r"(?P<m>\d{2})[\/|-|\.](?P<d>\d{2})[\/|-|\.](?P<Y>\d{4})")
mm_dd_yy = re.compile(r"(?P<m>\d{2})[\/|-|\.](?P<d>\d{2})[\/|-|\.](?P<y>\d{2})")
month_dd_yyyy = re.compile(
    r"(?P<B>[A-Za-z]{4,})\s+(?P<d>\d{2})(?:,\s*|\s+)(?P<Y>\d{4})"
)
smonth_dd_yyyy = re.compile(
    r"(?P<b>[A-Za-z]{3})\s+(?P<d>\d{2})(?:,\s*|\s+)(?P<Y>\d{4})"
)


def transform_date(text):

    patterns = {
        0: datetime_ISO,
        1: mm_dd_yyyy,
        2: mm_dd_yy,
        3: month_dd_yyyy,
        4: smonth_dd_yyyy,
    }
    # use finditer for date since they might be embedded within text

    for i, p in patterns.items():
        matched = list(p.finditer(text))
        for result in matched:
            if i == 0 and p.fullmatch(text):
                return str(datetime.fromisoformat(text))
            else:
                d = result.groupdict()
                params = " ".join([f"%{k}" for k in d if d[k]])
                values = " ".join([v for v in d.values() if v])
                return str(datetime.strptime(values, params))

    return text


def replace_str_by_position(original, replacements: list[tuple[tuple[int, int], str]]):
    """
    replacement: (start_char, end_char, replace_with)

    """

    modified_strings = []
    last_position = 0

    # replacements have to be sorted in order to work correctly
    for start_char, end_char, replacement in sorted(replacements):

        modified_string = (
            replacement
            if start_char == 0
            else original[last_position:start_char] + replacement
        )
        if not replacement:
            modified_strings.append(modified_string.rstrip())
        else:
            modified_strings.append(modified_string)

        last_position = end_char

    modified_strings.append(original[last_position:])
    return "".join(modified_strings)


def extract_attributive_statements(doc):

    nlp_attributed_statements.register()

    statements = []

    for d in doc._.attributive_spans:
        cleaned_texts = []
        for span in d["spans"]:
            # A sorted to_replace is needed due to span._.to_replace being a set
            to_replace = []

            for tr_span, replace_text in span._.to_replace:
                start_char = tr_span.start_char - span.start_char
                end_char = tr_span.end_char - span.start_char

                to_replace.append((start_char, end_char, replace_text))

            cleaned_texts.append(
                replace_str_by_position(span.text, sorted(to_replace)).strip()
            )

        cleaned_joined = " ".join(cleaned_texts).strip().strip('"')
        statements.append(
            {
                "attributed": d["attributed"].text,
                "text": f'"{cleaned_joined}"',
                "text_type": "attributive_statements",
            }
        )
    return statements


def transform_json(articles: Articles):

    nlp = spacy.load("en_core_web_trf")

    nlp_articles.register()

    nlp.add_pipe("set_newline_as_sentence_start", before="parser")
    nlp.add_pipe("set_midquote_as_combined_sentence", before="parser")

    for article in articles:

        asciified_text = asciify(article.text)
        doc = nlp(asciified_text)

        data = {
            # Unidecode asciifies the text
            "article_title": asciify(article.title),
            "article_timestamp": str(datetimeparse(article.timestamp)),
            "article_url": article.url,
            "article_text": asciified_text,
            "publish_location": (
                article.publish_location
                if article.publish_location
                else doc._.publish_location
            ),
            "statements": extract_attributive_statements(doc),
        }

        yield data
