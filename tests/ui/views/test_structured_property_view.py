"""Tests de la base des fiches structurées."""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ui.i18n import Translator
from ui.themes import COLORS
from ui.views.structured_property_view import StructuredPropertyView


class TestStructuredPropertyView(unittest.TestCase):
    """Vérifie les lignes, événements, libellés et le défilement."""

    def setUp(self):
        """Crée une fenêtre racine et une fiche structurée."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = Translator("fr")
        self.view = StructuredPropertyView(
            self.root,
            Mock(),
            self.translator,
            "INDI",
            "view.events",
        )

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie row records value and pointer link.
    def test_row_records_value_and_pointer_link(self):
        # Given une section de fiche
        section = self.view._section("Titre")

        # When on ajoute une ligne avec un pointeur
        self.view._row(section, 0, "Libellé", "Valeur", pointer="@I1@")

        # Then la valeur du pointeur et le lien sont mémorisés
        self.assertEqual(self.view._section_rows[section], [("Libellé", "@I1@")])
        self.assertIn("@I1@", self.view.links)
        self.assertEqual(len(self.view.value_widgets), 1)
        self.assertEqual(len(self.view.tag_widgets), 1)

    # Vérifie identity displays the entity pointer.
    def test_identity_displays_the_entity_pointer(self):
        # Given une entité avec un pointeur
        entity = SimpleNamespace(pointer="@I1@")
        # When on affiche l'identité
        self.view._display_identity(entity)
        # Then un libellé secondaire contient le pointeur
        labels = self.view.content.winfo_children()
        self.assertEqual([label.cget("text") for label in labels], ["@I1@"])

    # Vérifie identity falls back to an empty pointer.
    def test_identity_falls_back_to_empty_pointer(self):
        # Given une entité sans pointeur
        entity = SimpleNamespace()
        # When on affiche l'identité
        self.view._display_identity(entity)
        # Then un libellé vide est créé
        labels = self.view.content.winfo_children()
        self.assertEqual([label.cget("text") for label in labels], [""])

    # Vérifie event parts handles dict and object.
    def test_event_parts_handles_dict_and_object(self):
        # Given un événement dictionnaire et un événement objet
        as_dict = {"tag": "EVEN", "value": "x", "children": [{"tag": "TYPE"}]}
        as_object = SimpleNamespace(tag="EVEN", value="y", details=[("TYPE", "z")])

        # When on décompose les deux formes
        # Then le tag, la valeur et les enfants sont normalisés
        self.assertEqual(
            self.view._event_parts(as_dict),
            ("EVEN", "x", [{"tag": "TYPE"}]),
        )
        self.assertEqual(
            self.view._event_parts(as_object),
            ("EVEN", "y", [("TYPE", "z")]),
        )

    # Vérifie tag label uses translations and fallback.
    def test_tag_label_uses_translations_and_fallback(self):
        # Given un traducteur français
        # When on demande les libellés
        # Then les tags connus sont traduits, les inconnus passent par le repli
        self.assertEqual(
            self.view._tag_label("BIRT"), self.translator.get("view.birth_date")
        )
        self.assertEqual(
            self.view._tag_label("UNKNOWN"),
            self.translator.get("view.other_gedcom_tag", tag="UNKNOWN"),
        )
        self.assertEqual(self.view._tag_label("_CUSTOM"), "_CUSTOM")

    # Vérifie render event creates rows for root and children.
    def test_render_event_creates_rows_for_root_and_children(self):
        # Given une section et un événement avec un enfant
        section = self.view._section("Événements")
        event = {
            "tag": "EVEN",
            "value": "",
            "children": [{"tag": "TYPE", "value": "Militaire"}],
        }

        # When on rend l'événement
        next_row = self.view._render_event(section, 0, event)

        # Then deux lignes sont créées
        self.assertEqual(next_row, 2)
        self.assertEqual(len(self.view._section_rows[section]), 2)

    # Vérifie on mousewheel scrolls canvas.
    def test_on_mousewheel_scrolls_canvas(self):
        # Given une fiche structurée
        self.view.canvas.yview_scroll = Mock()

        # When on reçoit un événement de molette Linux
        self.view._on_mousewheel(SimpleNamespace(num=4, delta=0))

        # Then le canvas défile vers le haut
        self.view.canvas.yview_scroll.assert_called_once_with(-1, "units")

    # Vérifie clear resets content and links.
    def test_clear_resets_content_and_links(self):
        # Given une fiche avec une ligne et un lien
        section = self.view._section("Titre")
        self.view._row(section, 0, "Libellé", "Valeur", pointer="@I1@")

        # When on efface la fiche
        self.view._clear()

        # Then les sections, liens et widgets sont réinitialisés
        self.assertEqual(self.view.sections, {})
        self.assertEqual(self.view.links, {})
        self.assertEqual(self.view.value_widgets, [])
        self.assertEqual(self.view.tag_widgets, [])

    # Vérifie display pointer uses resolver label.
    def test_display_pointer_uses_resolver_label(self):
        # Given un résolveur de pointeur et un résolveur de libellé
        self.view.set_pointer_resolver(lambda pointer: SimpleNamespace(title="Cible"))
        self.view.set_display_name_resolver(lambda entity, entity_type: "Jean")

        # When on affiche un pointeur
        # Then le libellé résolu est utilisé
        self.assertEqual(self.view._display_pointer("@I1@"), "Jean (@I1@)")

    # Vérifie display pointer returns raw when unresolved.
    def test_display_pointer_returns_raw_when_unresolved(self):
        # Given aucun résolveur
        # When on affiche un pointeur inconnu
        # Then le pointeur brut est renvoyé
        self.assertEqual(self.view._display_pointer("@I9@"), "@I9@")

    # Vérifie on mousewheel handles large delta.
    def test_on_mousewheel_handles_large_delta(self):
        # Given une fiche structurée
        self.view.canvas.yview_scroll = Mock()

        # When on reçoit un événement de molette avec un delta important
        self.view._on_mousewheel(SimpleNamespace(num=0, delta=120))

        # Then le canvas défile vers le haut
        self.view.canvas.yview_scroll.assert_called_once_with(-1, "units")

    # Vérifie resize content updates canvas width.
    def test_resize_content_updates_canvas_width(self):
        # Given une fiche structurée
        self.view.canvas.itemconfigure = Mock()

        # When on redimensionne le contenu
        self.view._resize_content(SimpleNamespace(width=320))

        # Then la largeur du canvas est mise à jour
        self.view.canvas.itemconfigure.assert_called_once_with(
            self.view._content_window, width=320
        )

    # Vérifie event parts handles object without tag.
    def test_event_parts_handles_object_without_tag(self):
        # Given un objet sans tag
        # When on décompose l'événement
        # Then aucune donnée n'est retournée
        self.assertEqual(self.view._event_parts(SimpleNamespace()), (None, None, []))

    # Vérifie tag label uses multimedia for object pointer.
    def test_tag_label_uses_multimedia_for_object_pointer(self):
        # Given un résolveur de pointeur OBJE
        self.view.set_pointer_resolver(lambda pointer: SimpleNamespace(tag="OBJE"))

        # When on demande le libellé d'un pointeur OBJE
        label = self.view._tag_label("ASSO", "@O1@")

        # Then le libellé multimédia est utilisé
        self.assertEqual(label, self.translator.get("view.multimedia"))

    # Vérifie tag label uses referenced individual for unknown pointer.
    def test_tag_label_uses_referenced_individual_for_unknown_pointer(self):
        # Given un résolveur de pointeur INDI
        self.view.set_pointer_resolver(lambda pointer: SimpleNamespace(tag="INDI"))

        # When on demande le libellé d'un tag inconnu avec pointeur INDI
        label = self.view._tag_label("CUSTOM", "@I1@")

        # Then le libellé d'individu référencé est utilisé
        self.assertEqual(label, self.translator.get("view.referenced_individual"))

    # Vérifie render event skips core date and place and normalizes tuples.
    def test_render_event_skips_core_date_and_place_and_normalizes_tuples(self):
        # Given un événement BIRT avec DATE, PLAC et un enfant tuple
        section = self.view._section("Naissance")
        event = {
            "tag": "BIRT",
            "value": "",
            "children": [
                {"tag": "DATE", "value": "1 JAN 1900"},
                {"tag": "PLAC", "value": ""},
                ("TYPE", "Militaire"),
            ],
        }

        # When on rend l'événement
        next_row = self.view._render_event(section, 0, event)

        # Then seuls les enfants non filtrés sont rendus
        self.assertEqual(next_row, 1)
        self.assertEqual(len(self.view._section_rows[section]), 1)
        self.assertEqual(self.view._section_rows[section][0][1], "Militaire")

    # Vérifie apply theme updates canvas background.
    def test_apply_theme_updates_canvas_background(self):
        # Given une fiche structurée
        # When on réapplique le thème
        self.view.apply_theme()
        # Then le canevas utilise la couleur courante
        self.assertEqual(self.view.canvas.cget("background"), COLORS["background"])


if __name__ == "__main__":
    unittest.main()
