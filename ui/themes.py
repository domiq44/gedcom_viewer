import tkinter as tk
from tkinter import ttk


COLORS = {
    "background": "#f6f7f9",
    "surface": "#ffffff",
    "muted_surface": "#fafafa",
    "text": "#333333",
    "muted_text": "#666666",
    "link": "#0078d7",
    "sidebar": "#e7ebf0",
    "sidebar_hover": "#d5e5f5",
    "sidebar_active": "#ffffff",
    "sidebar_text": "#2b415a",
    "sidebar_active_text": "#0d3b66",
    "disabled_text": "#9aa4b2",
    "separator": "#c8ced6",
    "selection": "#0078d7",
}

FONTS = {
    "ui": ("Segoe UI", 10),
    "title": ("Segoe UI", 12, "bold"),
    "mono": ("Consolas", 10),
    "mono_bold": ("Consolas", 10, "bold"),
}


def apply_modern_theme(root):
    style = ttk.Style(root)

    # Thème moderne intégré
    style.theme_use("clam")

    # Couleurs et typographie cohérentes
    style.configure("TFrame", background=COLORS["background"])
    style.configure("TLabel", background=COLORS["background"], font=FONTS["ui"])
    style.configure("TButton", font=FONTS["ui"], padding=6)
    style.configure(
        "Nav.TButton",
        font=FONTS["ui"],
        padding=(4, 4),
        background=COLORS["surface"],
        foreground=COLORS["text"],
        borderwidth=0,
    )
    style.map(
        "Nav.TButton",
        background=[("active", COLORS["sidebar_hover"])],
        foreground=[("disabled", COLORS["disabled_text"])],
    )
    style.configure("TSeparator", background=COLORS["separator"])
    style.configure("TLabelframe", background=COLORS["background"])
    style.configure(
        "TLabelframe.Label",
        background=COLORS["background"],
        foreground="#1f2d3d",
        font=FONTS["title"],
    )
    style.configure("TNotebook", background=COLORS["background"])
    style.configure(
        "TNotebook.Tab",
        padding=(10, 6),
        font=FONTS["ui"],
        background=COLORS["sidebar"],
        foreground=COLORS["sidebar_text"],
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLORS["sidebar_active"])],
        foreground=[("selected", COLORS["sidebar_active_text"])],
    )

    # Accent discret pour mieux structurer les blocs d’information
    root.option_add("*LabelFrame.borderWidth", "1")
    root.option_add("*Frame.highlightThickness", "1")

    style.configure(
        "Entity.Treeview",
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
        font=FONTS["ui"],
        rowheight=26,
    )
    style.map(
        "Entity.Treeview",
        background=[("selected", COLORS["selection"])],
        foreground=[("selected", COLORS["surface"])],
    )

    # Zone texte
    root.option_add("*Text.font", FONTS["mono"])
    root.option_add("*Text.background", COLORS["surface"])
    root.option_add("*Text.foreground", COLORS["text"])
    root.option_add("*Entry.font", FONTS["ui"])
