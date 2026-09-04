from tkinter import messagebox


class EntityNavigator:
    """Service de navigation entre entités, séparé de la fenêtre principale."""

    def __init__(self, controller, history, on_display, on_error):
        self.controller = controller
        self.history = history
        self.on_display = on_display
        self.on_error = on_error

    def record(self, context):
        self.history.record(context)

    def navigate_to(self, pointer):
        if not self.controller.is_loaded():
            self.on_error(
                "ui.error",
                "ui.no_session",
            )
            return

        target = self.controller.resolve_pointer(pointer)
        if target is None:
            self.on_error(
                "ui.error",
                "ui.entity_not_found",
                pointer=pointer,
            )
            return

        context = self.controller.get_entity_display_info(target)
        self.record(context)
        self.on_display(context)

    def go_back(self):
        context = self.history.back()
        if context is not None:
            self.on_display(context)

    def go_forward(self):
        context = self.history.forward()
        if context is not None:
            self.on_display(context)
