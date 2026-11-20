"""Chargement des traductions de l'interface."""

import json
import logging
import os

logger = logging.getLogger(__name__)

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
    """Charge le catalogue de traduction d'une langue."""
    path = os.path.join(LOCALES_DIR, f"{language}.json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


TRANSLATIONS = {language: _load_catalog(language) for language in SUPPORTED_LANGUAGES}


class Translator:
    """Traducteur d'interface avec repli sur la langue par défaut."""

    def __init__(self, language=DEFAULT_LANGUAGE):
        """Initialise le traducteur avec la langue demandée."""
        self.language = (
            language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        )

    def set_language(self, language):
        """Change la langue (lève ValueError si non supportée)."""
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Langue non supportee: {language}")
        self.language = language

    def get(self, key, **values):
        """Retourne la traduction d'une clé, avec formatage des paramètres."""
        text = TRANSLATIONS.get(self.language, {}).get(key)
        if text is None:
            text = TRANSLATIONS.get(DEFAULT_LANGUAGE, {}).get(key, key)
        if not values:
            return text
        try:
            return text.format(**values)
        except (KeyError, IndexError):
            logger.warning("Paramètres manquants pour la clé de traduction %s", key)
            return text
