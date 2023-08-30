import re
import sys
import json

from pathlib import Path
from datetime import datetime
from collections import defaultdict

import spacy
from spacy.tokens import Span
from unidecode import unidecode
from tqdm import tqdm


ATTRIBUTION_TAGS = {
    'acknowledge', 'add','affirm' 'agree', 'announce', 'articulate', 'assert', 'backtrack', 'begin', 'blurt', 'call',
    'clarify', 'comment', 'communicate', 'confer', 'consider', 'contend', 'declare', 'denote', 'drawl', 'elaborate', 
    'echo','emit', 'end', 'enunciate', 'expound', 'express', 'greet', 'indicate','interject', 'mention', 'note', 'observe', 
    'orate', 'persist', 'predict', 'pronounce', 'quip', 'reaffirm','recite', 'reckon', 'relate', 'remark', 'repeat', 
    'reply', 'respond', 'say', 'share', 'slur', 'state', 'suggest', 'tell', 'urge', 'utter', 'vocalize', 'voice',
    'ask', 'beg', 'challenge', 'contemplate', 'guess', 'hint', 'hypothesize', 'imply', 'inquire', 'interrogate',
    'invite', 'mouth', 'muse', 'plead', 'ponder', 'probe', 'propose', 'puzzle', 'repeat', 'request', 'requisition',
    'query', 'question', 'quiz', 'solicit', 'speculate', 'wonder'
}

def read_file(filepath):

    with open(filepath, 'r') as f:
        content = json.load(f)
    
    return content['records']


def export_file(e, filename, directory):
    timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d-%H%M%S-%f')

    if len(filename) > 225:
        filename = filename[:225]
    
    with open(directory / f"{filename}_{timestamp}.json", 'w') as f:
        json.dump({'records': e}, f, indent=4)


def find_phrase(span:Span, phrase, pattern=False):
    phrase = re.escape(phrase) if not pattern else phrase
    for m in re.finditer(phrase, span.text):
        token_start = span._.tokens_start_pos.get(m.start())
        token_end = span._.tokens_end_pos.get(m.end())
        if token_start and token_end:
            yield((span._.tokens_start_pos.get(m.start()).i, 
                   span._.tokens_end_pos.get(m.end()).i + 1))

def attributed_to(span):
    for location_person, person in span._.persons.items():
        for location_attribution_tag in span._.attribution_tags:
            for location_mid_quote in span._.mid_quotes:
                if any((location_person > location_attribution_tag > location_mid_quote,
                        location_person < location_attribution_tag < location_mid_quote)):
                    return person

def is_attributed(span):
    if span._.has_mid_quote and span._.has_person and span._.has_attribution_tag:
        return False if not attributed_to(span) else True
    else:
        return False

def is_after(span, target_span):
    return True if span.start_char - target_span.end_char == 1 else False


asciify = lambda text: unidecode(text)
persons = lambda span: {(ent.start, ent.end): ent.text for ent in span.ents if ent.label_=='PERSON'}
mid_quotes = lambda span: {(start, end): f"{p}{q}" for q in ('"', "'") for p in (',',':') for start, end in span._.find_phrase(fr"[\s|\{p}]\s?\{q}", pattern=True)}
attribution_tags = lambda span: {(token.i, token.i+1):token.text for token in span if token.lemma_ in ATTRIBUTION_TAGS}
tokens_start_pos = lambda span: {token.idx - span.start_char: token for token in span}
tokens_end_pos = lambda span: {token.idx - span.start_char + len(token): token for token in span}

has_person = lambda span: any(ent.label_=='PERSON' for ent in span.ents)
has_start_quote = lambda span: any(q in span[:2].text for q in ('"', "'"))
has_mid_quote = lambda span: any(re.findall(fr"[\s|\{p}]+\s?\{q}", span.text) for p in (',',':') for q in ('"',"'"))
has_end_quote = lambda span: any(q in span[-2:].text for q in ('"', "'"))
has_attribution_tag = lambda span: any(token.lemma_ in ATTRIBUTION_TAGS for token in span)

Span.set_extension('tokens_start_pos', getter=tokens_start_pos, force=True)
Span.set_extension('tokens_end_pos', getter=tokens_end_pos, force=True)
Span.set_extension('find_phrase', method=find_phrase, force=True)

Span.set_extension('mid_quotes', getter=mid_quotes, force=True)
Span.set_extension('persons', getter=persons, force=True)
Span.set_extension('attributed_to', getter=attributed_to, force=True)
Span.set_extension('attribution_tags', getter=attribution_tags, force=True)

Span.set_extension('has_person', getter=has_person, force=True)
Span.set_extension('has_start_quote', getter=has_start_quote, force=True)
Span.set_extension('has_mid_quote', getter=has_mid_quote, force=True)
Span.set_extension('has_end_quote', getter=has_end_quote, force=True)
Span.set_extension('has_attribution_tag', getter=has_attribution_tag)
Span.set_extension('is_attributed', getter=is_attributed, force=True)
Span.set_extension('is_after', method=is_after, force=True)


def extract_statements(doc):
    attributed_sentences = defaultdict(lambda: defaultdict(list))
    related_sentences = []

    def attribute(related_sentences):
        start = related_sentences[0].start
        end = related_sentences[-1].end
        if doc[start:end]._.is_attributed:
            attributed_sentences[doc[start:end]._.attributed_to][i] += related_sentences
        related_sentences.clear()

    for i, s in enumerate(doc.sents):
        if related_sentences:
            if s._.is_after(related_sentences[-1]):
                if s._.has_start_quote:
                    if related_sentences[-1]._.has_mid_quote:
                        related_sentences.append(s)
                    else:
                        attribute(related_sentences)
                        related_sentences.append(s)
                elif s._.has_end_quote:
                    related_sentences.append(s)
                    attribute(related_sentences)
                else:
                    related_sentences.append(s)
            else:
                attribute(related_sentences)
                related_sentences.append(s)
        else:
            if any((s._.has_start_quote, s._.has_end_quote, s._.has_mid_quote)):
                related_sentences.append(s)
    return attributed_sentences


if __name__ == '__main__':
    _, filepath = sys.argv  
    
    working_dir = Path(filepath).parent.parent
    rows = read_file(Path(filepath))

    for row in tqdm(rows, desc='Asciifying...'):
        row['title'] = asciify(row['title'])
        row['text'] = asciify(row['text'])

    nlp = spacy.load('en_core_web_trf')

    new_records = []

    for row in tqdm(rows[:100], desc='Processing'):
        doc = nlp(row['text'])
        spans = list(doc.sents)
        attributed_sentences = extract_statements(doc)

        for person in attributed_sentences:
            for i in attributed_sentences[person]:
                attributed_sentences[person][i] = list(map(lambda span: span.text, attributed_sentences[person][i]))

        new_records.append({
            'title': row['title'],
            'timestamp': row['timestamp'],
            'url': row['url'],
            # 'sentences': [span.text for span in spans],
            'statements': attributed_sentences
        })

    export_file(new_records, 'processed', working_dir)
    