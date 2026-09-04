class Event:
    """Représente un événement GEDCOM et ses sous-tags."""

    def __init__(self, tag, value=""):
        self.tag = tag
        self.value = value or ""
        self.details = []

    def add_detail(self, tag, value):
        self.details.append((tag, value))

    def get(self, key, default=None):
        """Fournit un accès compatible avec l'ancien dictionnaire d'événement."""
        if key in {"tag", "value", "details"}:
            return getattr(self, key)
        return default
