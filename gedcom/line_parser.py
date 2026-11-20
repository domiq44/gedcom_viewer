"""Analyse lexicale d'une ligne GEDCOM."""

import re

LEVEL_PATTERN = re.compile(r"^([+-]?\d+)(?:[ \t]+|$)")
POINTER_PATTERN = re.compile(r"^(@[^ \t]+)(?:[ \t](.*))?$")
TAG_PATTERN = re.compile(r"^([^ \t]+)(?:[ \t](.*))?$")


def parse_line(line):
    """Analyse une ligne GEDCOM en (niveau, pointeur, tag, valeur)."""
    content = line.rstrip("\r\n")

    if not content.strip():
        return None, None, None, None

    level_match = LEVEL_PATTERN.match(content)
    if level_match is None:
        return None, None, None, None

    level = int(level_match.group(1))
    remainder = content[level_match.end() :]
    if not remainder.strip():
        return None, None, None, None

    pointer = None
    if level == 0 and remainder.startswith("@"):
        pointer_match = POINTER_PATTERN.match(remainder)
        if pointer_match is None:
            return None, None, None, None
        pointer = pointer_match.group(1)
        remainder = (pointer_match.group(2) or "").lstrip(" \t")

    tag_match = TAG_PATTERN.match(remainder)
    if tag_match is None:
        return level, pointer, None, ""

    tag = tag_match.group(1)
    value = tag_match.group(2) or ""
    return level, pointer, tag, value
