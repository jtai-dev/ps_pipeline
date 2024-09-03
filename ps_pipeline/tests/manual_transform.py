import os
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from spacy.tokens import Doc
from spacy.language import Language
from ps_pipeline.transform import pipe as t_pipe
from ps_pipeline.json_model import Articles
from ps_pipeline.tests.str_format import ansiscape, insert_format


def span_to_pos(w_span, p_span):
    start_char = p_span.start_char - w_span.start_char
    end_char = p_span.end_char - w_span.start_char
    return start_char, end_char


def print_sentences(doc):
    max_string = len(f"{len(doc)-1, len(doc)}:")

    for i, sent in enumerate(doc.sents):
        sent_pos = f"{(sent.start, sent.end)}:".rjust(max_string)

        if i % 2 == 0:
            formatted = ansiscape(sent.text, "CLR_CYAN")
        else:
            formatted = ansiscape(sent.text, "CLR_GREEN")

        if sent.text == "\n":
            formatted = ansiscape(sent.text, "BG_GREY")

        print(ansiscape(sent_pos, "TXT_BOLD"), formatted)


def print_related_sentences(doc):
    max_string = len(f"{len(doc)-1, len(doc)}:")
    current_color = "CLR_CYAN"
    related_sents = []

    for i, sent in enumerate(doc.sents):
        sent_pos = f"{(sent.start, sent.end)}:".rjust(max_string)

        if i == 0:
            related_sents.append((sent_pos, sent))
            continue

        if related_sents:
            if sent._.is_right_after(related_sents[-1][1]):
                related_sents.append((sent_pos, sent))
            else:
                for pos, s in related_sents:
                    if s.text == "\n":
                        formatted = ansiscape(s.text, "BG_GREY")
                    else:
                        formatted = ansiscape(s.text, current_color)

                    print(ansiscape(pos, "TXT_BOLD"), formatted)

                related_sents.clear()
                related_sents.append((sent_pos, sent))

                if sent.text.strip().strip("\n"):
                    current_color = (
                        "CLR_GREEN" if current_color == "CLR_CYAN" else "CLR_CYAN"
                    )
        else:
            related_sents.append((sent_pos, sent))


def print_attributive_spans_hints(doc):
    max_string = len(f"{len(doc)-1, len(doc)}:")

    for sent in doc.sents:

        sent_pos = f"{(sent.start, sent.end)}:".rjust(max_string)
        pos_d = defaultdict(list)

        for sq_span in sent._.start_quotes:
            sq_pos = span_to_pos(sent, sq_span)
            pos_d[sq_pos] += ["TXT_BOLD", "CLR_BRIGHT_MAGENTA"]

        for eq_span in sent._.end_quotes:
            eq_pos = span_to_pos(sent, eq_span)
            pos_d[eq_pos] += ["TXT_BOLD", "CLR_VIOLET"]

        for mq_span in sent._.mid_quotes:
            mq_pos = span_to_pos(sent, mq_span)
            pos_d[mq_pos] += ["TXT_BOLD", "CLR_CYAN"]

        for at_span in sent._.attributive_tags:
            at_pos = span_to_pos(sent, at_span)
            pos_d[at_pos] += ["TXT_BOLD", "CLR_BRIGHT_YELLOW"]

        for p_span in sent._.persons:
            p_pos = span_to_pos(sent, p_span)
            pos_d[p_pos] += ["TXT_BOLD", "CLR_BRIGHT_GREEN"]

        formatted = insert_format(sent.text, pos_d)
        print(sent_pos, formatted)


def print_attributive_spans(doc):
    max_string = len(f"{(len(doc)-1, len(doc))}:")

    for d in doc._.attributive_spans:
        for k, spans in d.items():
            if k == "attributed":
                name = d[k].text
                print(ansiscape(name, "TXT_BOLD", "BG_MAGENTA"))
            else:
                for span in spans:

                    span_pos = f"{(span.start, span.end)}:".rjust(max_string)
                    pos_to_palette = defaultdict(list)

                    # Innermost hex-escape takes precedence
                    for tr_span, _ in span._.to_replace:
                        pos = span_to_pos(span, tr_span)
                        pos_to_palette[pos] += ["TXT_BLINK", "CLR_RED"]

                    formatted = insert_format(span.text, pos_to_palette)
                    print(span_pos, formatted)

                print()


@Language.component("debug_sent_status_before")
def debug_sent_status_before(doc):
    Doc.set_extension("sentence_tokens_before", default=set())
    number_of_sentences = 0
    unassigned = 0

    for token in doc:
        if token.is_sent_start is True:
            number_of_sentences += 1
            doc._.sentence_tokens_before.add(token.i)
        if token.is_sent_start is None:
            unassigned += 1

    print("Number of Sentences", number_of_sentences)
    print("Unassigned Tokens", unassigned)
    return doc


@Language.component("debug_sent_status_after")
def debug_sent_status_after(doc):
    Doc.set_extension("sentence_tokens_after", default=set())
    number_of_sentences = 0
    unassigned = 0

    for token in doc:
        if token.is_sent_start is True:
            number_of_sentences += 1
            doc._.sentence_tokens_after.add(token.i)
        if token.is_sent_start is None:
            unassigned += 1

    print("Number of Sentences", number_of_sentences)
    print("Unassigned Tokens", unassigned)
    print(
        "Differences",
        len(
            doc._.sentence_tokens_before.symmetric_difference(
                doc._.sentence_tokens_after
            )
        ),
    )

    return doc


def see_all_trained_models(pipes_to_add):

    nlp_sm = t_pipe.spacy.load("en_core_web_sm")
    nlp_md = t_pipe.spacy.load("en_core_web_md")
    nlp_lg = t_pipe.spacy.load("en_core_web_lg")
    nlp_trf = t_pipe.spacy.load("en_core_web_trf")

    print("en_core_web_sm")
    print("Enabled:", " -> ".join(nlp_sm.pipe_names))
    print("Disabled:", ", ".join(nlp_sm.disabled))

    print()

    print("en_core_web_md")
    print("Enabled:", " -> ".join(nlp_md.pipe_names))
    print("Disabled:", ", ".join(nlp_md.disabled))

    print()

    print("en_core_web_lg")
    print("Enabled:", " -> ".join(nlp_lg.pipe_names))
    print("Disabled:", ", ".join(nlp_lg.disabled))

    print()

    print("en_core_web_trf")
    print("Enabled:", " -> ".join(nlp_trf.pipe_names))
    print("Disabled:", ", ".join(nlp_trf.disabled))


def main(args):

    load_dotenv()

    data_directory = Path(os.getenv("DATA_FILES_DIRECTORY"))
    import json

    if args.candidate_id is None or args.url is None:
        print("Both candidate ID and URL are required.")
        print("Exiting...")
        return

    extract_path = data_directory / args.candidate_id / "EXTRACT_FILES"
    extract_files = filter(lambda f: f.name.endswith(".json"), extract_path.iterdir())

    data = []

    for file in sorted(extract_files, key=lambda f: f.stat().st_mtime):
        with open(file, "r") as f:
            data += json.load(f)

    articles = Articles(data)

    text_by_url = {a.url: a.text for a in articles.all}
    text = text_by_url.get(args.url)

    if text is None:
        print("Text cannot be found. URL may not be listed in file.")
        return

    # see_all_trained_models()
    t_pipe.nlp_articles.register()
    t_pipe.nlp_attributed_statements.register()

    nlp = t_pipe.spacy.load("en_core_web_trf")

    nlp.add_pipe("sentencizer", before="parser")
    nlp.add_pipe("set_midquote_as_combined_sentence", after="sentencizer")
    nlp.add_pipe(
        "set_newline_as_sentence_start", after="set_midquote_as_combined_sentence"
    )

    # DEBUGGING
    # nlp.add_pipe("debug_sent_status_before", after="set_midquote_as_combined_sentence")
    # nlp.add_pipe("debug_sent_status_after", after="parser")
    # print(nlp.pipe_names)

    doc = nlp(t_pipe.asciify(text))

    if args.attributive_spans:
        print_attributive_spans(doc)

    if args.attributive_spans_hints:
        print_attributive_spans_hints(doc)

    if args.sentences:
        print_sentences(doc)

    if args.related_sentences:
        print_related_sentences(doc)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(prog="ps_pipeline_manual_test")

    parser.add_argument(
        "-c",
        "--candidate_id",
        help="Candidate ID",
    )

    parser.add_argument(
        "-u",
        "--url",
        help="URL of the article",
    )

    parser.add_argument(
        "-st",
        "--sentences",
        action="store_true",
        help="Print sentences",
    )

    parser.add_argument(
        "-rst",
        "--related_sentences",
        action="store_true",
        help="Print related sentences",
    )

    parser.add_argument(
        "-as",
        "--attributive_spans",
        action="store_true",
        help="Test for attributive spans",
    )

    parser.add_argument(
        "-ash",
        "--attributive_spans_hints",
        action="store_true",
        help="Test for hints towards attributive spans",
    )

    main(parser.parse_args())
