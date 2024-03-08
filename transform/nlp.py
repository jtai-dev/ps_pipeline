# Built-ins
import re

# External packages and libraries
from spacy.tokens import Doc, Span


ATTRIBUTIVE_TAGS = [
    "announce",
    "say",
    "declare",
    "affirm",
    "explain",
    "assert",
    "state",
    "express",
    "mention",
    "add",
    "clarify",
    "comment",
    "communicate",
    "quote",
    "report",
    "observe",
    "remark",
    "reaffirm",
    "recite",
    "request",
    "respond",
    "share",
    "suggest",
    "invite",
    "read",
    "predict",
    "relate",
    "outline",
    "elaborate",
    "propose",
    "articulate",
    "highlight",
    "imply",
    "indicate",
    "inquire",
    "greet",
    "voice",
    "enunciate",
    "expound",
    "quote",
    "remark",
    "repeat",
    "reply",
    "speculate",
    "convey",
    "acknowledge",
    "insist",
    "ask",
    "quiz",
    "query",
]


def span_find_all(span, to_find, pattern=False):
    to_find = re.escape(to_find) if not pattern else to_find
    for m in re.finditer(to_find, span.text):
        found = span.char_span(m.start(), m.end())
        if found:
            yield span.doc[found.start : found.end]


def span_is_right_after(span, target_span):
    if (
        span > target_span
        and
        # To account for whitespace
        0 <= span.start - target_span.end < 2
        and "\n" not in span[:2].text
        and "\n" not in target_span[-2:].text
    ):
        return True
    return False


def span_distance(span, target_span) -> int:
    if span > target_span:
        product = span.start - target_span.end
    else:
        product = target_span.start - span.end
    return product if product >= 0 else -1


def span_persons(span):
    for s in span.ents:
        if s.label_ == "PERSON":
            # Returns a new span instance that does not change the label from ents
            yield s.doc.char_span(s.start_char, s.end_char, label="person")


def span_locations(span):
    for s in span.ents:
        if s.label_ == "GPE":
            # Returns a new span instance that does not change the label from ents
            yield s.doc.char_span(s.start_char, s.end_char, label="location")


def span_attributive_tags(span):
    for token in span:
        if token.lemma_ in ATTRIBUTIVE_TAGS:
            yield span.doc.char_span(
                token.idx, token.idx + len(token), label="attributive_tag"
            )


def span_start_quotes(span):
    for s in span[:2]._.find_all('"'):
        yield s.doc.char_span(s.start_char, s.end_char, label="start_quote")


def span_mid_quotes(span):
    for s in span[2:-2]._.find_all(r"[\,|\:|\s]+\"+", pattern=True):
        yield s.doc.char_span(s.start_char, s.end_char, label="mid_quote")


def span_end_quotes(span):
    for s in span[-2:]._.find_all('"'):
        yield s.doc.char_span(s.start_char, s.end_char, label="end_quote")


def span_clean_attributed(span, mq_pos, order):
    if order.startswith("start_attributed"):
        span._.to_replace.add(span.doc.char_span(span.start_char, mq_pos))
    elif order.startswith("end_attributed"):
        if (
            span.end > 0
            and span.char_span(-2, -1)
            and span.char_span(-2, -1).text == "."
        ):
            span._.to_replace.add(span.doc.char_span(mq_pos, span.end_char - 1))
        else:
            span._.to_replace.add(span.doc.char_span(mq_pos, span.end_char))


def span_attributed_to(span):
    if not (
        any(span._.mid_quotes) and any(span._.persons) and any(span._.attributive_tags)
    ):
        return
    spans = sorted(
        list(span._.persons) + list(span._.attributive_tags) + list(span._.mid_quotes)
    )
    persons = []
    for i in range(len(spans) - 2):
        # End Attributed (Tag First)
        if (
            spans[i].label_ == "mid_quote"
            and spans[i + 1].label_ == "attributive_tag"
            and spans[i + 2].label_ == "person"
            and 0 <= spans[i + 1]._.dist(spans[i + 2]) <= 2
        ):
            span._.clean_attributed(spans[i].start_char, "end_attributed_tfirst")
            persons.append(spans[i + 2])
        # End Attributed (Person First)
        if (
            spans[i].label_ == "mid_quote"
            and spans[i + 1].label_ == "person"
            and spans[i + 2].label_ == "attributive_tag"
            and 0 <= spans[i + 1]._.dist(spans[i + 2]) <= 3
        ):
            span._.clean_attributed(spans[i].start_char, "end_attributed_pfirst")
            persons.append(spans[i + 1])
        # Start Attributed
        if (
            spans[i].label_ == "person"
            and spans[i + 1].label_ == "attributive_tag"
            and spans[i + 2].label_ == "mid_quote"
            and 0 <= spans[i + 1]._.dist(spans[i]) <= 2
        ):
            span._.clean_attributed(spans[i + 2].start_char, "start_attributed")
            persons.append(spans[i])
    if len(persons) == 1:
        return persons.pop()


# Span Extensions (Methods)
Span.set_extension("dist", method=span_distance, force=True)
Span.set_extension("find_all", method=span_find_all, force=True)
Span.set_extension("is_right_after", method=span_is_right_after, force=True)
Span.set_extension("clean_attributed", method=span_clean_attributed, force=True)
# Span Extensions (Properties)
Span.set_extension("persons", getter=span_persons, force=True)
Span.set_extension("locations", getter=span_locations, force=True)
Span.set_extension("attributive_tags", getter=span_attributive_tags, force=True)
Span.set_extension("start_quotes", getter=span_start_quotes, force=True)
Span.set_extension("mid_quotes", getter=span_mid_quotes, force=True)
Span.set_extension("end_quotes", getter=span_end_quotes, force=True)
Span.set_extension("attributed_to", getter=span_attributed_to, force=True)
Span.set_extension("to_replace", default=set(), force=True)


def str_replace_by_position(original, replacements: list[tuple]):
    modified_strings = []
    last_position = 0
    for start, end, replacement in replacements:
        modified_string = (
            replacement if start == 0 else original[last_position:start] + replacement
        )
        if not replacement:
            modified_strings.append(modified_string.rstrip())
        else:
            modified_strings.append(modified_string)
        last_position = end
    modified_strings.append(original[last_position:])
    return "".join(modified_strings)


def doc_attributed_sentences(doc) -> list[dict]:
    """
    attributed_sentences =
    [
        {
            attributed: ...
            spans: [span_1, span_2, ...]
        },
        {
            attributed: ...
            spans: [span_3, span_4, ...]
        },
        ...
    ]
    """
    attributed_person = None
    related_sentences = []
    attributed_sentences = []

    def reset():
        nonlocal related_sentences, attributed_person
        if attributed_person:
            attributed_sentences.append(
                {"attributed": attributed_person, "sentences": related_sentences.copy()}
            )
        attributed_person = None
        related_sentences.clear()

    for s in doc.sents:
        attributed_to = s._.attributed_to
        s._.to_replace.update(set(s._.start_quotes))
        s._.to_replace.update(set(s._.end_quotes))
        # Check if related_sentences exists to prevent a key-error
        if related_sentences and s._.is_right_after(related_sentences[-1]):
            if attributed_to:
                if attributed_person and attributed_person != attributed_to:
                    reset()
                attributed_person = attributed_to
                related_sentences.append(s)
            elif any(s._.start_quotes):
                if not attributed_person:
                    # Since an open quote should only exist as first in the
                    # related sentence list, having it when there are no attributed_to
                    # would not be considered related, hence resetting it.
                    reset()
                related_sentences.append(s)
            elif any(s._.end_quotes):
                related_sentences.append(s)
                reset()  # Having an end quoted most likely ends the relation.
            else:
                # Sentences with no open or end quote are subject to
                # related sentences if the following are true:
                #   i) One of the current related sentences is attributed (person!=None)
                #  ii) None of the current related sentences contains an end quote (which
                #      is already taken care of above)
                # iii) Sentence immediately before the current sentence is attributed
                if attributed_person:
                    related_sentences.append(s)
        else:
            reset()  # Makes sure that it would be the first of the related sentences
            if attributed_to:
                attributed_person = attributed_to
                related_sentences.append(s)
            elif any(s._.start_quotes):
                related_sentences.append(s)
    return attributed_sentences


def doc_attributed_statements(doc):
    """
    attributed_statements =
    [
        {
            'attributed': [...]
            'text': ...
        },
        {
            'attributed': [...]
            'text': ...
        }
        ...
    ]
    """
    attributed_statements = []
    for d in doc._.attributed_sentences:
        cleaned_texts = []
        for span in d["sentences"]:
            to_replace = []
            for tr in span._.to_replace:
                start = tr.start_char - span.start_char
                end = tr.end_char - span.start_char
                to_replace.append((start, end, ""))
            cleaned_texts.append(str_replace_by_position(span.text, to_replace))
        attributed_statements.append(
            {
                "attributed": d["attributed"], 
                "text": " ".join(cleaned_texts)
             }
        )
    return attributed_statements


def doc_publish_location(doc):
    # Location Criteria:
    # 1) Has to be a starting token of the sentence
    # 2) At least one GPE token followed by a dash
    location_pattern = re.compile(r"(?P<location>[A-Za-z]{2,}\,?\s?[A-Za-z\.?]+)\s+-+")

    for sentence in doc.sents:
        for token_pos in sentence._.locations:
            if token_pos.start == sentence.start:
                results = re.finditer(location_pattern, sentence.text)
                # If the result shows that the location matched is
                # at the start of the sentence, return it otherwise None
                for m in results:
                    if m.start() == sentence.start:
                        return m.group("location")

    return "Unknown"


# Doc Extensions
Doc.set_extension("publish_location", getter=doc_publish_location, force=True)
Doc.set_extension("attributed_sentences", getter=doc_attributed_sentences, force=True)
Doc.set_extension("attributed_statements", getter=doc_attributed_statements, force=True)
