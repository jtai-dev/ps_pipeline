ANSI_PALETTE = {
    "TXT_END": "0",
    "TXT_BOLD": "1",
    "TXT_GREYED": "2",
    "TXT_ITALIC": "3",
    "TXT_UNDERLINE": "4",
    "TXT_BLINK": "5",
    "TXT_INVERSE": "7",
    "TXT_TRANS": "8",
    "TXT_STRIKE": "9",  # Not supported in terminal.app
    "CLR_BLACK": "30",
    "CLR_RED": "31",
    "CLR_GREEN": "32",
    "CLR_YELLOW": "33",
    "CLR_BLUE": "34",
    "CLR_MAGENTA": "35",
    "CLR_CYAN": "36",
    "CLR_GREY": "37",
    "CLR_DARK_GREY": "90",
    "CLR_BRIGHT_RED": "91",
    "CLR_BRIGHT_GREEN": "92",
    "CLR_BRIGHT_YELLOW": "93",
    "CLR_VIOLET": "94",
    "CLR_BRIGHT_MAGENTA": "95",
    "CLR_BRIGHT_CYAN": "96",
    "CLR_WHITE": "97",
    "BG_BLACK": "40",
    "BG_RED": "41",
    "BG_GREEN": "42",
    "BG_YELLOW": "43",
    "BG_BLUE": "44",
    "BG_MAGENTA": "45",
    "BG_CYAN": "46",
    "BG_GREY": "47",
    "BG_DARK_GREY": "100",
    "BG_BRIGHT_RED": "101",
    "BG_BRIGHT_GREEN": "102",
    "BG_BRIGHT_YELLOW": "103",
    "BG_BRIGHT_BLUE": "104",
    "BG_BRIGHT_MAGENTA": "105",
    "BG_BRIGHT_CYAN": "106",
    "BG_WHITE": "107",
}


def hexscape(value):
    return f"\x1b[{value}m"


def ansiscape(text, *options):

    end = hexscape(ANSI_PALETTE.get("TXT_END"))
    formatted = text

    for option in options:
        emphasis = hexscape(ANSI_PALETTE.get(option))
        if end in formatted:
            formatted = emphasis + formatted
        else:
            formatted = emphasis + formatted + end

    return formatted


def insert_format(original, pos_palette: dict[tuple[int, int], list[str]]):
    modified = []
    last_position = 0

    for pos in sorted(pos_palette):

        start_char, end_char = pos
        palettes = pos_palette.get(pos)

        trailing_str = ""
        formatted = ""

        if start_char > last_position:
            trailing_str = original[last_position:start_char]
            formatted = ansiscape(original[start_char:end_char], *palettes)
        else:
            if end_char > last_position:
                formatted = ansiscape(
                    original[last_position:end_char],
                    *palettes,
                )
            else:
                pass

        if trailing_str:
            modified.append(trailing_str)

        if formatted:
            modified.append(formatted)

        if end_char > last_position:
            last_position = end_char

    modified.append(original[last_position:])
    return "".join(modified)
