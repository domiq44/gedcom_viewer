import re
import webbrowser

from ui.themes import COLORS


_URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")
_TRAILING_URL_CHARS = ".,;:!?)]}"


def find_urls(value):
    if not isinstance(value, str):
        return []
    return [match.group(0).rstrip(_TRAILING_URL_CHARS) for match in _URL_PATTERN.finditer(value)]


def configure_label(label, value):
    text = value if value else "—"
    label.config(text=text, foreground=COLORS["text"], cursor="")
    label.unbind("<Button-1>")

    urls = find_urls(text)
    if urls:
        label.config(foreground=COLORS["link"], cursor="hand2")
        label.bind("<Button-1>", lambda event, url=urls[0]: webbrowser.open(url))


def configure_text_widget(text_widget, value):
    text = value if value else "—"
    text_widget.config(state="normal")
    text_widget.delete("1.0", "end")
    text_widget.insert("1.0", text)
    text_widget.tag_delete("url")

    for match in _URL_PATTERN.finditer(text):
        url = match.group(0).rstrip(_TRAILING_URL_CHARS)
        if not url:
            continue
        end_offset = match.start() + len(url)
        text_widget.tag_add("url", f"1.0 + {match.start()} chars", f"1.0 + {end_offset} chars")

    text_widget.tag_configure("url", foreground=COLORS["link"], underline=True)
    text_widget.tag_bind("url", "<Button-1>", _open_url_at_click)
    text_widget.config(state="disabled")


def _open_url_at_click(event):
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
