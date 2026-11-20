"""Gestion centralisée des continuations de texte CONT/CONC."""

CONTINUATION_TAGS = frozenset({"CONT", "CONC"})


def append_continuation(text, tag, value):
    """Append a GEDCOM CONT/CONC value without changing its spacing."""
    suffix = value or ""
    if tag == "CONC":
        return f"{text or ''}{suffix}"
    if tag == "CONT":
        return f"{text or ''}\n{suffix}"
    return text
