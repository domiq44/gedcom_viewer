"""Point d'entrée de l'application GEDCOM Viewer."""

import faulthandler
import logging
import os
import time

_startup_started_at = time.perf_counter()


def _disable_slow_ibus_xim(logger):
    """Désactive l'XIM IBus pour éviter les lenteurs de saisie."""
    if (
        os.environ.get("XMODIFIERS") == "@im=ibus"
        and os.environ.get("GEDCOM_VIEWER_KEEP_XIM") != "1"
    ):
        os.environ.pop("XMODIFIERS", None)
        logger.info("XIM IBus désactivé pour ce lancement")


def main():
    """Démarre l'application GEDCOM Viewer."""
    log_path = os.path.expanduser("~/.gedcom_viewer.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8")],
    )
    logger = logging.getLogger(__name__)
    _disable_slow_ibus_xim(logger)
    startup_log_handler = next(
        handler
        for handler in logging.getLogger().handlers
        if isinstance(handler, logging.FileHandler)
    )
    if startup_log_handler.stream is not None:
        faulthandler.dump_traceback_later(
            5, repeat=True, file=startup_log_handler.stream.fileno()
        )
    logger.info("Démarrage de GEDCOM Viewer")

    imports_started_at = time.perf_counter()
    import tkinter as tk

    from ui.main_window import GedcomViewer
    from ui.themes import apply_app_theme

    logger.info(
        "Imports de l'application terminés en %.3f s",
        time.perf_counter() - imports_started_at,
    )

    tk_started_at = time.perf_counter()
    root = tk.Tk()
    logger.info("Fenêtre Tk créée en %.3f s", time.perf_counter() - tk_started_at)

    startup_state = {"configure_events": 0, "mapped": False, "idle": False}

    def count_configure_events(event):
        """Compte les événements <Configure> pendant le démarrage."""
        startup_state["configure_events"] += 1

    root.bind_all("<Configure>", count_configure_events, add="+")

    def stop_startup_monitor_if_complete():
        """Arrête le suivi de démarrage une fois la fenêtre mappée et idle."""
        if startup_state["mapped"] and startup_state["idle"]:
            root.unbind_all("<Configure>")

    def log_window_mapped(event):
        """Journalise la durée d'affichage de la fenêtre au premier Map."""
        if event.widget is root:
            startup_state["mapped"] = True
            faulthandler.cancel_dump_traceback_later()
            logger.info(
                "Fenêtre affichée après %.3f s (%d événements Configure)",
                time.perf_counter() - _startup_started_at,
                startup_state["configure_events"],
            )
            root.unbind("<Map>", map_binding_id)
            stop_startup_monitor_if_complete()

    map_binding_id = root.bind("<Map>", log_window_mapped, add="+")

    def report_startup_progress():
        """Journalise périodiquement l'état d'attente du démarrage Tk."""
        if startup_state["mapped"] and startup_state["idle"]:
            return
        logger.info(
            "Attente démarrage Tk après %.3f s: %d événements Configure, "
            "fenêtre mappée=%s, idle=%s",
            time.perf_counter() - _startup_started_at,
            startup_state["configure_events"],
            startup_state["mapped"],
            startup_state["idle"],
        )
        root.after(2000, report_startup_progress)

    root.after(2000, report_startup_progress)

    theme_started_at = time.perf_counter()
    apply_app_theme(root)
    logger.info("Thème appliqué en %.3f s", time.perf_counter() - theme_started_at)

    window_started_at = time.perf_counter()
    GedcomViewer(root)
    logger.info(
        "Interface construite en %.3f s",
        time.perf_counter() - window_started_at,
    )
    root.after(
        0,
        lambda: logger.info(
            "Boucle d'événements Tk active après %.3f s",
            time.perf_counter() - _startup_started_at,
        ),
    )

    def log_first_idle():
        """Journalise l'obtention du premier état idle Tk."""
        startup_state["idle"] = True
        logger.info(
            "Premier état idle Tk après %.3f s",
            time.perf_counter() - _startup_started_at,
        )
        stop_startup_monitor_if_complete()

    root.after_idle(log_first_idle)
    root.mainloop()


if __name__ == "__main__":
    main()
