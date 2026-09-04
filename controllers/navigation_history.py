class NavigationHistory:
    def __init__(self):
        self.entries = []
        self.index = -1

    def reset(self):
        self.entries = []
        self.index = -1

    def record(self, context):
        if not context or not context.get("entity"):
            return

        pointer = getattr(context["entity"], "pointer", None)
        if not pointer:
            return

        if self.index >= 0:
            current_pointer = getattr(
                self.entries[self.index]["entity"], "pointer", None
            )
            if current_pointer == pointer:
                return

        if self.index < len(self.entries) - 1:
            self.entries = self.entries[: self.index + 1]

        self.entries.append(context)
        self.index = len(self.entries) - 1

    def back(self):
        if self.index <= 0:
            return None
        self.index -= 1
        return self.entries[self.index]

    def forward(self):
        if self.index >= len(self.entries) - 1:
            return None
        self.index += 1
        return self.entries[self.index]

    @property
    def can_go_back(self):
        return self.index > 0

    @property
    def can_go_forward(self):
        return self.index < len(self.entries) - 1
