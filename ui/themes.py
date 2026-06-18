import tkinter as tk
from tkinter import ttk

def apply_modern_theme(root):
    style = ttk.Style(root)

    # Thème moderne intégré
    style.theme_use("clam")

    # Couleurs modernes
    style.configure("TFrame", background="#f2f2f2")
    style.configure("TLabel", background="#f2f2f2", font=("Segoe UI", 10))
    style.configure("TButton", font=("Segoe UI", 10), padding=6)
    style.configure("TSeparator", background="#999999")

    # Listbox (police en tuple)
    root.option_add("*Listbox.font", ("Segoe UI", 10))
    root.option_add("*Listbox.background", "#ffffff")
    root.option_add("*Listbox.selectBackground", "#0078d7")
    root.option_add("*Listbox.selectForeground", "#ffffff")

    # Zone texte (police en tuple)
    root.option_add("*Text.font", ("Consolas", 10))
    root.option_add("*Text.background", "#ffffff")
    root.option_add("*Text.foreground", "#333333")
