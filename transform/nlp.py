
# Built-ins
import re
from collections import defaultdict, namedtuple

# External packages and libraries
from spacy.tokens import Doc, Span


ATTRIBUTIVE_TAGS = ['announce', 'say', 'declare', 'affirm', 'explain', 'assert', 'state', 'express', 'mention', 'add', 'clarify', 'comment',
                    'communicate', 'quote', 'report', 'observe', 'remark', 'reaffirm', 'recite', 'request', 'respond', 'share', 'suggest',
                    'invite', 'read', 'predict', 'relate', 'outline', 'elaborate', 'propose', 'articulate', 'highlight', 'imply', 'indicate',
                    'inquire', 'greet', 'voice', 'enunciate', 'expound', 'quote', 'remark', 'repeat', 'reply', 'speculate', 'convey',
                    'acknowledge', 'insist', 'ask', 'quiz', 'query']


def span_find_all(span, to_find, pattern=False):
    to_find = re.escape(to_find) if not pattern else to_find
    for m in re.finditer(to_find, span.text):
        found = span.char_span(m.start(), m.end())
        if found:
            yield span.doc[found.start:found.end]


def span_is_right_after(span, target_span):
    if (span > target_span and
        # To account for whitespace
        0 <= span.start - target_span.end < 2 and
        '\n' not in span[:2].text and
        '\n' not in target_span[-2:].text
        ):
        return True
    return False


def span_distance(span, target_span) -> int:
    if span > target_span:
        product = span.start - target_span.end
        return product if product >= 0 else -1
    else:
        return abs(product) if product <= 0 else -1


def span_persons(span):
    for s in span.ents:
        if s.label_ == 'PERSON':
            # Returns a new span instance that does not change the label from ents
            yield s.doc.char_span(s.start_char, s.end_char, label='person')


def span_locations(span):
    for s in span.ents:
        if s.label_ == 'GPE':
            # Returns a new span instance that does not change the label from ents
            yield s.doc.char_span(s.start_char, s.end_char, label='location')


def span_attributive_tags(span):
    for token in span:
        if token.lemma_ in ATTRIBUTIVE_TAGS:
            yield span.doc.char_span(token.idx, token.idx+len(token), label='attributive_tag')


def span_start_quotes(span):
    for s in span[:2]._.find_all('"'):
        yield s.doc.char_span(s.start_char, s.end_char, label='start_quote')


def span_mid_quotes(span):
    for s in span[2:-2]._.find_all(r"[\,|\:|\s]+\"+", pattern=True):
        yield s.doc.char_span(s.start_char, s.end_char, label='mid_quote')


def span_end_quotes(span):
    for s in span[-2:]._.find_all('"'):
        yield s.doc.char_span(s.start_char, s.end_char, label='end_quote')
    

def span_attributed_to(span):
    if not(any(span._.mid_quotes) and any(span._.persons) and any(span._.attributive_tags)):
        yield from ()
    spans = sorted(list(span._.persons) + list(span._.attributive_tags) + list(span._.mid_quotes))
    for i in range(len(spans)-2):
        # End attributed
        if (spans[i].label_=='mid_quote' and spans[i+1].label_=='attributive_tag' and spans[i+2].label_=='person'):
            if 0 <= spans[i+1]._.dist(spans[i]) <= 2:
                if span.end > 0 and span.char_span(-2,-1) and span.char_span(-2,-1).text == '.':
                    span_to_replace=span.doc.char_span(spans[i].start_char,span.end_char-1)
                else:
                    span_to_replace=span.doc.char_span(spans[i].start_char,span.end_char)
                span._.to_replace.add(span_to_replace)
                yield spans[i+2]
        # End attributed
        elif (spans[i].label_=='mid_quote' and spans[i+1].label_=='person' and spans[i+2].label_=='attributive_tag'):
            if 0 <= spans[i+1]._.dist(spans[i]) <= 3:
                if span.end > 0 and span.char_span(-2,-1) and span.char_span(-2,-1).text == '.':
                    span_to_replace=span.doc.char_span(spans[i].start_char,span.end_char-1)
                else:
                    span_to_replace=span.doc.char_span(spans[i].start_char,span.end_char)
                span._.to_replace.add(span_to_replace)
                yield spans[i+1]
        # Start attributed
        elif (spans[i].label_=='person' and spans[i+1].label_=='attributive_tag' and spans[i+2].label_=='mid_quote'):
            if 0 <= spans[i+1]._.dist(spans[i]) <= 2:
                span_to_replace=span.doc.char_span(span.start_char, spans[i+2].end_char)
                span._.to_replace.add(span_to_replace)
                yield spans[i]


def span_is_attributed(span):
    if any(span._.mid_quotes) and any(span._.persons) and any(span._.attributive_tags):
        return False if not any(span._.attributed_to) else True
    else:
        return False


# Span Extensions (Methods)
Span.set_extension('dist', method=span_distance, force=True)
Span.set_extension('find_all', method=span_find_all, force=True)
Span.set_extension('is_right_after', method=span_is_right_after, force=True)
# Span Extensions (Properties)
Span.set_extension('persons', getter=span_persons, force=True)
Span.set_extension('locations', getter=span_locations, force=True)
Span.set_extension('attributive_tags', getter=span_attributive_tags, force=True)
Span.set_extension('start_quotes', getter=span_start_quotes, force=True)
Span.set_extension('mid_quotes', getter=span_mid_quotes, force=True)
Span.set_extension('end_quotes', getter=span_end_quotes, force=True)
Span.set_extension('attributed_to', getter=span_attributed_to, force=True)
Span.set_extension('to_replace', default=set(), force=True)
# Span Extensions (Booleans)
Span.set_extension('is_attributed',getter=span_is_attributed, force=True)


def doc_attributed_statements(doc):
    """
    attributed_sentences =
    {
        person_1: {
            index: [span_1, span_2, span_3],
            index: [span_1, span_2]
        }
        person_2: {
            index: [span_1, span_2, span_3],
            index: [span_1, span_2]
        }
    }
    """
    person = None
    related_sentences = []
    attributed_sentences = defaultdict(lambda: defaultdict(list))
    def reset(index):
        nonlocal related_sentences, person
        if person:
            attributed_sentences[person][index] += related_sentences
        related_sentences.clear()
        person = None
    for i, s in enumerate(doc.sents):
        persons = list(s._.attributed_to)
        if related_sentences and s._.is_right_after(related_sentences[-1]):
            if len(persons) == 1:
                person = persons.pop()
                related_sentences.append(s)
            elif any(s._.start_quotes):
                if related_sentences[-1]._.is_attributed:
                    related_sentences.append(s)
                else:
                    reset(i-1)
                    related_sentences.append(s)
            elif any(s._.end_quotes):
                related_sentences.append(s)
                reset(i)
            else:
                # TODO: Sentences with no open or end quote are subject to
                # related sentences if one of the sentence in the related
                # sentences is attributed and none of the currently 
                # related sentences contains an end quote.
                if not (related_sentences[-1]._.is_attributed):
                    # Since the current sentence does not have 
                    # an open or an end quote, it would only be related 
                    # if the previous sentence is not attributed
                    related_sentences.append(s)
        else:
            reset(i-1)
            if len(persons) == 1:
                person = persons.pop()
                related_sentences.append(s)
            elif (any(s._.start_quotes) or any(s._.end_quotes)):
                related_sentences.append(s)
    return attributed_sentences


def json_attributed_sentences(attributed_sentences):
    """
    {
    'attributed': ...,
    'content': [
        {
        'start': ...,
        'end': ...,
        'replaces':[
            {
            'start': ...,
            'end': ...,
            },
            ...
            ]
        },
    ]
    },
    """
    statements = []
    for person, sentences in attributed_sentences.items():
        statement = defaultdict(list)
        contents = []

        for spans in sentences.values():
            content = {
                'text': "".join(span.text for span in spans),
                # TODO: Make sure to reflect change in the json_model.py
                'to_replace': [],
            }
            for span in spans:
                for s in span._.to_replace:
                    content['to_replace'].append(
                        {
                            'start': s.start_char - spans[0].start_char,
                            'end': s.end_char - spans[0].start_char
                        }
                    )
            contents.append(content)
        statement['attributed'].append(person)
        statement['contents'] += contents
        statements.append(statement)

    return statements


def doc_publish_location(doc):
    # Location Criteria:
    # 1) Has to be a starting token of the sentence
    # 2) At least one GPE token followed by a dash
    location_pattern = re.compile(
        r'(?P<location>[A-Za-z]{2,}\,?\s?[A-Za-z\.?]+)\s+-+')

    for sentence in doc.sents:
        for token_pos in sentence._.locations:
            if token_pos.start == sentence.start:
                results = re.finditer(location_pattern, sentence.text)
                # If the result shows that the location matched is
                # at the start of the sentence, return it otherwise None
                for m in results:
                    if m.start() == sentence.start:
                        return m.group('location')

    return 'Unknown'


# Doc Extensions
Doc.set_extension('publish_location', getter=doc_publish_location, force=True)
Doc.set_extension('attributed_statements',getter=doc_attributed_statements, force=True)
