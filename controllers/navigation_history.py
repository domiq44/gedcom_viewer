"""Historique de navigation entre entités."""


class NavigationHistory:
    """Historique de navigation entre entités (pile bornée)."""

    MAX_ENTRIES = 100

    def __init__(self):
        """Initialise l'historique vide."""
        self.entries = []
        self.index = -1

    def reset(self):
        """Réinitialise l'historique."""
        self.entries = []
        self.index = -1

    def record(self, context):
        """Enregistre un contexte de navigation."""
        if not context or not context.get("entity"):
            return

        entity = context["entity"]
        pointer = getattr(entity, "pointer", None)
        if not pointer:
            return

        if self.index >= 0:
            current_context = self.entries[self.index]
            current_entity = current_context["entity"]
            current_pointer = getattr(current_entity, "pointer", None)
            same_type = current_context.get("type") == context.get("type")
            if same_type and current_pointer == pointer:
                if context.get("type") != "citation" or current_entity is entity:
                    return

        if self.index < len(self.entries) - 1:
            self.entries = self.entries[: self.index + 1]

        self.entries.append(context)
        self.index = len(self.entries) - 1
        if len(self.entries) > self.MAX_ENTRIES:
            overflow = len(self.entries) - self.MAX_ENTRIES
            del self.entries[:overflow]
            self.index -= overflow

    def back(self):
        """Revient au contexte précédent."""
        if self.index <= 0:
            return None
        self.index -= 1
        return self.entries[self.index]

    def forward(self):
        """Avance au contexte suivant."""
        if self.index >= len(self.entries) - 1:
            return None
        self.index += 1
        return self.entries[self.index]

    @property
    def can_go_back(self):
        """Indique si un retour est possible."""
        return self.index > 0

    @property
    def can_go_forward(self):
        """Indique si une avance est possible."""
        return self.index < len(self.entries) - 1
