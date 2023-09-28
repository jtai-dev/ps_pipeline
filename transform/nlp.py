
# Built-ins
import re
from collections import defaultdict, namedtuple

# External packages and libraries
from spacy.tokens import Doc, Span


ATTRIBUTION_TAGS = ['acknowledge', 'add', 'affirmagree', 'announce', 'articulate', 'ask', 'assert',
                    'backtrack', 'begin', 'blurt',
                    'call', 'challenge', 'clarify', 'comment', 'communicate', 'confer', 'consider', 'contemplate', 'contend', 'continue',
                    'declare', 'denote', 'drawl', 'echo', 'elaborate', 'emit', 'end', 'enunciate', 'expound', 'express', 'explain'
                    'greet', 'guess', 'hint', 'hypothesize', 'imply', 'indicate', 'inquire', 'interject', 'interrogate', 'invite',
                    'mention', 'mouth', 'muse', 'note', 'observe', 'orate',
                    'persist', 'plead', 'ponder', 'predict', 'probe', 'pronounce', 'propose', 'puzzle',
                    'query', 'question', 'quip', 'quiz',
                    'read', 'reaffirm', 'recite', 'reckon', 'relate', 'remark', 'repeat', 'reply', 'request', 'requisition', 'respond',
                    'say', 'share', 'slur', 'solicit', 'speculate', 'state', 'suggest', 'tell', 'urge', 'utter', 'vocalize', 'voice', 'wonder']


def char_tokens_start(span): return {
    token.idx - span.start_char: token for token in span}


def char_tokens_end(span): return {
    token.idx - span.start_char + len(token): token for token in span}


def find_phrase(span: Span, phrase, pattern=False):
    phrase = re.escape(phrase) if not pattern else phrase
    for m in re.finditer(phrase, span.text):
        token_start = span._.char_tokens_start.get(m.start())
        token_end = span._.char_tokens_end.get(m.end())
        if token_start and token_end:
            yield ((span._.char_tokens_start.get(m.start()).i,
                   span._.char_tokens_end.get(m.end()).i + 1))


def is_after_span(span, target_span):
    if ('\n' not in span[:2].text and '\n' not in target_span[-2:].text):
        # To account for whitespace
        if span.start - target_span.end < 2:
            return True
    return False


class TokenPosition(namedtuple('TokenPosition', ['name', 'start', 'end', 'text'])):
    def __gt__(self, target_pos):
        return (self.start, self.end) > (target_pos.start, target_pos.end)

    def __lt__(self, target_pos):
        return (self.start, self.end) < (target_pos.start, target_pos.end)

    def __sub__(self, target_pos):
        if self > target_pos:
            product = self.start - target_pos.end
            return product if product >= 0 else -1
        else:
            product = self.end - target_pos.start
            return abs(product) if product <= 0 else -1


def persons(span): return [
    TokenPosition('person', ent.start, ent.end, ent.text) for ent in span.ents if ent.label_ == 'PERSON']


def locations(span): return [
    TokenPosition('location', ent.start, ent.end, ent.text) for ent in span.ents if ent.label_ == 'GPE']


def mid_quotes(span): return [TokenPosition('mid_quote', start, end, span.doc[start:end].text) for q in ('"') for p in (
    ',', ':') for start, end in span[2:-2]._.find_phrase(fr"\{p}?\s?\{q}", pattern=True)]


def attribution_tags(span): return [TokenPosition('attribution_tag',
                                                  token.i, token.i+1, token.text) for token in span if token.lemma_ in ATTRIBUTION_TAGS]


def span_has_person(span): return any(
    ent.label_ == 'PERSON' for ent in span.ents)


def span_has_start_quote(span): return any(
    q in span[:2].text for q in ('"'))


def span_has_mid_quote(span):
    return any(re.findall(
        fr"\{p}?\s?\{q}", span[2:-2].text) for p in (',', ':') for q in ('"'))


def span_has_end_quote(span): return any(
    q in span[-2:].text for q in ('"'))


def span_has_attribution_tag(span): return any(
    token.lemma_ in ATTRIBUTION_TAGS for token in span)


def span_start_attributed_to(span):
    t = sorted(span._.persons + span._.attribution_tags + span._.mid_quotes)
    for i in range(len(t)-2):
        if (t[i].name == 'person' and t[i+1].name == 'attribution_tag' and t[i+2].name == 'mid_quote'):
            if 0 <= t[i+2] - t[i+2] <= 2:
                return t[i+2], t[i].text


def span_end_attributed_to(span):
    t = sorted(span._.persons + span._.attribution_tags + span._.mid_quotes)
    for i in range(len(t)-2):
        if (t[i].name == 'mid_quote' and t[i+1].name == 'person' and t[i+2].name == 'attribution_tag'):
            if 0 <= t[i+1] - t[i] <= 3:
                return t[i], t[i+1].text
        elif (t[i].name == 'mid_quote' and t[i+1].name == 'attribution_tag' and t[i+2].name == 'person'):
            if 0 <= t[i+1] - t[i] <= 2:
                return t[i], t[i+2].text


def span_is_start_attributed(span):
    if span._.has_mid_quote and span._.has_person and span._.has_attribution_tag:
        return False if not span_start_attributed_to(span) else True
    else:
        return False


def span_is_end_attributed(span):
    if span._.has_mid_quote and span._.has_person and span._.has_attribution_tag:
        return False if not span_end_attributed_to(span) else True
    else:
        return False


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
    attributed_sentences = defaultdict(lambda: defaultdict(list))
    currently_attributed = None
    related_sentences = []

    def reset_current(index):
        nonlocal related_sentences, currently_attributed
        if currently_attributed:
            attributed_sentences[currently_attributed][index] += related_sentences
        related_sentences.clear()
        currently_attributed = None

    for i, s in enumerate(doc.sents):

        if related_sentences and s._.is_after_span(related_sentences[-1]):

            if s._.is_start_attributed:
                tp_mq, currently_attributed = s._.start_attributed_to
                s._.to_replace.append(
                    TokenPosition('replace', s.start, tp_mq.start, doc[s.start: tp_mq.start].text))
                related_sentences.append(s)

            elif s._.is_end_attributed:
                tp_mq, currently_attributed = s._.end_attributed_to
                if s.end > 0 and doc[s.end-1].text == '.':
                    s._.to_replace.append(
                        TokenPosition('replace', tp_mq.start, s.end - 1, doc[tp_mq.start: s.end - 1].text))
                else:
                    s._.to_replace.append(
                        TokenPosition('replace', tp_mq.start, s.end, doc[tp_mq.start: s.end].text))
                related_sentences.append(s)

            elif s._.has_end_quote:
                related_sentences.append(s)
                reset_current(i)

            elif s._.has_start_quote:
                if related_sentences[-1]._.is_end_attributed:
                    related_sentences.append(s)
                else:
                    reset_current(i-1)
                    related_sentences.append(s)
            else:
                # TODO: If the last sentence has a mid quote, then it would require
                # the current sentence to have an open quote or an end quote,
                # otherwise it would not be related. (THIS DOESN'T APPLY IF THE PERSON EXIST BEFORE MID QUOTE) (see schumer record 2)
                if not (related_sentences[-1]._.is_end_attributed):
                    related_sentences.append(s)
        else:
            if related_sentences:
                reset_current(i-1)

            if s._.is_start_attributed:
                tp_mq, currently_attributed = s._.start_attributed_to
                s._.to_replace.append(
                    TokenPosition('replace', s.start, tp_mq.start, doc[s.start: tp_mq.start].text))
                related_sentences.append(s)

            elif s._.is_end_attributed:
                tp_mq, currently_attributed = s._.end_attributed_to
                if s.end > 0 and doc[s.end-1].text == '.':
                    s._.to_replace.append(
                        TokenPosition('replace', tp_mq.start, s.end - 1, doc[tp_mq.start: s.end - 1].text))
                else:
                    s._.to_replace.append(TokenPosition(tp_mq.start, s.end))
                related_sentences.append(s)

            elif (s._.has_start_quote or s._.has_end_quote):
                related_sentences.append(s)

    statements = []
    for person, sentences in attributed_sentences.items():
        statement = defaultdict(list)
        contents = []
        for spans in sentences.values():
            combined_span = doc[spans[0].start: spans[-1].end]
            content = {
                'text': combined_span.text,
                'start': combined_span.start_char,
                'end': combined_span.end_char,
                'to_replace': [],
            }
            for span in spans:
                for tp in span._.to_replace:
                    content['to_replace'].append(
                        {
                            'start': doc[tp.start:tp.end].start_char - combined_span.start_char,
                            'end': doc[tp.start:tp.end].end_char - combined_span.start_char
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


# Span Extensions
Span.set_extension('char_tokens_start', getter=char_tokens_start, force=True)
Span.set_extension('char_tokens_end', getter=char_tokens_end, force=True)
Span.set_extension('find_phrase', method=find_phrase, force=True)
Span.set_extension('mid_quotes', getter=mid_quotes, force=True)
Span.set_extension('persons', getter=persons, force=True)
Span.set_extension('locations', getter=locations, force=True)
Span.set_extension('to_replace', default=[])
Span.set_extension('start_attributed_to',
                   getter=span_start_attributed_to, force=True)
Span.set_extension('end_attributed_to',
                   getter=span_end_attributed_to, force=True)
Span.set_extension('attribution_tags', getter=attribution_tags, force=True)

# Span Extensions (Booleans)
Span.set_extension('has_person', getter=span_has_person, force=True)
Span.set_extension('has_start_quote', getter=span_has_start_quote, force=True)
Span.set_extension('has_mid_quote', getter=span_has_mid_quote, force=True)
Span.set_extension('has_end_quote', getter=span_has_end_quote, force=True)
Span.set_extension('has_attribution_tag',
                   getter=span_has_attribution_tag, force=True)
Span.set_extension('is_start_attributed',
                   getter=span_is_start_attributed, force=True)
Span.set_extension('is_end_attributed',
                   getter=span_is_end_attributed, force=True)
Span.set_extension('is_after_span', method=is_after_span, force=True)


# Doc Extensions
Doc.set_extension('publish_location', getter=doc_publish_location, force=True)
Doc.set_extension('attributed_statements',
                  getter=doc_attributed_statements, force=True)
