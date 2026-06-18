from ui.main_window import GedcomViewer
from ui.themes import apply_modern_theme
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    apply_modern_theme(root)
    app = GedcomViewer(root)
    root.mainloop()
