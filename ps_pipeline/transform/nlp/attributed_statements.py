# External packages and libraries
from spacy.tokens import Doc, Span
from ps_pipeline.transform.nlp import articles as nlp_articles


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


def doc_attributive_spans(doc) -> list[dict]:
    """
    attributive_spans =
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
    attributed_to = None
    related_spans = []
    attributed_spans = []

    def reset():
        nonlocal related_spans, attributed_to
        if attributed_to:
            attributed_spans.append(
                {"attributed": attributed_to, "spans": related_spans.copy()}
            )
        attributed_to = None
        related_spans.clear()

    for s in doc.sents:
        _attributed_to = s._.attributed_to
        s._.to_replace.update(set(s._.start_quotes))
        s._.to_replace.update(set(s._.end_quotes))
        # Check if related_sentences exists to prevent a key-error
        if related_spans and s._.is_right_after(related_spans[-1]):
            if _attributed_to:
                if attributed_to and attributed_to != _attributed_to:
                    reset()
                attributed_to = _attributed_to
                related_spans.append(s)
            elif any(s._.start_quotes):
                if not attributed_to:
                    # Since an open quote should only exist as first in the
                    # related sentence list, having it when there are no attributed_to
                    # would not be considered related, hence resetting it.
                    reset()
                related_spans.append(s)
            elif any(s._.end_quotes):
                related_spans.append(s)
                reset()  # Having an end quoted most likely ends the relation.
            else:
                # Sentences with no open or end quote are subject to
                # related sentences if the following are true:
                #   i) One of the current related sentences is attributed (person!=None)
                #  ii) None of the current related sentences contains an end quote (which
                #      is already taken care of above)
                # iii) Sentence immediately before the current sentence is attributed
                if attributed_to:
                    related_spans.append(s)
        else:
            reset()  # Makes sure that it would be the first of the related sentences
            if _attributed_to:
                attributed_to = _attributed_to
                related_spans.append(s)
            elif any(s._.start_quotes):
                related_spans.append(s)

    return attributed_spans


def register():
    # Span Extensions (Methods)
    Span.set_extension("clean_attributed", method=span_clean_attributed, force=True)

    if not Span.has_extension("dist"):
        Span.set_extension("dist", method=nlp_articles.span_distance)
    if not Span.has_extension("find_all"):
        Span.set_extension("find_all", method=nlp_articles.span_find_all)
    if not Span.has_extension("is_right_after"):
        Span.set_extension("is_right_after", method=nlp_articles.span_is_right_after)

    # Span Extensions (Properties)
    if not Span.has_extension("persons"):
        Span.set_extension("persons", getter=nlp_articles.span_persons)
    if not Span.has_extension("locations"):
        Span.set_extension("locations", getter=nlp_articles.span_locations)

    Span.set_extension("attributive_tags", getter=span_attributive_tags, force=True)
    Span.set_extension("start_quotes", getter=span_start_quotes, force=True)
    Span.set_extension("mid_quotes", getter=span_mid_quotes, force=True)
    Span.set_extension("end_quotes", getter=span_end_quotes, force=True)
    Span.set_extension("attributed_to", getter=span_attributed_to, force=True)
    Span.set_extension("to_replace", default=set(), force=True)

    # Doc Extensions
    Doc.set_extension("attributive_spans", getter=doc_attributive_spans, force=True)


def deregister():
    Span.remove_extension("clean_attributed")
    Span.remove_extension("attributive_tags")
    Span.remove_extension("start_quotes")
    Span.remove_extension("mid_quotes")
    Span.remove_extension("end_quotes")
    Span.remove_extension("attributed_to")
    Span.remove_extension("to_replace")
