"""Vue d'arbre d'ascendance horizontal dans un Canvas Tkinter."""

from __future__ import annotations

import logging
import os
import re
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Any, Callable

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None  # type: ignore[assignment]
    ImageTk = None  # type: ignore[assignment]

from controllers.ancestor_tree_service import AncestorNode, AncestorTreeService
from ui.themes import COLORS

logger = logging.getLogger(__name__)


class AncestorTreeView(ttk.Frame):
    """Affiche l'arbre d'ascendance horizontal d'un individu dans un Canvas."""

    NODE_WIDTH = 295
    NODE_HEIGHT = 104
    HORIZONTAL_SPACING = 315
    # La hauteur de la boîte est fixe ; seule la largeur a été ajustée.
    # HORIZONTAL_SPACing évite le chevauchement entre deux frères successifs.
    VERTICAL_STEP = 140
    START_X = 99
    START_Y = 60
    NODE_PADDING_X = 8
    NODE_PADDING_Y = 8
    MAX_NAME_CHARS = 26
    CONNECTOR_OFFSET = 22
    NAME_FONT = ("Segoe UI", 8)
    VISIBLE_GENERATIONS = 5
    MAX_GENERATIONS_SERVICE = 50
    BUTTON_SIZE = 23

    def __init__(
        self,
        parent: tk.Misc,
        controller_provider: Callable[[], Any],
        translator: Any,
        individual_pointer: str | None = None,
        tooltip_factory: Callable[..., Any] | None = None,
        on_individual_selected: Callable[[str], None] | None = None,
        base_path: str | None = None,
    ) -> None:
        """Initialise la vue d'arbre d'ascendance."""
        super().__init__(parent)
        self.controller_provider = controller_provider
        self.translator = translator
        self.tooltip_factory: Callable[..., Any] | None = tooltip_factory
        self.on_individual_selected: Callable[[str], None] | None = (
            on_individual_selected
        )
        self.base_path = base_path
        self._root_node: AncestorNode | None = None
        self._node_positions: dict[int, tuple[int, int]] = {}
        self._node_items: dict[int, int] = {}
        self._canvas: tk.Canvas | None = None
        self._photo_images: dict[str, Any] = {}
        self._generation_offset = 0
        self._current_pointer: str | None = None
        self._children_window: tk.Toplevel | None = None
        self._build()
        if individual_pointer:
            self.load_tree(individual_pointer)

    def _build(self) -> None:
        """Construit le canvas avec barres de défilement."""
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(
            container,
            background=COLORS["background"],
            highlightthickness=0,
            borderwidth=0,
        )
        self._canvas.grid(row=0, column=0, sticky="nsew")

        v_scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=self._canvas.yview
        )
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        self._canvas.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(
            container, orient="horizontal", command=self._canvas.xview
        )
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        self._canvas.configure(xscrollcommand=h_scrollbar.set)

        self._canvas.bind("<Configure>", lambda _event: self._on_configure())
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

    def _bind_mousewheel(self, _event: Any) -> None:
        """Active le défilement à la molette sur le canvas."""
        canvas = self._canvas
        if canvas is None:
            return
        canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        canvas.bind_all("<Shift-MouseWheel>", self._on_shift_mousewheel)
        canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        canvas.bind_all("<Button-5>", self._on_mousewheel_linux)
        canvas.bind_all("<Shift-Button-4>", self._on_shift_mousewheel_linux)
        canvas.bind_all("<Shift-Button-5>", self._on_shift_mousewheel_linux)

    def _unbind_mousewheel(self, _event: Any) -> None:
        """Désactive le défilement à la molette."""
        canvas = self._canvas
        if canvas is None:
            return
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Shift-MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")
        canvas.unbind_all("<Shift-Button-4>")
        canvas.unbind_all("<Shift-Button-5>")

    def _on_mousewheel(self, event: Any) -> None:
        """Défile verticalement à la molette."""
        if self._canvas is None:
            return
        delta = int(-1 * (event.delta / 120)) if hasattr(event, "delta") else -1
        self._canvas.yview_scroll(delta, "units")

    def _on_shift_mousewheel(self, event: Any) -> None:
        """Défile horizontalement à la molette + Shift."""
        if self._canvas is None:
            return
        delta = int(-1 * (event.delta / 120)) if hasattr(event, "delta") else -1
        self._canvas.xview_scroll(delta, "units")

    def _on_mousewheel_linux(self, event: Any) -> None:
        """Défile verticalement à la molette (Linux)."""
        if self._canvas is None:
            return
        delta = -1 if event.num == 4 else 1
        self._canvas.yview_scroll(delta, "units")

    def _on_shift_mousewheel_linux(self, event: Any) -> None:
        """Défile horizontalement à la molette + Shift (Linux)."""
        if self._canvas is None:
            return
        delta = -1 if event.num == 4 else 1
        self._canvas.xview_scroll(delta, "units")

    def _on_configure(self) -> None:
        """Recalcule la région de défilement du canvas."""
        if self._canvas is not None:
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def load_tree(self, individual_pointer: str) -> None:
        """Construit et affiche l'arbre d'ascendance pour l'individu donné."""
        controller = self.controller_provider()
        service = AncestorTreeService(controller, base_path=self.base_path)
        self._root_node = service.build_tree(
            individual_pointer, generations=self.MAX_GENERATIONS_SERVICE
        )
        if self._root_node is None:
            return
        self._current_pointer = individual_pointer
        self._generation_offset = 0
        self._redraw_with_offset()

    def _redraw_with_offset(self) -> None:
        """Recalcule les positions et redessine l'arbre avec l'offset courant."""
        if self._root_node is None or self._canvas is None:
            return
        self._node_positions = {}
        min_gen = self._generation_offset
        max_gen = self._generation_offset + self.VISIBLE_GENERATIONS - 1
        total_height = (
            self._leaf_count_in_visible_range(self._root_node, min_gen, max_gen)
            * self.VERTICAL_STEP
        )
        y_start = self.START_Y
        y_end = self.START_Y + total_height
        # Positions x absolues (START_X pour la racine, pas de décalage en
        # négatif qui causerait un écran blanc). Seul le filtre de génération
        # et le scroll du canvas changent ce qui est visible.
        self._assign_positions(
            self._root_node, self.START_X, y_start, y_end, min_gen, max_gen
        )
        self._draw_tree()

    def _leaf_count(self, node: AncestorNode | None) -> int:
        """Retourne le nombre de feuilles (nœuds sans parents) du sous-arbre."""
        if node is None:
            return 0
        if node.father is None and node.mother is None:
            return 1
        return self._leaf_count(node.father) + self._leaf_count(node.mother)

    def _leaf_count_in_visible_range(
        self, node: AncestorNode | None, min_gen: int, max_gen: int
    ) -> int:
        """Retourne le nombre de feuilles dans la fenêtre visible [min_gen, max_gen].

        Un nœud est compté comme feuille s'il est dans la fenêtre visible et
        qu'il n'a aucun parent dans cette même fenêtre (ses parents au-delà
        de la dernière génération visible ne sont pas affichés).
        """
        if node is None:
            return 0
        if node.generation < min_gen:
            return self._leaf_count_in_visible_range(
                node.father, min_gen, max_gen
            ) + self._leaf_count_in_visible_range(node.mother, min_gen, max_gen)
        if node.generation > max_gen:
            return 0
        father_in_window = node.father is not None and node.father.generation <= max_gen
        mother_in_window = node.mother is not None and node.mother.generation <= max_gen
        if not father_in_window and not mother_in_window:
            return 1
        return self._leaf_count_in_visible_range(
            node.father, min_gen, max_gen
        ) + self._leaf_count_in_visible_range(node.mother, min_gen, max_gen)

    def _truncate_name(self, name: str) -> str:
        """Tronque un nom trop long avec points de suspension."""
        if len(name) <= self.MAX_NAME_CHARS:
            return name
        return name[: self.MAX_NAME_CHARS - 1] + "\u2026"

    def _fit_text(self, text: str, font: tkfont.Font, max_width: int) -> str:
        """Tronque un texte pour qu'il tienne sur une seule ligne dans max_width."""
        if font.measure(text) <= max_width:
            return text
        # Recherche dichotomique de la plus longue prefixe qui tient
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if font.measure(text[:mid] + "\u2026") <= max_width:
                lo = mid
            else:
                hi = mid - 1
        if lo == 0:
            return "\u2026"
        return text[:lo] + "\u2026"

    @staticmethod
    def _format_individual_name(name: str | None) -> str:
        """Formate un nom GEDCOM en « Nom, Prénom1 Prénom2 ... ».

        Le nom GEDCOM utilise des séparateurs / pour le nom de famille,
        ex: "Jean /Dupont/" -> "Dupont, Jean".
        """
        if not isinstance(name, str):
            return ""
        surname_match = re.search(r"/([^/]*)/", name)
        if not surname_match:
            surname = ""
            given_name = re.sub(r"\s+/([^/]*)/\s*", r" \1 ", name)
        else:
            surname = surname_match.group(1).strip()
            given_name = re.sub(
                r"\s+/([^/]*)/\s*",
                r" ",
                name[: surname_match.start()] + name[surname_match.end() :],
            )
        given_name = " ".join(given_name.split())
        if surname and given_name:
            return f"{surname}, {given_name}"
        if surname:
            return f"{surname},"
        return given_name

    def _assign_positions(
        self,
        node: AncestorNode | None,
        x: int,
        y_start: int,
        y_end: int,
        min_gen: int,
        max_gen: int,
    ) -> None:
        """Assigne les positions en pyramide horizontale, nœud centré verticalement."""
        if node is None:
            return
        node_y = (y_start + y_end) // 2
        self._node_positions[id(node)] = (x, node_y)

        father_leaves = self._leaf_count_in_visible_range(node.father, min_gen, max_gen)
        mother_leaves = self._leaf_count_in_visible_range(node.mother, min_gen, max_gen)
        total = father_leaves + mother_leaves
        if total == 0:
            return

        if node.father is not None and node.mother is not None:
            father_portion = (y_end - y_start) * father_leaves // total
            self._assign_positions(
                node.father,
                x + self.HORIZONTAL_SPACING,
                y_start,
                y_start + father_portion,
                min_gen,
                max_gen,
            )
            self._assign_positions(
                node.mother,
                x + self.HORIZONTAL_SPACING,
                y_start + father_portion,
                y_end,
                min_gen,
                max_gen,
            )
        elif node.father is not None:
            self._assign_positions(
                node.father,
                x + self.HORIZONTAL_SPACING,
                y_start,
                y_end,
                min_gen,
                max_gen,
            )
        elif node.mother is not None:
            self._assign_positions(
                node.mother,
                x + self.HORIZONTAL_SPACING,
                y_start,
                y_end,
                min_gen,
                max_gen,
            )

    def _draw_tree(self) -> None:
        """Dessine les nœuds et les lignes de l'arbre sur le canvas."""
        if self._canvas is None or self._root_node is None:
            return
        self._canvas.delete("all")
        self._node_items = {}
        self._draw_node_recursive(self._root_node)

        # Bouton « < » à gauche du nœud racine pour afficher ses enfants
        # (tous conjoints confondus), quelque soit la génération défilée.
        children_pointers = self._root_children_pointers()
        children_btn_x1 = None
        if children_pointers:
            x, y = self._node_positions[id(self._root_node)]
            self._draw_children_button(x, y, children_pointers)
            children_btn_x1 = x - self.NODE_WIDTH // 2 - 8 - self.BUTTON_SIZE

        half_w = self.NODE_WIDTH // 2
        half_h = self.NODE_HEIGHT // 2
        first_visible_x = (
            self.START_X + self._generation_offset * self.HORIZONTAL_SPACING
        )
        last_visible_x = (
            self.START_X
            + (self._generation_offset + self.VISIBLE_GENERATIONS - 1)
            * self.HORIZONTAL_SPACING
        )
        # Le nœud le plus à gauche est centré sur first_visible_x ; son bord
        # gauche est à first_visible_x - half_w. Le scrollregion doit l'inclure
        # entièrement (pas de rognage) avec une petite marge fixe. Les
        # connecteurs du nœud racine partent vers la droite (parents à x plus
        # grand), donc aucun espace supplémentaire n'est nécessaire à gauche.
        min_x = first_visible_x - half_w - 15
        if children_btn_x1 is not None:
            min_x = min(min_x, children_btn_x1 - 5)
        max_x = last_visible_x + half_w + self.CONNECTOR_OFFSET + self.BUTTON_SIZE + 10
        max_y = self.START_Y + self.NODE_HEIGHT
        for x, y in self._node_positions.values():
            max_y = max(max_y, y + half_h)
        if self._canvas is not None:
            self._canvas.configure(scrollregion=(min_x, 0, max_x, max_y + 50))
            self._canvas.xview_moveto(0)

    def _draw_node_recursive(self, node: AncestorNode | None) -> None:
        """Dessine un nœud et ses descendants (parents) récursivement.

        Le traversal atteint toujours toutes les générations, mais seuls
        les nœuds dans la fenêtre visible
        ([generation_offset, generation_offset + VISIBLE_GENERATIONS)) sont
        dessinés. Un bouton ">" apparaît à droite des nœuds de la dernière
        génération visible qui possèdent encore des parents.
        """
        if node is None or self._canvas is None:
            return
        is_visible = (
            self._generation_offset
            <= node.generation
            < self._generation_offset + self.VISIBLE_GENERATIONS
        )
        if is_visible:
            x, y = self._node_positions[id(node)]
            last_visible_gen = self._generation_offset + self.VISIBLE_GENERATIONS - 1
            is_last_visible = node.generation == last_visible_gen
            show_expand = is_last_visible and (
                node.father is not None or node.mother is not None
            )
            self._draw_single_node(node, x, y, show_expand_button=show_expand)
            if not is_last_visible:
                if node.father is not None or node.mother is not None:
                    self._draw_connections(node)
        # Toujours traverser les enfants, même si le nœud courant n'est pas
        # visible, afin d'atteindre les générations filtrées en amont.
        if node.father is not None:
            self._draw_node_recursive(node.father)
        if node.mother is not None:
            self._draw_node_recursive(node.mother)

    @staticmethod
    def _sex_color(sex: str | None) -> str:
        """Retourne la couleur de fond selon le sexe de l'individu."""
        if sex == "M":
            # Bleu des garçons plus sombre pour meilleure lisibilité.
            return "#99ccff"
        if sex == "F":
            return "#ffcce5"
        return COLORS["surface"]

    @staticmethod
    def _fit_name(name: str, font: tkfont.Font, max_width: int) -> str:
        """Tronque un nom en supprimant les derniers prénoms s'il dépasse.

        Le nom de famille et le(s) premier(s) prénom(s) sont conservés ; on
        retire les derniers prénoms un par un jusqu'à ce que le texte tienne,
        puis on ajoute des points de suspension. Si même le nom de famille
        dépasse, il est tronqué caractère par caractère.
        """
        if font.measure(name) <= max_width:
            return name
        parts = name.split()
        while len(parts) > 1 and font.measure(" ".join(parts) + "...") > max_width:
            parts.pop()
        if len(parts) == 1 and font.measure(parts[0] + "...") > max_width:
            base = parts[0]
            while base and font.measure(base + "...") > max_width:
                base = base[:-1]
            parts[0] = base
        return " ".join(parts) + "..."

    def _draw_rounded_rect(
        self, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs
    ) -> int:
        """Dessine un rectangle aux coins arrondis sur le canvas."""
        canvas = self._canvas
        if canvas is None:
            return 0
        radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def _load_photo(self, photo_path: str | None) -> Any:
        """Charge une image depuis le chemin donné, résolu par rapport à base_path."""
        if not photo_path or Image is None or ImageTk is None:
            return None
        key = photo_path
        if key in self._photo_images:
            return self._photo_images[key]
        try:
            resolved = photo_path
            if self.base_path and not os.path.isabs(photo_path):
                resolved = os.path.join(self.base_path, photo_path)
            resolved = os.path.realpath(resolved)
            if not os.path.isfile(resolved):
                logger.warning("Photo introuvable: %s", photo_path)
                return None
            img = Image.open(resolved)
            img.thumbnail((self.NODE_WIDTH // 3, self.NODE_HEIGHT))
            photo = ImageTk.PhotoImage(img)
            self._photo_images[key] = photo
            return photo
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Echec chargement photo %s: %s", photo_path, exc)
            return None

    def _draw_single_node(
        self, node: AncestorNode, x: int, y: int, show_expand_button: bool = False
    ) -> None:
        """Dessine un seul nœud (rectangle + texte) et enregistre son item."""
        if self._canvas is None:
            return
        x1 = x - self.NODE_WIDTH // 2
        y1 = y - self.NODE_HEIGHT // 2
        x2 = x + self.NODE_WIDTH // 2
        y2 = y + self.NODE_HEIGHT // 2

        fill_color = self._sex_color(node.sex)
        self._draw_rounded_rect(
            x1,
            y1,
            x2,
            y2,
            radius=10,
            fill=fill_color,
            outline=COLORS["text"],
            width=2,
            tags=("node",),
        )

        # Témoin de décès : barre oblique en haut à gauche, touche les bords haut
        # et gauche du cadre. Appliqué à toutes les générations.
        if node.death_date:
            self._canvas.create_line(
                x1,
                y1 + 12,
                x1 + 12,
                y1,
                fill="#000000",
                width=4,
                tags=("node",),
            )

        # La zone d'informations occupe 3/3 de la boîte quand il n'y a pas de
        # photo (les textes ne wrapent pas), sinon 2/3 pour laisser la place à
        # la photo sur le tiers droit.
        has_photo = node.generation < 5 and node.photo_path
        photo_x1 = x2 - self.NODE_WIDTH // 3 if has_photo else x2
        text_left = x1 + self.NODE_PADDING_X
        text_right = photo_x1 if has_photo else x2
        text_width = text_right - text_left - self.NODE_PADDING_X

        name_font = tkfont.Font(font=self.NAME_FONT)
        display_name = self._fit_name(node.name, name_font, max(0, text_width))

        self._canvas.create_text(
            text_left,
            y1 + self.NODE_PADDING_Y,
            text=display_name,
            font=self.NAME_FONT,
            fill=COLORS["text"],
            width=0,
            tags=("node",),
            anchor="nw",
            justify="left",
        )
        # La date de naissance ne s'affiche pas à la 5e génération, ni son
        # symbole. La date de décès et son symbole s'affichent à toutes les
        # générations quand la date est connue.
        if node.generation < 4 and node.birth_date:
            self._canvas.create_text(
                text_left,
                y1 + self.NODE_PADDING_Y + 18,
                text=f"* {node.birth_date}",
                font=("Segoe UI", 8),
                fill=COLORS["muted_text"],
                width=0,
                tags=("node",),
                anchor="nw",
                justify="left",
            )
        elif node.generation < 4:
            self._canvas.create_text(
                text_left,
                y1 + self.NODE_PADDING_Y + 18,
                text="*",
                font=("Segoe UI", 8),
                fill=COLORS["muted_text"],
                tags=("node",),
                anchor="nw",
                justify="left",
            )
        if node.death_date:
            self._canvas.create_text(
                text_left,
                y1 + self.NODE_PADDING_Y + 36,
                text=f"✝ {node.death_date}",
                font=("Segoe UI", 8),
                fill=COLORS["muted_text"],
                width=0,
                tags=("node",),
                anchor="nw",
                justify="left",
            )
        else:
            self._canvas.create_text(
                text_left,
                y1 + self.NODE_PADDING_Y + 36,
                text="✝",
                font=("Segoe UI", 8),
                fill=COLORS["muted_text"],
                tags=("node",),
                anchor="nw",
                justify="left",
            )

        # Quand il y a une photo, elle est justifiée à droite : son bord droit
        # touche le bord droit du nœud, et le fond de la zone photo reprend la
        # couleur du sexe (pas de fond distinct, pas de bord blanc). Quand il
        # n'y a pas de photo, toute la boîte garde la couleur du sexe.
        if node.generation < 5 and node.photo_path:
            photo = self._load_photo(node.photo_path)
            if photo is not None:
                self._canvas.create_image(
                    x2,
                    y1 + self.NODE_HEIGHT // 2,
                    image=photo,
                    anchor="e",
                    tags=("photo",),
                )

        # Bouton « > » à droite du nœud de la dernière génération visible
        # quand cet individu a encore des parents. Un clic décale l'arbre
        # d'une génération vers la gauche pour révéler la génération suivante.
        if show_expand_button:
            self._draw_expand_button(x, y, node.pointer or "")

        # L'encadrement homogène du nœud est assuré par le rounded_rect dessiné
        # en début de _draw_single_node (bordure width=2 sur tout le périmètre).
        # Le rectangle cliquable ci-dessous n'a ni remplissage ni bordure :
        # seul le nœud possède l'encadrement visible.
        item_id = self._canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill="",
            outline="",
            tags=("clickable", node.pointer or ""),
        )
        self._node_items[id(node)] = item_id
        if node.pointer:
            self._canvas.tag_bind(
                item_id,
                "<Button-1>",
                self._make_click_handler(node.pointer),
            )
            self._canvas.tag_bind(
                item_id,
                "<Enter>",
                self._on_enter,
            )
            self._canvas.tag_bind(
                item_id,
                "<Leave>",
                self._on_leave,
            )

    def _draw_connections(self, node: AncestorNode) -> None:
        """Dessine les lignes reliant un nœud à ses parents en angle droit."""
        canvas = self._canvas
        if canvas is None:
            return
        x, y = self._node_positions[id(node)]
        parent_x = x + self.HORIZONTAL_SPACING
        parent_left_x = parent_x - self.NODE_WIDTH // 2
        offset_x = parent_left_x - self.CONNECTOR_OFFSET

        def draw_connection(child_y: int) -> None:
            """Trace un connecteur en angle droit vers le milieu gauche de l'enfant."""
            canvas.create_line(
                x + self.NODE_WIDTH // 2,
                y,
                offset_x,
                y,
                fill=COLORS["text"],
                width=2,
                tags=("connection",),
            )
            canvas.create_line(
                offset_x,
                y,
                offset_x,
                child_y,
                fill=COLORS["text"],
                width=2,
                tags=("connection",),
            )
            canvas.create_line(
                offset_x,
                child_y,
                parent_left_x,
                child_y,
                fill=COLORS["text"],
                width=2,
                tags=("connection",),
            )

        if node.father is not None:
            father_y = self._node_positions[id(node.father)][1]
            draw_connection(father_y)
        if node.mother is not None:
            mother_y = self._node_positions[id(node.mother)][1]
            draw_connection(mother_y)

        if node.father is not None and node.mother is not None and node.marriage_date:
            marriage_text = f"oo {node.marriage_date}"
            marriage_x = offset_x + self.CONNECTOR_OFFSET // 2
            available_width = (parent_x + self.NODE_WIDTH // 2) - marriage_x
            if available_width < 60:
                return
            font = tkfont.Font(font=("Segoe UI", 8))
            text_width = font.measure(marriage_text)
            if text_width > available_width:
                return
            canvas.create_text(
                marriage_x,
                y,
                text=marriage_text,
                font=("Segoe UI", 8),
                fill=COLORS["muted_text"],
                tags=("connection",),
                anchor="w",
            )

    def _set_cursor(self, cursor: str) -> None:
        """Change le curseur du canvas s'il existe."""
        canvas = self._canvas
        if canvas is not None:
            canvas.config(cursor=cursor)

    def _on_enter(self, event: Any) -> None:
        """Passe le curseur en main sur survol d'un nœud cliquable."""
        self._set_cursor("hand2")

    def _on_leave(self, event: Any) -> None:
        """Rétablit le curseur par défaut à la sortie d'un nœud."""
        self._set_cursor("")

    def _make_click_handler(self, pointer: str) -> Callable[[Any], None]:
        """Retourne un gestionnaire de clic typé pour un pointeur donné."""

        def handler(event: Any) -> None:
            """Gère le clic sur un nœud : recentre l'arbre sur le pointeur."""
            self._on_node_click(pointer)

        return handler

    def _make_expand_handler(self, pointer: str) -> Callable[[Any], None]:
        """Retourne un gestionnaire de clic typé pour le bouton « > » d'un pointeur."""

        def handler(event: Any) -> None:
            """Gère le clic sur le bouton « > » : recentre sur le parent de la racine."""
            self._on_expand_click(pointer)

        return handler

    def _close_children_window(self, _event: Any = None) -> None:
        """Ferme la fenêtre des enfants si elle est ouverte."""
        if self._children_window is not None and self._children_window.winfo_exists():
            self._children_window.destroy()
        self._children_window = None

    def _on_node_click(self, pointer: str) -> None:
        """Réagit au clic sur un nœud : sélectionne l'individu et recentre l'arbre."""
        self._close_children_window()
        if not pointer:
            return
        if self.on_individual_selected is not None:
            self.on_individual_selected(pointer)
        self.load_tree(pointer)

    def _on_expand_click(self, pointer: str) -> None:
        """Recentre l'arbre sur le parent de la racine dans la lignée du nœud.

        Cliquer sur « > » à droite d'un nœud de la dernière génération visible
        est équivalent à cliquer sur l'ancêtre de ce nœud qui est le parent
        direct de la racine courante (ex: « > » à droite de I19 recentre sur
        I2, car I19 -> I8 -> I4 -> I2 -> I1(racine)).
        """
        if not pointer or self._root_node is None:
            return
        target = self._find_child_of_root_toward(self._root_node, pointer)
        if target is not None:
            self._on_node_click(target)

    def _find_child_of_root_toward(
        self, root: AncestorNode, target_pointer: str
    ) -> str | None:
        """Retourne le pointeur de l'enfant direct de root ancêtre de target_pointer."""
        if root.pointer == target_pointer:
            return None
        for parent in (root.father, root.mother):
            if parent is not None and self._is_ancestor(parent, target_pointer):
                return parent.pointer
        return None

    def _is_ancestor(self, node: AncestorNode | None, target_pointer: str) -> bool:
        """Vérifie si node est target_pointer ou l'un de ses ancêtres."""
        if node is None:
            return False
        if node.pointer == target_pointer:
            return True
        return self._is_ancestor(node.father, target_pointer) or self._is_ancestor(
            node.mother, target_pointer
        )

    def _root_children_pointers(self) -> list[str]:
        """Retourne les pointeurs des enfants de l'individu racine.

        Tous les enfants de toutes les familles (FAMS) de la racine sont
        retournés, quelque soit l'époux ou l'épouse. La recherche se fait
        via le FAMC des individus (robuste, fonctionne même quand la
        famille ne porte pas de tag CHIL).
        """
        if self._current_pointer is None:
            return []
        controller = self.controller_provider()
        individual = controller.get_individual(self._current_pointer)
        if individual is None:
            return []
        root_fams = set(individual.fams or [])
        if not root_fams:
            return []
        children: list[str] = []
        seen: set[str] = set()
        for child in controller.get_entity_list("INDI") or []:
            famc = child.famc
            if famc in root_fams and child.pointer not in seen:
                seen.add(child.pointer)
                children.append(child.pointer)
        return children

    def _draw_children_button(
        self, x: int, y: int, children_pointers: list[str]
    ) -> None:
        """Dessine le bouton « < » à gauche du nœud racine."""
        if self._canvas is None or not children_pointers:
            return
        canvas = self._canvas
        btn_x2 = x - self.NODE_WIDTH // 2 - 8
        btn_x1 = btn_x2 - self.BUTTON_SIZE
        btn_y1 = y - self.BUTTON_SIZE // 2
        btn_y2 = btn_y1 + self.BUTTON_SIZE
        btn_id = canvas.create_rectangle(
            btn_x1,
            btn_y1,
            btn_x2,
            btn_y2,
            fill=COLORS["surface"],
            outline=COLORS["text"],
            width=1,
            tags=("children_button",),
        )
        text_id = canvas.create_text(
            (btn_x1 + btn_x2) // 2,
            (btn_y1 + btn_y2) // 2,
            text="<",
            font=("Segoe UI", 10, "bold"),
            fill=COLORS["text"],
            tags=("children_button",),
        )

        def handler(event: Any) -> None:
            """Ouvre ou ferme la fenêtre des enfants de la racine près du bouton."""
            if (
                self._children_window is not None
                and self._children_window.winfo_exists()
            ):
                self._close_children_window()
                return
            cx = canvas.winfo_rootx() + (btn_x1 + btn_x2) // 2 - int(canvas.canvasx(0))
            cy = canvas.winfo_rooty() + (btn_y1 + btn_y2) // 2 - int(canvas.canvasy(0))
            self._show_children_window(children_pointers, cx, cy)

        self._canvas.tag_bind(btn_id, "<Button-1>", handler)
        self._canvas.tag_bind(text_id, "<Button-1>", handler)

    def _show_children_window(
        self, children_pointers: list[str], cx: int, cy: int
    ) -> None:
        """Ouvre une petite fenêtre listant les enfants de la racine.

        Fenêtre sans bordure ni bouton, uniquement une liste. Un clic sur un
        enfant recentre l'arbre sur lui ; un clic à côté ferme la fenêtre.
        """
        controller = self.controller_provider()
        win = tk.Toplevel(self)
        win.overrideredirect(True)
        listbox = tk.Listbox(win)
        listbox.pack(fill="both", expand=True)
        for child_pointer in children_pointers:
            individual = controller.get_individual(child_pointer)
            name = (
                self._format_individual_name(
                    individual.name if individual is not None else None
                )
                or child_pointer
            )
            listbox.insert("end", name)
        listbox.focus_set()
        # Ajuste la taille de la fenêtre à son contenu (listbox + petite marge).
        win.update_idletasks()
        first_bbox = listbox.bbox(0)
        line_height = first_bbox[3] - first_bbox[1] if first_bbox else 16
        # Hauteur = un item supplémentaire pour donner de l'air à la sélection.
        height = (len(children_pointers) + 1) * line_height + 4
        # Largeur = contenu + marge généreuse pour les noms longs.
        width = listbox.winfo_reqwidth() + 150
        # Fenêtre centrée horizontalement sur le bouton et adjacente à son
        # bord inférieur (le bord supérieur de la fenêtre touche le bouton).
        x = cx - width // 2
        y = cy + self.BUTTON_SIZE // 2
        win.geometry("%dx%d+%d+%d" % (width, height, x, y))

        def close_window() -> None:
            """Ferme la fenêtre des enfants."""
            if win.winfo_exists():
                win.destroy()
            self._children_window = None

        def on_select(_event: Any) -> None:
            """Sélectionne l'enfant choisi et recentre l'arbre sur lui."""
            sel = listbox.curselection()
            if not sel:
                return
            child_pointer = children_pointers[sel[0]]
            close_window()
            self.load_tree(child_pointer)

        listbox.bind("<<ListboxSelect>>", on_select)
        self._children_window = win

    def _draw_expand_button(self, x: int, y: int, pointer: str) -> None:
        """Dessine le bouton « > » à droite d'un nœud de dernière génération.

        Ce bouton permet de décaler l'arbre d'une génération vers la gauche
        pour révéler la génération suivante d'ancêtres.
        """
        if self._canvas is None:
            return
        btn_x1 = x + self.NODE_WIDTH // 2 + 8
        btn_x2 = btn_x1 + self.BUTTON_SIZE
        btn_y1 = y - self.BUTTON_SIZE // 2
        btn_y2 = btn_y1 + self.BUTTON_SIZE
        btn_id = self._canvas.create_rectangle(
            btn_x1,
            btn_y1,
            btn_x2,
            btn_y2,
            fill=COLORS["surface"],
            outline=COLORS["text"],
            width=1,
            tags=("expand_button",),
        )
        text_id = self._canvas.create_text(
            (btn_x1 + btn_x2) // 2,
            (btn_y1 + btn_y2) // 2,
            text=">",
            font=("Segoe UI", 10, "bold"),
            fill=COLORS["text"],
            tags=("expand_button",),
        )
        self._canvas.tag_bind(btn_id, "<Button-1>", self._make_expand_handler(pointer))
        self._canvas.tag_bind(text_id, "<Button-1>", self._make_expand_handler(pointer))

    def apply_theme(self) -> None:
        """Re-applique les couleurs du thème courant au canvas."""
        if self._canvas is not None:
            self._canvas.configure(background=COLORS["background"])
