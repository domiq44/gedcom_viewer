"""Modèle d'un événement GEDCOM."""

from gedcom.models.lazy_list import _LazyList


class Event:
    """Représente un événement GEDCOM et ses sous-tags."""

    details = _LazyList()

    __slots__ = ("tag", "value", "_details")

    def __init__(self, tag, value=""):
        """Initialise l'événement avec son tag et sa valeur."""
        self.tag = tag
        self.value = value or ""
        self._details = None

    def add_detail(self, tag, value):
        """Ajoute un sous-tag (tag, valeur) à l'événement."""
        self.details.append((tag, value))

    def get(self, key, default=None):
        """Fournit un accès compatible avec l'ancien dictionnaire d'événement."""
        if key in {"tag", "value", "details"}:
            return getattr(self, key)
        return default
