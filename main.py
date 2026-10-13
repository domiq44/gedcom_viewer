import logging
import os
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

    theme_started_at = time.perf_counter()
    apply_modern_theme(root)
    logger.info("Thème appliqué en %.3f s", time.perf_counter() - theme_started_at)

    window_started_at = time.perf_counter()
    app = GedcomViewer(root)
    logger.info(
        "Interface construite en %.3f s",
        time.perf_counter() - window_started_at,
    )
    root.after_idle(
        lambda: logger.info(
            "Interface prête pour interaction après %.3f s",
            time.perf_counter() - _startup_started_at,
        )
    )
    root.mainloop()
