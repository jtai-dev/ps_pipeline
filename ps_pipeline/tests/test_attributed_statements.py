import pytest
from ps_pipeline.tests.str_format import ansiscape


def test_number_of_expected_statements(docs_to_expected_attributed_statements):
    errors = []

    for (
        candidate_id,
        source,
        doc,
    ), expected_data in docs_to_expected_attributed_statements:
        expected_length = len([e for e in expected_data if e["ignore"] == "False"])
        actual_length = len(doc._.attributive_spans)
        if expected_length != actual_length:
            errors.append(
                f"   {ansiscape('Candidate ID: ' + str(candidate_id), 'CLR_GREY')}\n"
                f"         {ansiscape('Source: ' + source, 'CLR_GREY')}\n\n"
                f"{ansiscape('Expected Length: ', 'CLR_BRIGHT_GREEN')}"
                + f" {ansiscape(str(expected_length), 'CLR_BRIGHT_GREEN')}\n"
                f"     {ansiscape('Got Length: ', 'CLR_BRIGHT_RED')}"
                + f" {ansiscape(str(actual_length), 'CLR_BRIGHT_RED')}\n"
            )

    assert not errors, "LENGTH NOT MATCHED:\n\n" + "\n\n\n".join(errors)


def test_attributed_statements_are_extracted_in_order(
    docs_to_expected_attributed_statements,
):

    errors = []

    for (
        candidate_id,
        source,
        doc,
    ), expected_data in docs_to_expected_attributed_statements:
        extracted_data = []

        for statement in doc._.attributive_spans:
            extracted_data.append(
                {
                    "attributed": statement.get("attributed").text,
                    "text": " ".join(map(lambda x: x.text, statement["spans"])),
                }
            )

        for extracted, expected in zip(extracted_data, expected_data):

            if expected["ignore"] == "True":
                continue

            if extracted["text"] != expected["text"]:
                errors.append(
                    f"         {ansiscape('Candidate ID: ' + str(candidate_id), 'CLR_GREY')}\n"
                    f"               {ansiscape('Source: ' + source, 'CLR_GREY')}\n\n"
                    + f"{ansiscape('Expected Attributed:', 'CLR_BRIGHT_GREEN','TXT_BOLD')}"
                    + f" {ansiscape(expected['attributed'], 'BG_CYAN')}\n"
                    f"        {ansiscape('Expected Text:', 'CLR_BRIGHT_GREEN','TXT_BOLD')}"
                    + f" {ansiscape(expected['text'], 'CLR_BRIGHT_GREEN')}\n\n"
                    f"       {ansiscape('Got Attributed:', 'TXT_BOLD')}"
                    + f" {ansiscape(extracted['attributed'], 'BG_MAGENTA')}\n"
                    f"             {ansiscape('Got Text:', 'TXT_BOLD')}"
                    + f" {ansiscape(extracted['text'], 'CLR_BRIGHT_RED')}\n"
                )

    assert not errors, "MISMATCHED ORDER:\n\n" + "\n\n\n".join(errors)


def test_attributed_statements_are_extracted(docs_to_expected_attributed_statements):

    errors = []

    for (
        candidate_id,
        source,
        doc,
    ), expected_data in docs_to_expected_attributed_statements:

        extracted_data = []

        for statement in doc._.attributive_spans:
            text = " ".join(map(lambda x: x.text, statement["spans"]))
            extracted_data.append(text)

        for expected in expected_data:

            if expected["ignore"] == "True":
                continue

            if expected["text"] not in extracted_data:
                errors.append(
                    f"       {ansiscape('Candidate ID: ' + str(candidate_id), 'CLR_GREY')}\n"
                    f"             {ansiscape('Source: ' + source, 'CLR_GREY')}\n\n"
                    f"           {ansiscape('[MISSING]\n', 'CLR_BRIGHT_RED', 'TXT_BOLD')}"
                    f"         {ansiscape('Attributed:', 'CLR_BRIGHT_GREEN', 'TXT_BOLD')}"
                    + f" {ansiscape(expected['attributed'], 'BG_CYAN')}\n"
                    f"               {ansiscape('Text:', 'CLR_BRIGHT_GREEN','TXT_BOLD')}"
                    + f" {ansiscape(expected['text'], 'CLR_BRIGHT_GREEN')}\n\n"
                )

    assert not errors, "NOT EXTRACTED:\n\n" + "\n\n".join(errors)


def test_attributed_statements_are_correctly_attributed(
    docs_to_expected_attributed_statements,
):
    errors = []

    for (
        candidate_id,
        source,
        doc,
    ), expected_data in docs_to_expected_attributed_statements:

        expected_text_to_attributed = {
            e["text"]: e["attributed"] for e in expected_data
        }

        for statement in doc._.attributive_spans:
            attributed = statement["attributed"]
            text = " ".join(map(lambda x: x.text, statement["spans"]))

            if text in expected_text_to_attributed:
                expected_attribution = expected_text_to_attributed.get(text)
                if attributed != expected_attribution:
                    errors.append(
                        f"       {ansiscape('Candidate ID: ' + str(candidate_id), 'CLR_GREY')}\n"
                        f"             {ansiscape('Source: ' + source, 'CLR_GREY')}\n\n"
                        f"               {ansiscape('Text:', 'CLR_BRIGHT_GREEN','TXT_BOLD')}"
                        + f" {ansiscape(expected_data['text'], 'CLR_BRIGHT_GREEN')}\n\n"
                        f"{ansiscape('Expected Attributed:', 'CLR_BRIGHT_GREEN', 'TXT_BOLD')}"
                        + f" {ansiscape(expected_attribution, 'BG_CYAN')}\n"
                        f"                 Got Attributed: {attributed}\n"
                    )

    assert not errors, "MISMATCHED ATTRIBUTION:\n\n" + "\n\n".join(errors)


# def main():
#     from ps_pipeline.tests.conftest import attributed_statements_docs_to_expected, attributed_statements_nlp, attributed_statements_test_data
#     ast = attributed_statements_docs_to_expected(attributed_statements_test_data(), attributed_statements_nlp())
#     test_check_statements_are_in_exact_order(ast)

if __name__ == "__main__":
    pytest.main()
    # main()
