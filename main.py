import logging
import os
import faulthandler
import time

_startup_started_at = time.perf_counter()

if __name__ == "__main__":
    log_path = os.path.expanduser("~/.gedcom_viewer.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8")],
    )
    logger = logging.getLogger(__name__)
    startup_log_handler = next(
        handler
        for handler in logging.getLogger().handlers
        if isinstance(handler, logging.FileHandler)
    )
    faulthandler.dump_traceback_later(5, repeat=True, file=startup_log_handler.stream)
    logger.info("Démarrage de GEDCOM Viewer")

    imports_started_at = time.perf_counter()
    import tkinter as tk

    from ui.main_window import GedcomViewer
    from ui.themes import apply_modern_theme

    logger.info(
        "Imports de l'application terminés en %.3f s",
        time.perf_counter() - imports_started_at,
    )

    tk_started_at = time.perf_counter()
    root = tk.Tk()
    logger.info("Fenêtre Tk créée en %.3f s", time.perf_counter() - tk_started_at)

    startup_state = {"configure_events": 0, "mapped": False, "idle": False}
    root._startup_diagnostics_enabled = True
    root._startup_callback_metrics = {}

    def count_configure_events(event):
        startup_state["configure_events"] += 1

    root.bind_all("<Configure>", count_configure_events, add="+")

    def stop_startup_monitor_if_complete():
        if startup_state["mapped"] and startup_state["idle"]:
            root.unbind_all("<Configure>")

    def log_layout_callback_metrics():
        for callback_name, metrics in sorted(root._startup_callback_metrics.items()):
            logger.info(
                "Tk layout callback %s: count=%d total=%.3f s max=%.3f s",
                callback_name,
                metrics[0],
                metrics[1],
                metrics[2],
            )

    def log_window_mapped(event):
        if event.widget is root:
            startup_state["mapped"] = True
            root._startup_diagnostics_enabled = False
            faulthandler.cancel_dump_traceback_later()
            logger.info(
                "Fenêtre affichée après %.3f s (%d événements Configure)",
                time.perf_counter() - _startup_started_at,
                startup_state["configure_events"],
            )
            log_layout_callback_metrics()
            root.unbind("<Map>", map_binding_id)
            stop_startup_monitor_if_complete()

    map_binding_id = root.bind("<Map>", log_window_mapped, add="+")

    def report_startup_progress():
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
    apply_modern_theme(root)
    logger.info("Thème appliqué en %.3f s", time.perf_counter() - theme_started_at)

    window_started_at = time.perf_counter()
    app = GedcomViewer(root)
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
        startup_state["idle"] = True
        logger.info(
            "Premier état idle Tk après %.3f s",
            time.perf_counter() - _startup_started_at,
        )
        stop_startup_monitor_if_complete()

    root.after_idle(log_first_idle)
    root.mainloop()
