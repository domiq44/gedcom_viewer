import tkinter as tk
from tkinter import ttk


def apply_modern_theme(root):
    style = ttk.Style(root)

    # Thème moderne intégré
    style.theme_use("clam")

    # Couleurs et typographie cohérentes
    style.configure("TFrame", background="#f6f7f9")
    style.configure("TLabel", background="#f6f7f9", font=("Segoe UI", 10))
    style.configure("TButton", font=("Segoe UI", 10), padding=6)
    style.configure("TSeparator", background="#c8ced6")
    style.configure("TLabelframe", background="#f6f7f9")
    style.configure(
        "TLabelframe.Label",
        background="#f6f7f9",
        foreground="#1f2d3d",
        font=("Segoe UI", 10, "bold"),
    )
    style.configure("TNotebook", background="#f6f7f9")
    style.configure(
        "TNotebook.Tab",
        padding=(10, 6),
        font=("Segoe UI", 10),
        background="#e7ebf0",
        foreground="#2b415a",
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", "#ffffff")],
        foreground=[("selected", "#0d3b66")],
    )

    # Accent discret pour mieux structurer les blocs d’information
    root.option_add("*LabelFrame.borderWidth", "1")
    root.option_add("*Frame.highlightThickness", "1")

    # Listbox
    root.option_add("*Listbox.font", ("Consolas", 10))
    root.option_add("*Listbox.background", "#ffffff")
    root.option_add("*Listbox.foreground", "#1f1f1f")
    root.option_add("*Listbox.selectBackground", "#0078d7")
    root.option_add("*Listbox.selectForeground", "#ffffff")

    # Zone texte
    root.option_add("*Text.font", ("Consolas", 10))
    root.option_add("*Text.background", "#ffffff")
    root.option_add("*Text.foreground", "#333333")
    root.option_add("*Entry.font", ("Segoe UI", 10))
