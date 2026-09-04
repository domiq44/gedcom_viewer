"""Chargement des traductions de l'interface."""

import json
import os

SUPPORTED_LANGUAGES = {
    "fr": "Francais",
    "en": "English",
    "es": "Español",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português",
}
DEFAULT_LANGUAGE = "en"
LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")


def _load_catalog(language):
    path = os.path.join(LOCALES_DIR, f"{language}.json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


TRANSLATIONS = {language: _load_catalog(language) for language in SUPPORTED_LANGUAGES}


class Translator:
    def __init__(self, language=DEFAULT_LANGUAGE):
        self.language = (
            language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        )

    def set_language(self, language):
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Langue non supportee: {language}")
        self.language = language

    def get(self, key, **values):
        text = TRANSLATIONS.get(self.language, {}).get(key)
        if text is None:
            text = TRANSLATIONS.get(DEFAULT_LANGUAGE, {}).get(key, key)
        return text.format(**values) if values else text
