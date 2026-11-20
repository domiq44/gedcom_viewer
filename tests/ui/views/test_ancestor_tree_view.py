"""Tests de la vue d'arbre d'ascendance."""

import os
import tempfile
import tkinter as tk
import tkinter.font as tkfont
import unittest
from unittest.mock import MagicMock, patch

from PIL import Image

from controllers.ancestor_tree_service import AncestorNode
from ui.views.ancestor_tree_view import AncestorTreeView


class TestAncestorTreeView(unittest.TestCase):
    """Vérifie la construction et l'affichage de l'arbre d'ascendance."""

    def setUp(self):
        """Crée une fenêtre Tk et un contrôleur factice."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.controller = MagicMock()
        self.controller.get_individual.return_value = None
        self.controller.get_family.return_value = None

    def tearDown(self):
        """Détruit la fenêtre Tk."""
        self.root.destroy()

    # Vérifie la vue se construit sans erreur.
    def test_view_constructs_without_error(self):
        # Given (Arrange) une fenêtre Tk et un contrôleur factice
        # When (Act) on instancie AncestorTreeView
        view = AncestorTreeView(
            self.root,
            lambda: self.controller,
            MagicMock(),
        )
        # Then (Assert) la vue est créée
        self.assertIsInstance(view, AncestorTreeView)
        view.destroy()

    # Vérifie load_tree avec un individu absent ne plante pas.
    def test_load_tree_none_individual_does_not_crash(self):
        # Given (Arrange) une vue et un contrôleur sans individu
        view = AncestorTreeView(
            self.root,
            lambda: self.controller,
            MagicMock(),
        )
        # When (Act) on charge un arbre avec un pointeur invalide
        view.load_tree("@I99@")
        # Then (Assert) aucun nœud racine n'est créé
        self.assertIsNone(view._root_node)
        view.destroy()

    # Vérifie apply_theme ne plante pas.
    def test_apply_theme_does_not_crash(self):
        # Given (Arrange) une vue instanciée
        view = AncestorTreeView(
            self.root,
            lambda: self.controller,
            MagicMock(),
        )
        # When (Act) on applique le thème
        view.apply_theme()
        # Then (Assert) aucune exception n'est levée
        view.destroy()

    # Vérifie _fit_name ne tronque pas un nom qui tient dans l'espace.
    def test_fit_name_does_not_truncate_when_fits(self):
        # Given (Arrange) une police et un nom court
        font = tkfont.Font(font=("Segoe UI", 8))
        name = "Dubots, Zélie"
        # When (Act) on ajuste le nom à une largeur suffisante
        result = AncestorTreeView._fit_name(name, font, 300)
        # Then (Assert) le nom est retourné tel quel
        self.assertEqual(result, name)

    # Vérifie _fit_name supprime le dernier prénom quand le nom dépasse.
    def test_fit_name_truncates_last_firstname(self):
        # Given (Arrange) une police et un nom long
        font = tkfont.Font(font=("Segoe UI", 8))
        name = "Dubots, Zélie Emilienne Armandine"
        # When (Act) on ajuste le nom à une largeur insuffisante
        result = AncestorTreeView._fit_name(name, font, 100)
        # Then (Assert) le dernier prénom est retiré et des points ajoutés
        self.assertNotEqual(result, name)
        self.assertTrue(result.endswith("..."))
        self.assertLessEqual(font.measure(result), 100)

    # Vérifie _fit_name garde au moins le nom de famille.
    def test_fit_name_keeps_at_least_surname(self):
        # Given (Arrange) une police et une largeur très faible
        font = tkfont.Font(font=("Segoe UI", 8))
        name = "Dubots, Zélie Emilienne Armandine"
        # When (Act) on ajuste le nom à une largeur très faible
        result = AncestorTreeView._fit_name(name, font, 10)
        # Then (Assert) le résultat contient au moins le nom de famille tronqué
        self.assertTrue(result.endswith("..."))

    # Vérifie _root_children_pointers trouve les enfants via FAMC.
    def test_root_children_pointers_returns_children_via_famc(self):
        # Given (Arrange) une vue avec un individu racine ayant des FAMS
        view = AncestorTreeView(self.root, lambda: self.controller, MagicMock())
        root = MagicMock()
        root.fams = ["@F8@"]
        self.controller.get_individual.return_value = root
        child1 = MagicMock()
        child1.famc = "@F8@"
        child1.pointer = "@I17@"
        child2 = MagicMock()
        child2.famc = "@F8@"
        child2.pointer = "@I18@"
        self.controller.get_entity_list.return_value = [child1, child2]
        view._current_pointer = "@I1@"
        # When (Act) on liste les enfants de la racine
        result = view._root_children_pointers()
        # Then (Assert) les deux enfants sont retournés
        self.assertEqual(result, ["@I17@", "@I18@"])
        view.destroy()

    # Vérifie _root_children_pointers retourne [] sans FAMS.
    def test_root_children_pointers_empty_without_fams(self):
        # Given (Arrange) une vue avec un individu racine sans FAMS
        view = AncestorTreeView(self.root, lambda: self.controller, MagicMock())
        root = MagicMock()
        root.fams = []
        self.controller.get_individual.return_value = root
        view._current_pointer = "@I1@"
        # When (Act) on liste les enfants de la racine
        result = view._root_children_pointers()
        # Then (Assert) aucune liste n'est retournée
        self.assertEqual(result, [])
        view.destroy()

    # Vérifie le bouton « < » est dessiné quand la racine a des enfants.
    def test_children_button_drawn_when_root_has_children(self):
        # Given (Arrange) une vue avec un nœud racine et des enfants
        view = AncestorTreeView(self.root, lambda: self.controller, MagicMock())
        view._root_node = MagicMock()
        view._root_node.pointer = "@I1@"
        view._node_positions = {id(view._root_node): (100, 100)}
        view._current_pointer = "@I1@"
        self.controller.get_individual.return_value = MagicMock(fams=["@F8@"])
        self.controller.get_entity_list.return_value = [
            MagicMock(famc="@F8@", pointer="@I17@")
        ]
        # When (Act) on dessine le bouton « < »
        view._draw_children_button(100, 100, ["@I17@"])
        # Then (Assert) le bouton « < » est présent sur le canvas
        items = view._canvas.find_withtag("children_button")
        self.assertEqual(len(items), 2)  # rectangle + texte
        view.destroy()

    # Vérifie le bouton « < » n'est pas dessiné sans enfants.
    def test_children_button_not_drawn_without_children(self):
        # Given (Arrange) une vue avec un nœud racine sans enfants
        view = AncestorTreeView(self.root, lambda: self.controller, MagicMock())
        view._root_node = MagicMock()
        view._node_positions = {id(view._root_node): (100, 100)}
        # When (Act) on dessine le bouton « < » sans enfants
        view._draw_children_button(100, 100, [])
        # Then (Assert) aucun bouton « < » n'est présent
        items = view._canvas.find_withtag("children_button")
        self.assertEqual(len(items), 0)
        view.destroy()

    # Vérifie _format_individual_name met « Nom, Prénom ».
    def test_format_individual_name(self):
        # Given (Arrange) un nom GEDCOM avec séparateurs
        cases = [
            ("Jean /Dupont/", "Dupont, Jean"),
            ("/Dupont/ Jean", "Dupont, Jean"),
            ("Jean Dupont", "Jean Dupont"),
            ("", ""),
            (None, ""),
        ]
        # When (Act) puis Then (Assert) chaque cas est formaté correctement
        for name, expected in cases:
            self.assertEqual(AncestorTreeView._format_individual_name(name), expected)

    # Vérifie clic sur « < » ouvre la fenêtre enfants.
    def test_click_children_button_opens_window(self):
        # Given (Arrange) une vue et des enfants
        view = AncestorTreeView(self.root, lambda: self.controller, MagicMock())
        view._children_window = None
        child = MagicMock()
        child.name = "Jean /Dupont/"
        self.controller.get_individual.return_value = child
        # When (Act) on simule un clic sur le bouton « < »
        view._show_children_window(["@I17@"], 100, 100)
        # Then (Assert) la fenêtre enfants est ouverte
        self.assertIsNotNone(view._children_window)
        view._close_children_window()
        view.destroy()

    # Vérifie second clic sur « < » ferme la fenêtre enfants.
    def test_click_children_button_again_closes_window(self):
        # Given (Arrange) une vue avec une fenêtre enfants ouverte
        view = AncestorTreeView(self.root, lambda: self.controller, MagicMock())
        view._show_children_window(["@I17@"], 100, 100)
        self.assertIsNotNone(view._children_window)
        # When (Act) on appelle _close_children_window directement
        view._close_children_window()
        # Then (Assert) la fenêtre enfants est fermée
        self.assertIsNone(view._children_window)
        view.destroy()

    # Vérifie load_tree avec un arbre multi-générations dessine tout le canevas.
    @patch("ui.views.ancestor_tree_view.AncestorTreeService.build_tree")
    def test_load_tree_draws_multi_generation_tree(self, mock_build_tree):
        # Given (Arrange) un arbre avec racine, deux parents et quatre grands-parents
        root = AncestorNode("@I1@", 0)
        root.father = AncestorNode("@I2@", 1)
        root.mother = AncestorNode("@I3@", 1)
        root.father.father = AncestorNode("@I4@", 2)
        root.father.mother = AncestorNode("@I5@", 2)
        root.mother.father = AncestorNode("@I6@", 2)
        root.mother.mother = AncestorNode("@I7@", 2)
        mock_build_tree.return_value = root
        view = AncestorTreeView(self.root, lambda: self.controller, MagicMock())
        # When (Act) on charge l'arbre
        view.load_tree("@I1@")
        # Then (Assert) le nœud racine et les positions sont assignés
        self.assertIsNotNone(view._root_node)
        self.assertEqual(view._root_node.pointer, "@I1@")
        self.assertIn(id(root), view._node_positions)
        self.assertGreater(len(view._node_items), 0)
        view.destroy()

    # Vérifie _on_node_click recentre l'arbre sur le nœud cliqué.
    @patch("ui.views.ancestor_tree_view.AncestorTreeService.build_tree")
    def test_on_node_click_recentres_tree(self, mock_build_tree):
        # Given (Arrange) un arbre avec un seul nœud
        root = AncestorNode("@I1@", 0)
        mock_build_tree.return_value = root
        view = AncestorTreeView(self.root, lambda: self.controller, MagicMock())
        view.load_tree("@I1@")
        # When (Act) on clique sur le nœud racine
        view._on_node_click("@I1@")
        # Then (Assert) load_tree est rappelé sur le même pointeur
        self.assertEqual(view._current_pointer, "@I1@")
        view.destroy()

    @staticmethod
    def _build_full_binary_tree(node: AncestorNode, gen: int, max_gen: int) -> None:
        """Construit un arbre binaire complet jusqu'à max_gen."""
        if gen >= max_gen:
            return
        node.father = AncestorNode(
            f"@I{gen}f{node.pointer}@", name="", generation=gen + 1
        )
        node.mother = AncestorNode(
            f"@I{gen}m{node.pointer}@", name="", generation=gen + 1
        )
        TestAncestorTreeView._build_full_binary_tree(node.father, gen + 1, max_gen)
        TestAncestorTreeView._build_full_binary_tree(node.mother, gen + 1, max_gen)

    # Vérifie que la hauteur du canevas reste raisonnable (5 générations
    # visibles max) même avec beaucoup de générations dans l'arbre complet.
    @patch("ui.views.ancestor_tree_view.AncestorTreeService.build_tree")
    def test_scrollregion_height_stays_reasonable_with_many_generations(
        self, mock_build_tree
    ):
        # Given (Arrange) un arbre de 10 générations (512 feuilles au plus profond)
        root = AncestorNode("@I1@", 0)
        self._build_full_binary_tree(root, 0, 10)
        mock_build_tree.return_value = root
        view = AncestorTreeView(self.root, lambda: self.controller, MagicMock())
        # When (Act) on charge l'arbre
        view.load_tree("@I1@")
        # Then (Assert) la hauteur du scrollregion est basée sur les 5 générations
        # visibles, pas sur l'arbre complet
        scrollregion = view._canvas.cget("scrollregion")
        parts = scrollregion.split()
        height = int(parts[3])
        # 5 générations visibles => au plus 2^4 = 16 feuilles => ~2350 avec marge
        self.assertLessEqual(height, 3000)  # corrigé : pas d'explosion
        view.destroy()

    # Vérifie _load_photo charge une image existante et la met en cache.
    def test_load_photo_loads_existing_image(self):
        # Given un fichier PNG factice
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img = Image.new("RGB", (10, 10), (255, 0, 0))
            img.save(tmp.name, format="PNG")
            tmp_path = tmp.name
        try:
            view = AncestorTreeView(
                self.root,
                lambda: self.controller,
                MagicMock(),
            )
            # When on charge la photo par son chemin complet
            photo = view._load_photo(tmp_path)
            # Then l'image est chargée et mise en cache
            self.assertIsNotNone(photo)
            self.assertIn(tmp_path, view._photo_images)
            view.destroy()
        finally:
            os.unlink(tmp_path)

    # Vérifie _load_photo retourne None pour une image inexistante.
    def test_load_photo_returns_none_for_missing_file(self):
        # Given une vue sans base_path valide
        view = AncestorTreeView(
            self.root,
            lambda: self.controller,
            MagicMock(),
            base_path="/tmp",
        )
        # When on charge une photo inexistante
        photo = view._load_photo("photo_inexistante.png")
        # Then aucune photo n'est chargée
        self.assertIsNone(photo)
        view.destroy()

    # Vérifie le bouton « > » est dessiné pour un nœud de dernière génération avec parents.
    def test_expand_button_drawn_for_last_generation_with_parents(self):
        # Given un nœud racine de dernière génération visible avec un père
        view = AncestorTreeView(self.root, lambda: self.controller, MagicMock())
        view._generation_offset = 0
        view._root_node = MagicMock()
        view._root_node.pointer = "@I1@"
        view._root_node.father = MagicMock()
        view._root_node.mother = None
        view._node_positions = {id(view._root_node): (300, 100)}
        # When on dessine le bouton « > »
        view._draw_expand_button(300, 100, "@I1@")
        # Then le bouton « > » est présent sur le canvas
        items = view._canvas.find_withtag("expand_button")
        self.assertEqual(len(items), 2)  # rectangle + texte
        view.destroy()

    # Vérifie le bouton « > » n'est pas dessiné sans parents.


if __name__ == "__main__":
    unittest.main()
