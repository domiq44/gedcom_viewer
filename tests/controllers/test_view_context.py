"""Tests du constructeur de contexte d'affichage."""

import tkinter as tk
import unittest
from types import SimpleNamespace

from controllers.view_context import ViewContextBuilder


class FakeEntity:
    """Entité factice avec gedcom_lines et raw_block."""

    def __init__(self, pointer, tag, gedcom_lines):
        self.pointer = pointer
        self.tag = tag
        self._gedcom_lines = gedcom_lines

    def raw_block(self):
        return "".join(self._gedcom_lines)


class FakeGedcomService:
    """Service GEDCOM factice."""

    def __init__(self, entities):
        self._entities = entities

    def is_loaded(self):
        return True

    def get_entity(self, pointer):
        return self._entities.get(pointer)


class FakeEntityController:
    """Contrôleur d'entités factice."""

    def __init__(self, entities):
        self._entities = entities

    def get_individual(self, pointer):
        return self._entities.get(pointer)

    def get_family(self, pointer):
        return None

    def get_source(self, pointer):
        return None

    def get_repository(self, pointer):
        return None

    def get_note(self, pointer):
        return None

    def get_object(self, pointer):
        return None

    def get_submitter(self, pointer):
        return None


class TestViewContextBuilder(unittest.TestCase):
    """Vérifie la construction du contexte d'affichage pour les citations."""

    def setUp(self):
        """Crée un constructeur de contexte avec des entités de test."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.translator = None

        self.citation_lines = [
            "2 SOUR @S3@\n",
            "3 PAGE Naissance Crétel, Dominique Fernand\n",
            "3 EVEN BIRT\n",
            "4 ROLE CHIL\n",
            "3 DATA\n",
            "4 DATE 1963\n",
            "4 TEXT Dominique Crétel\n",
            "5 CONT N°482\n",
            "5 CONT Le dix-neuf juin mil neuf cent soixante-trois\n",
            "5 CONC est né à Armentières\n",
            "3 QUAY 3\n",
        ]

        self.citation = SimpleNamespace(
            source_pointer="@S3@",
            owner_pointer="@I1@",
            owner_type="INDI",
            level=2,
            context_tag="",
            page="",
            gedcom_lines=self.citation_lines,
        )
        self.citation.raw_block = lambda: "".join(self.citation_lines)
        self.citation.details = [
            {"tag": "PAGE", "value": "Naissance Crétel, Dominique Fernand", "level": 1},
            {"tag": "EVEN/BIRT", "value": "", "level": 1},
            {"tag": "EVEN/BIRT/ROLE", "value": "CHIL", "level": 2},
            {"tag": "DATA", "value": "", "level": 1},
            {"tag": "DATA/DATE", "value": "1963", "level": 2},
            {
                "tag": "DATA/TEXT",
                "value": (
                    "Dominique Crétel\n"
                    "N°482\n"
                    "Le dix-neuf juin mil neuf cent soixante-trois\n"
                    "est né à Armentières"
                ),
                "level": 2,
            },
            {"tag": "DATA/QUAY", "value": "3", "level": 2},
        ]
        self.entities = {"@I1@": self.citation}

    def tearDown(self):
        self.root.destroy()

    # Vérifie get_entity_display_info retourne le raw_block complet d'une citation.
    def test_get_entity_display_info_citation_has_complete_raw_block(self):
        # Given un contexte avec une citation contenant des continuations CONT/CONC
        service = FakeGedcomService(self.entities)
        controller = FakeEntityController(self.entities)
        builder = ViewContextBuilder(service, controller, self.translator)

        # When on demande les infos d'affichage de la citation
        info = builder.get_entity_display_info(self.citation)

        # Then le raw_block contient toutes les lignes GEDCOM brutes
        self.assertEqual(info["type"], "citation")
        self.assertEqual(info["entity"], self.citation)
        self.assertIn("2 SOUR @S3@", info["raw_block"])
        self.assertIn("4 TEXT Dominique Crétel", info["raw_block"])
        self.assertIn("5 CONT N°482", info["raw_block"])
        self.assertIn("5 CONC est né à Armentières", info["raw_block"])

    # Vérifie get_entity_display_info retourne le type citation pour une entité CITE.
    def test_get_entity_view_context_citation_type(self):
        # Given une citation
        service = FakeGedcomService(self.entities)
        controller = FakeEntityController(self.entities)
        builder = ViewContextBuilder(service, controller, self.translator)

        # When on demande le contexte de vue
        context = builder.get_entity_view_context(self.citation)

        # Then le type est citation
        self.assertEqual(context["type"], "citation")


if __name__ == "__main__":
    unittest.main()
