"""Thèmes de couleurs et styles ttk de l'application.

Fournit une palette claire (par défaut) et une palette sombre, ainsi qu'un
sélecteur de thème à l'exécution. ``COLORS`` est un dictionnaire mutable qui
reflète toujours le thème actif : les modules qui font
``from ui.themes import COLORS`` voient automatiquement les nouvelles couleurs
après un appel à :func:`set_theme`.
"""

from tkinter import ttk

LIGHT_COLORS = {
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
    "section_accent": "#176f65",
    "section_accent_border": "#5c9b91",
    "header_background": "#dfeaf5",
    "header_title": "#163a57",
    "header_subtitle": "#44627a",
    "section_title": "#1f2d3d",
    "tooltip_background": "#263746",
    "tooltip_text": "#ffffff",
    "syntax_tag": "#d14",
    "syntax_pointer": "#008000",
    "syntax_date": "#aa5500",
}

DARK_COLORS = {
    "background": "#1e1e1e",
    "surface": "#252526",
    "muted_surface": "#2d2d2d",
    "text": "#e0e0e0",
    "muted_text": "#a0a0a0",
    "link": "#4aa8ff",
    "sidebar": "#2b2b2b",
    "sidebar_hover": "#37373d",
    "sidebar_active": "#3c3c3c",
    "sidebar_text": "#c0c0c0",
    "sidebar_active_text": "#ffffff",
    "disabled_text": "#6a6a6a",
    "separator": "#3c3c3c",
    "selection": "#094771",
    "section_accent": "#4ec9b0",
    "section_accent_border": "#3a6b63",
    "header_background": "#2b3a4a",
    "header_title": "#e0e0e0",
    "header_subtitle": "#a0a0a0",
    "section_title": "#e0e0e0",
    "tooltip_background": "#3c3c3c",
    "tooltip_text": "#e0e0e0",
    "syntax_tag": "#ff7b72",
    "syntax_pointer": "#7ee787",
    "syntax_date": "#ffa657",
}

THEMES = {"light": LIGHT_COLORS, "dark": DARK_COLORS}

COLORS = dict(LIGHT_COLORS)

_active_theme = "light"

FONTS: dict[str, tuple[str, int] | tuple[str, int, str]] = {
    "ui": ("Segoe UI", 10),
    "title": ("Segoe UI", 12, "bold"),
    "mono": ("Consolas", 10),
    "mono_bold": ("Consolas", 10, "bold"),
    "display_title": ("Segoe UI", 16, "bold"),
    "display_subtitle": ("Segoe UI", 10),
    "fact_label": ("Segoe UI", 9),
}


def set_theme(name):
    """Active le thème ``name`` (« light » ou « dark ») en modifiant COLORS."""
    global _active_theme
    if name not in THEMES:
        raise ValueError(f"Thème inconnu: {name}")
    _active_theme = name
    COLORS.clear()
    COLORS.update(THEMES[name])


def current_theme():
    """Retourne le nom du thème actif."""
    return _active_theme


def apply_app_theme(root):
    """Applique le thème ttk courant à la fenêtre racine."""
    style = ttk.Style(root)

    # Thème moderne intégré
    style.theme_use("clam")

    # Couleurs et typographie cohérentes
    style.configure("TFrame", background=COLORS["background"])
    style.configure("TLabel", background=COLORS["background"], font=FONTS["ui"])
    style.configure("TButton", font=FONTS["ui"], padding=6)
    style.configure(
        "Copy.TButton",
        font=FONTS["ui"],
        padding=(2, 1),
        background=COLORS["background"],
        foreground=COLORS["muted_text"],
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Copy.TButton",
        background=[
            ("disabled", COLORS["background"]),
            ("active", COLORS["sidebar_hover"]),
        ],
        foreground=[("disabled", COLORS["disabled_text"])],
        relief=[("pressed", "flat")],
    )
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
    style.configure(
        "ClearSearch.TButton",
        font=("Segoe UI", 11, "bold"),
        padding=(3, 1),
        background=COLORS["surface"],
        foreground=COLORS["muted_text"],
        borderwidth=1,
        relief="solid",
    )
    style.map(
        "ClearSearch.TButton",
        background=[("active", COLORS["sidebar_hover"])],
        foreground=[("active", COLORS["text"]), ("disabled", COLORS["disabled_text"])],
    )
    style.configure("TSeparator", background=COLORS["separator"])
    style.configure("TLabelframe", background=COLORS["background"])
    style.configure(
        "TLabelframe.Label",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=FONTS["title"],
    )
    style.configure(
        "DetailSection.TLabelframe",
        background=COLORS["background"],
        bordercolor=COLORS["section_accent_border"],
        lightcolor=COLORS["section_accent_border"],
        darkcolor=COLORS["section_accent_border"],
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "DetailSection.TLabelframe.Label",
        background=COLORS["background"],
        foreground=COLORS["section_accent"],
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
