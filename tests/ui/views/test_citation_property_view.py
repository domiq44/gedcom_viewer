"""Tests de la vue des citations."""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from ui.i18n import Translator
from ui.views.citation_property_view import CitationPropertyView


class TestCitationPropertyView(unittest.TestCase):
    """Vérifie les informations et détails d'une citation."""

    def setUp(self):
        """Crée une fenêtre racine et une vue de citation."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = Translator("fr")
        self.view = CitationPropertyView(self.root, Mock(), self.translator)

    def tearDown(self):
        """Détruit la fenêtre racine."""
        self.root.destroy()

    # Vérifie display renders information and details.
    def test_display_renders_information_and_details(self):
        # Given une citation avec page et rôle
        citation = SimpleNamespace(
            source_pointer="@S1@",
            owner_pointer="@I1@",
            owner_type="INDI",
            context_tag="BIRT",
            level=2,
            page="12",
            details=[
                {"tag": "PAGE", "value": "12", "level": 1},
                {"tag": "ROLE", "value": "Witness", "level": 2},
            ],
        )

        # When on affiche la citation
        self.view.display(citation)

        # Then les sections d'information et de détail sont présentes
        information = self.translator.get("view.citation_information")
        details = self.translator.get("view.citation_details")
        self.assertIn(information, self.view.sections)
        self.assertIn(details, self.view.sections)
        information_rows = self.view._section_rows[self.view.sections[information]]
        self.assertIn((self.translator.get("view.page"), "12"), information_rows)

    # Vérifie detail label joins tag path.
    def test_detail_label_joins_tag_path(self):
        # Given un chemin de tags
        # When on demande son libellé
        # Then chaque segment est traduit et joint par un slash
        self.assertEqual(
            self.view._detail_label("PAGE/ROLE"),
            f"{self.translator.get('view.page')} / {self.translator.get('view.role')}",
        )

    # Vérifie localized owner type falls back to raw value.
    def test_localized_owner_type_falls_back_to_raw_value(self):
        # Given un type connu et un type inconnu
        # When on localise les deux
        # Then le type connu est traduit et l'inconnu est conservé
        self.assertEqual(
            self.view._localized_owner_type("INDI"),
            self.translator.get("entity.INDI"),
        )
        self.assertEqual(self.view._localized_owner_type("XYZ"), "XYZ")

    # Vérifie localized owner type empty returns dash.
    def test_localized_owner_type_empty_returns_dash(self):
        # Given un type de propriétaire absent
        # When on le localise
        # Then un tiret est retourné
        self.assertEqual(self.view._localized_owner_type(""), "—")

    # Vérifie display supports tuple details and removes empty information.
    def test_display_supports_tuple_details_and_removes_empty_information(self):
        # Given une citation sans information d'en-tête mais avec des détails tuples
        citation = SimpleNamespace(
            source_pointer="",
            owner_pointer="",
            owner_type="",
            details=[("NOTE", "Note citation")],
        )
        # When on affiche la citation
        self.view.display(citation)
        # Then la section des détails est présente et celle des informations est absente
        self.assertNotIn(
            self.translator.get("view.citation_information"), self.view.sections
        )
        details = self.view.sections[self.translator.get("view.citation_details")]
        self.assertIn(
            (self.translator.get("view.notes"), "Note citation"),
            self.view._section_rows[details],
        )

    # Vérifie display supports event object details.
    def test_display_supports_event_object_details(self):
        # Given une citation dont les détails sont des objets événement
        citation = SimpleNamespace(
            source_pointer="",
            owner_pointer="",
            owner_type="",
            details=[SimpleNamespace(tag="NOTE", value="Note objet", details=[])],
        )
        # When on affiche la citation
        self.view.display(citation)
        # Then le détail est rendu
        details = self.view.sections[self.translator.get("view.citation_details")]
        self.assertIn(
            (self.translator.get("view.notes"), "Note objet"),
            self.view._section_rows[details],
        )

    # Vérifie display none clears previous content.
    def test_display_none_clears_previous_content(self):
        # Given une vue déjà remplie
        self.view.display(
            SimpleNamespace(
                source_pointer="@S1@", owner_pointer="@I1@", owner_type="INDI"
            )
        )

        # When on affiche None
        self.view.display(None)

        # Then la vue est vidée et le titre par défaut est restauré
        self.assertEqual(self.view.sections, {})
        self.assertEqual(
            self.view.title_label.cget("text"),
            self.translator.get("view.citation"),
        )

    # Vérifie que le texte TEXT avec ses continuations CONT/CONC est affiché
    # sans tiret remplaceur (regression : le texte d'une citation avec
    # continuations doit être rendu dans son intégralité).
    def test_display_text_with_continuations_is_fully_rendered(self):
        # Given une citation dont le détail TEXT comporte des continuations
        citation = SimpleNamespace(
            source_pointer="@S1@",
            owner_pointer="@I1@",
            owner_type="INDI",
            context_tag="",
            level=2,
            details=[
                {
                    "tag": "TEXT",
                    "value": "Dominique Crétel\nN°482\nLe dix-neuf juin mil neuf cent soixante-trois, six heures quarante-cinq, est né, rue Jules Lebleu, 121, Dominique Fernand, du sexe masculin, de Albert Eugène Crétel, infirmier, né à Bruay-en-Artois (Pas-de-Calais), le dix-sept octobre mil neuf cent trente-six et de Louisette Eva Maria Dupré, bobineuse, son épouse, née à Estrées-les-Crécy (Somme), le trente janvier mil neuf cent quarante-deux, domiciliés à Nieppe (Nord), rue de Ploegsteert. Dressé, le vingt juin mil neuf cent soixante-trois, dix-sept heures trente, sur la déclaration du père qui, lecture faite et invité à lire l'acte, a signé avec Nous, Marceau Flament, adjoint au Maire d'Armentières, Officier de l'Etat Civil par délégation.\n(1)\nMarié à Armentières le 03 août 1985 avec Nathalie Marie Bernadette Dewilde.\nLe 06.VIII.85\nL'agent Communal délégué\n(2)\nDivorcé de Nathalie Marie Bernadette Dewilde par jugement rendu le 29 septembre 1992 par le Tribunal de Grande Instance de Lille (Nord).\nL'agent territorial délégué\n10.01.1993\n(3)\nMarié à Frasnes-les-Anvaing (Belgique) le 1er mars 1997 avec Alexandra Annie Verpoort. Instructions n° E0-01130/97 de Monsieur le Procureur de la République de Lille (Nord) en date du 20 juin 1997.\nLe 04.07.1997\nL'agent territorial délégué",
                    "level": 1,
                }
            ],
        )

        # When on affiche la citation
        self.view.display(citation)

        # Then le détail contient le texte complet (pas de tiret remplaceur)
        details_section = self.translator.get("view.citation_details")
        self.assertIn(details_section, self.view.sections)
        rows = self.view._section_rows[self.view.sections[details_section]]
        text_rows = [row for row in rows if row[0] == self.translator.get("view.text")]
        self.assertTrue(text_rows)
        text_value = text_rows[0][1]
        self.assertIn("Dominique Crétel", text_value)
        self.assertIn("N°482", text_value)
        self.assertIn("Le dix-neuf juin mil neuf cent soixante-trois", text_value)
        self.assertIn("Marié à Armentières le 03 août 1985", text_value)
        self.assertNotIn("—", text_value)

        # And le widget tk.Text rendu contient aussi le texte intégral
        full_text = (
            "Dominique Crétel\n"
            "N°482\n"
            "Le dix-neuf juin mil neuf cent soixante-trois, six heures quarante-cinq, est né, rue Jules Lebleu, 121, Dominique Fernand, du sexe masculin, de Albert Eugène Crétel, infirmier, né à Bruay-en-Artois (Pas-de-Calais), le dix-sept octobre mil neuf cent trente-six et de Louisette Eva Maria Dupré, bobineuse, son épouse, née à Estrées-les-Crécy (Somme), le trente janvier mil neuf cent quarante-deux, domiciliés à Nieppe (Nord), rue de Ploegsteert. Dressé, le vingt juin mil neuf cent soixante-trois, dix-sept heures trente, sur la déclaration du père qui, lecture faite et invité à lire l'acte, a signé avec Nous, Marceau Flament, adjoint au Maire d'Armentières, Officier de l'Etat Civil par délégation.\n"
            "(1)\n"
            "Marié à Armentières le 03 août 1985 avec Nathalie Marie Bernadette Dewilde.\n"
            "Le 06.VIII.85\n"
            "L'agent Communal délégué\n"
            "(2)\n"
            "Divorcé de Nathalie Marie Bernadette Dewilde par jugement rendu le 29 septembre 1992 par le Tribunal de Grande Instance de Lille (Nord).\n"
            "L'agent territorial délégué\n"
            "10.01.1993\n"
            "(3)\n"
            "Marié à Frasnes-les-Anvaing (Belgique) le 1er mars 1997 avec Alexandra Annie Verpoort. Instructions n° E0-01130/97 de Monsieur le Procureur de la République de Lille (Nord) en date du 20 juin 1997.\n"
            "Le 04.07.1997\n"
            "L'agent territorial délégué"
        )
        text_widget_contents = [
            w.get("1.0", "end-1c")
            for w in self.view.value_widgets
            if isinstance(w, tk.Text)
        ]
        self.assertTrue(
            any(full_text in content for content in text_widget_contents),
            f"Aucun widget Text ne contient le texte complet. Contenus: {text_widget_contents}",
        )


if __name__ == "__main__":
    unittest.main()
