# External packages and libraries
import re
from spacy.language import Language
from spacy.tokens import Doc, Span
from ps_pipeline.transform.nlp import articles as nlp_articles


ATTRIBUTIVE_TAGS = [
    "announce",
    "say",
    "tell",
    "continue",
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
    "warn",
]

# Having an optional punctuation is to account for slight grammar errors in
# the text.
MID_QUOTE_PAT = r"[,:\?\!\s]?\s?\""


def span_attributive_tags(span):
    for token in span:
        if token.lemma_ in ATTRIBUTIVE_TAGS and token.pos_ == "VERB":
            yield span.doc.char_span(
                token.idx, token.idx + len(token), label="attributive_tag"
            )


def span_start_quotes(span):
    # NOTE: Even though this is technically looking at the start of the span,
    # it might be treated as an end quote if the quote is in a span with
    # less than or equal to 3 tokens.
    for s in span[:2]._.find_all('"'):
        yield s.doc.char_span(s.start_char, s.end_char, label="start_quote")


def span_mid_quotes(span):
    # NOTE: Even though this is technically looking for quotes in the middle of a span,
    # it might be treated as a start or end quote if the quote is in a span with
    # less than or equal to 3 tokens.

    # The current version of midquote has an optional space between a char and
    # the quote.
    for s in span[2:-2]._.find_all(MID_QUOTE_PAT, is_pat=True):
        yield s.doc.char_span(s.start_char, s.end_char, label="mid_quote")


def span_end_quotes(span):
    # NOTE: Even though this is technically looking at the end of the span,
    # it might be treated as a start quote if the quote is in a span with
    # less than or equal to 3 tokens.
    for s in span[-2:]._.find_all('"'):
        yield s.doc.char_span(s.start_char, s.end_char, label="end_quote")


def span_clean_attributed(span, to_from_pos, order) -> tuple[tuple, str]:
    if order.startswith("start_attributed"):
        span._.to_replace.add((span.doc.char_span(span.start_char, to_from_pos), ""))
    elif order.startswith("end_attributed"):
        # .char_span returns None if not found at position
        if span.end_char > 0 and "." in span.text[-2:]:
            # setting alignment_mode="expand" will return whatever possible string that is
            # covered till the end, default="strict" which will return None when it is not
            # within boundaries of token's start or end.
            span._.to_replace.add(
                (
                    span.doc.char_span(
                        to_from_pos, span.end_char - 1, alignment_mode="expand"
                    ),
                    "",
                )
            )
        else:
            span._.to_replace.add((span.doc.char_span(to_from_pos, span.end_char), "."))


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
            and 0 <= spans[i]._.dist(spans[i + 1]) <= 1
        ):
            span._.clean_attributed(spans[i].start_char, "end_attributed_tfirst")
            persons.append(spans[i + 2])
        # End Attributed (Person First)
        if (
            spans[i].label_ == "mid_quote"
            and spans[i + 1].label_ == "person"
            and spans[i + 2].label_ == "attributive_tag"
            and (
                0 <= spans[i]._.dist(spans[i + 1]) <= 1
                # Attributive tag should not appear too far from the end to be
                # grammatically correct
                or 0 <= spans[i + 2]._.dist(span[-1:]) <= 2
            )
        ):
            span._.clean_attributed(spans[i].start_char, "end_attributed_pfirst")
            persons.append(spans[i + 1])
        # Start Attributed
        if (
            spans[i].label_ == "person"
            and spans[i + 1].label_ == "attributive_tag"
            and spans[i + 2].label_ == "mid_quote"
            and 0 <= spans[i + 1]._.dist(spans[i + 2]) <= 1
        ):
            span._.clean_attributed(spans[i + 2].end_char, "start_attributed")
            persons.append(spans[i])

    if len(persons) == 1:
        return persons.pop()


@Language.component("set_midquote_as_combined_sentence")
def _set_midquote_as_combined_sentence(doc):
    """Dependent on span._.find_all extension"""
    count = 0
    while count < len(doc) - 2:

        span = doc[count : count + 2]
        found = list(span._.find_all(MID_QUOTE_PAT, is_pat=True))

        if not found:
            count += 1
            continue

        for f in found:
            # Makes sure that the quote precedes with a punctuation
            # according to the midquote pattern
            if len(f.text) > 1:
                doc[f.start].is_sent_start = False
                doc[f.end].is_sent_start = False
                count += 2
            else:
                # print(doc[f.start-1])
                if doc[f.start - 1].text == ".":
                    # print(span)
                    if (
                        f.start > 0
                        and f.end < len(doc) - 1
                        and re.match(r"^.\s{1}.$", doc[f.start - 1 : f.end].text)
                    ):
                        doc[f.start].is_sent_start = True
                        doc[f.end].is_sent_start = False
                    else:
                        doc[f.start].is_sent_start = False
                        doc[f.end].is_sent_start = True
                else:
                    doc[f.start].is_sent_start = None
            count += 1

    return doc


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
        _start_quotes = list(s._.start_quotes)
        _end_quotes = list(s._.end_quotes)
        _mid_quotes = list(s._.mid_quotes)
        s._.to_replace.update({(sq, "") for sq in s._.start_quotes})
        s._.to_replace.update({(eq, "") for eq in s._.end_quotes})
        if len(related_spans) > 0 and s._.is_right_after(related_spans[-1]):
            if _attributed_to:
                if attributed_to and attributed_to != _attributed_to:
                    reset()
                attributed_to = _attributed_to
                related_spans.append(s)
            # Some sentences do end on the same line.
            elif any(_start_quotes) and any(_end_quotes):
                related_spans.append(s)
                reset()
            elif any(_start_quotes):
                if not attributed_to:
                    # An open quote should only exist as the first span in the
                    # related spans list. appending it **while there is no attributed_to**
                    # is likely not related to the previous spans, hence resetting it.
                    reset()
                related_spans.append(s)
            elif any(_end_quotes):
                related_spans.append(s)
                # Having an end quoted ends the related sentence.
                reset()
            else:
                related_spans.append(s)
        else:
            # Make sure that this sentence is the first of the related sentence
            reset()
            if _attributed_to:
                # This takes care of statements like this: `Schumer explained that "swatting"`
                if len(_mid_quotes) > 1 and not (
                    any(_start_quotes) or any(_end_quotes)
                ):
                    continue
                attributed_to = _attributed_to
                related_spans.append(s)
            # Some sentences do end on the same line.
            elif any(_start_quotes) and any(_end_quotes):
                related_spans.append(s)
                reset()
            elif any(_start_quotes):
                related_spans.append(s)
            else:
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
