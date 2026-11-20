"""Utilitaires de détection et d'ouverture des liens."""

import re
import webbrowser

from ui.themes import COLORS

_URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")
_TRAILING_URL_CHARS = ".,;:!?)]}"


def configure_text_urls(text_widget):
    """Rend les URL d'un texte cliquables."""
    text = text_widget.get("1.0", "end-1c")
    text_widget.tag_delete("url")

    for match in _URL_PATTERN.finditer(text):
        url = match.group(0).rstrip(_TRAILING_URL_CHARS)
        if not url:
            continue
        end_offset = match.start() + len(url)
        text_widget.tag_add(
            "url", f"1.0 + {match.start()} chars", f"1.0 + {end_offset} chars"
        )

    text_widget.tag_configure("url", foreground=COLORS["link"], underline=True)
    text_widget.tag_bind("url", "<Button-1>", _open_url_at_click)
    text_widget.tag_bind(
        "url", "<Enter>", lambda event: event.widget.configure(cursor="hand2")
    )
    text_widget.tag_bind(
        "url", "<Leave>", lambda event: event.widget.configure(cursor="xterm")
    )


def _open_url_at_click(event):
    """Ouvre l'URL au clic."""
    text_widget = event.widget
    index = text_widget.index(f"@{event.x},{event.y}")
    line_start = text_widget.index(f"{index} linestart")
    line_end = text_widget.index(f"{index} lineend")
    line = text_widget.get(line_start, line_end)
    column = int(index.split(".")[1])
    for match in _URL_PATTERN.finditer(line):
        url = match.group(0).rstrip(_TRAILING_URL_CHARS)
        if match.start() <= column < match.start() + len(url):
            webbrowser.open(url)
            return
