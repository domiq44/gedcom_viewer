import tkinter as tk

from ui.themes import COLORS


class EntityTypePanel(tk.Frame):
    """Panneau latéral de sélection du type d’entité GEDCOM."""

    def __init__(self, parent, translator, selected_type_var):
        super().__init__(
            parent,
            bg=COLORS["sidebar"],
            width=220,
            highlightthickness=1,
            highlightbackground=COLORS["separator"],
            highlightcolor=COLORS["separator"],
        )
        self.translator = translator
        self.selected_type_var = selected_type_var
        self._buttons = {}
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

    def set_items(self, items):
        for button in self._buttons.values():
            button.destroy()
        self._buttons = {}

        for row, (display, entity_type) in enumerate(items):
            button = tk.Button(
                self,
                text=display,
                command=lambda value=entity_type: self.selected_type_var.set(value),
                anchor="w",
                justify="left",
                padx=14,
                pady=9,
                relief="flat",
                bd=1,
                bg=COLORS["sidebar"],
                fg=COLORS["sidebar_text"],
                activebackground=COLORS["sidebar_hover"],
                activeforeground=COLORS["sidebar_active_text"],
                cursor="hand2",
                highlightthickness=0,
                font=("Segoe UI", 10, "bold"),
            )
            button.grid(row=row, column=0, sticky="ew", padx=6, pady=(0, 4))
            if row == 0:
                button.grid(pady=(4, 4))
            self._buttons[entity_type] = button

        self.update_selection(self.selected_type_var.get())

    def update_selection(self, selected_type):
        for entity_type, button in self._buttons.items():
            is_selected = entity_type == selected_type
            button.config(
                relief="solid" if is_selected else "flat",
                borderwidth=2 if is_selected else 1,
                bg=(COLORS["sidebar_active"] if is_selected else COLORS["sidebar"]),
                fg=(
                    COLORS["sidebar_active_text"]
                    if is_selected
                    else COLORS["sidebar_text"]
                ),
                padx=14,
                pady=9,
            )
            if is_selected:
                button.config(
                    fg=COLORS["sidebar_active_text"],
                    bg=COLORS["sidebar_active"],
                    highlightbackground=COLORS["selection"],
                    highlightcolor=COLORS["selection"],
                    activebackground=COLORS["sidebar_hover"],
                    activeforeground=COLORS["sidebar_active_text"],
                )
            else:
                button.config(
                    fg=COLORS["sidebar_text"],
                    bg=COLORS["sidebar"],
                    highlightbackground=COLORS["sidebar"],
                    highlightcolor=COLORS["sidebar"],
                    activebackground=COLORS["sidebar_hover"],
                    activeforeground=COLORS["sidebar_active_text"],
                )
