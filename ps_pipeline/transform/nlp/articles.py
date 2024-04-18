import re
from spacy.tokens import Doc, Span


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


def doc_publish_location(doc):
    # Location Criteria:
    # 1) Has to be a starting token of the sentence
    # 2) At least one GPE token followed by a dash
    location_pattern = re.compile(r"(?P<location>[A-Za-z]{2,}\,?\s?[A-Za-z\.?]+)\s+-+")

    for span in doc.sents:
        for token_pos in span._.locations:
            if token_pos.start == span.start:
                results = re.finditer(location_pattern, span.text)
                # If the result shows that the location matched is
                # at the start of the sentence, return it otherwise None
                for m in results:
                    if m.start() == span.start:
                        return m.group("location")

    return "Unknown"


def register():
    Span.set_extension("persons", getter=span_persons)
    Span.set_extension("locations", getter=span_locations)

    Span.set_extension("dist", method=span_distance)
    Span.set_extension("find_all", method=span_find_all)
    Span.set_extension("is_right_after", method=span_is_right_after)

    Doc.set_extension("publish_location", getter=doc_publish_location, force=True)


def deregister():
    Span.remove_extension("persons")
    Span.remove_extension("locations")
    Span.remove_extension("dist")
    Span.remove_extension("find_all")
    Span.remove_extension("is_right_after")
