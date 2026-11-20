"""Style et activation des pointeurs cliquables des fiches structurées."""

from ui.themes import COLORS


class StructuredLinkRenderer:
    """Applique le style lien et active les pointeurs avec garde anti-glissement."""

    ACTIVATION_THRESHOLD_PX = 4

    @staticmethod
    def bind(widget, pointer, on_begin, on_finish):
        """Style le pointeur et lie les événements de clic et de survol."""
        widget.tag_add("pointer", "1.0", "end-1c")
        widget.tag_configure("pointer", foreground=COLORS["link"])
        widget.tag_bind("pointer", "<Button-1>", lambda event: on_begin(event, pointer))
        widget.tag_bind(
            "pointer", "<ButtonRelease-1>", lambda event: on_finish(event, pointer)
        )
        widget.tag_bind(
            "pointer",
            "<Enter>",
            lambda event: event.widget.configure(cursor="hand2"),
        )
        widget.tag_bind(
            "pointer",
            "<Leave>",
            lambda event: event.widget.configure(cursor="xterm"),
        )

    @staticmethod
    def begin(event, target):
        """Mémorise le point de départ de l'appui."""
        event.widget._pointer_activation_start = (target, event.x, event.y)

    @staticmethod
    def finish(event, target, navigate):
        """Active le pointeur si l'appui n'a pas glissé au-delà du seuil."""
        start = getattr(event.widget, "_pointer_activation_start", None)
        event.widget._pointer_activation_start = None
        if start is None or start[0] != target:
            return

        if (
            abs(event.x - start[1]) > StructuredLinkRenderer.ACTIVATION_THRESHOLD_PX
            or abs(event.y - start[2]) > StructuredLinkRenderer.ACTIVATION_THRESHOLD_PX
        ):
            return

        event.widget.after_idle(navigate, target)
