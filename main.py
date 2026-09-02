import logging
import os
import tkinter as tk

from ui.main_window import GedcomViewer
from ui.themes import apply_modern_theme

if __name__ == "__main__":
    log_path = os.path.expanduser("~/.gedcom_viewer.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8")],
    )

    root = tk.Tk()
    apply_modern_theme(root)
    app = GedcomViewer(root)
    root.mainloop()
