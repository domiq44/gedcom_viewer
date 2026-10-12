from gedcom.models.lazy_list import _LazyList


class Event:
    """Représente un événement GEDCOM et ses sous-tags."""

    details = _LazyList()

    __slots__ = ("tag", "value", "_details")

    def __init__(self, tag, value=""):
        self.tag = tag
        self.value = value or ""
        self._details = None

    def add_detail(self, tag, value):
        self.details.append((tag, value))

    def get(self, key, default=None):
        """Fournit un accès compatible avec l'ancien dictionnaire d'événement."""
        if key in {"tag", "value", "details"}:
            return getattr(self, key)
        return default
