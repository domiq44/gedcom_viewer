"""Formatage de texte pour la présentation des entités."""

import re


class TextFormatter:
    """Formate les valeurs de texte pour l'affichage des entités."""

    def __init__(self, translator=None):
        """Initialise le formateur avec un traducteur optionnel."""
        self.translator = translator

    def _text(self, key):
        """Retourne le libellé traduit d'une clé de locale."""
        if self.translator is None:
            return key
        return self.translator.get(key)

    def _facts(self, pairs, max_facts=4):
        """Retourne les couples (libellé, valeur) non vides."""
        facts = []
        for key, value in pairs:
            text = self._value(value)
            if text:
                facts.append((self._text(key), text))
        return facts[:max_facts]

    @staticmethod
    def _value(value):
        """Formate une valeur de fait en texte affichable."""
        if value is None:
            return ""
        if isinstance(value, (list, tuple, set)):
            return ", ".join(str(item) for item in value if item)
        return str(value).strip()

    @staticmethod
    def _year(value):
        """Retourne l'année sur quatre chiffres d'une date GEDCOM."""
        match = re.search(r"\d{4}", value or "")
        return match.group(0) if match else ""

    def _life_span(self, entity):
        """Retourne la plage d'années de vie d'un individu."""
        birth = self._year(entity.birth_date)
        death = self._year(entity.death_date)
        if birth and death:
            return f"{birth} – {death}"
        if birth:
            return birth
        if death:
            return f"? – {death}"
        return ""

    @staticmethod
    def _pointer(entity):
        """Retourne le pointeur d'une entité."""
        return getattr(entity, "pointer", "") or "—"

    @staticmethod
    def _clean_name(value: str | None) -> str:
        """Nettoie un nom GEDCOM pour l'affichage.

        Retire les ``/`` autour du nom de famille et les virgules. Si un nom de
        famille est détecté entre ``/``, il est placé en premier suivi d'une
        virgule (ex: ``John /Doe/`` devient ``Doe, John``).
        """
        if not value:
            return ""
        cleaned = value.replace(",", "")
        parts = re.split(r"/", cleaned)
        if len(parts) >= 3:
            surname = parts[1].strip()
            given = " ".join(p.strip() for p in (parts[0], parts[2]) if p.strip())
            if given:
                return f"{surname}, {given}"
            return f"{surname},"
        return cleaned.strip()

    @staticmethod
    def _first_line(text, limit=120):
        """Retourne la première ligne d'un texte, tronquée si nécessaire."""
        if not text:
            return ""
        lines = str(text).strip().splitlines()
        if not lines:
            return ""
        first = lines[0].strip()
        if len(first) <= limit:
            return first
        return first[: limit - 1] + "…"
