from unidecode import unidecode


def asciffy(text):
    return unidecode(text).replace('"', '\\"')


def main(text):
    if text is not None:
        print(asciffy(text))
    else:
        print("Error.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="Text Asciifier")

    parser.add_argument(
        "text",
        help="Paste the text that is you want to asciify.",
    )

    args = parser.parse_args()

    main(args.text)