"""Préparation commune des tests du contrôleur applicatif."""

from controllers.app_controller import AppController
from controllers.entity_controller import EntityController
from controllers.presentation_controller import PresentationController
from controllers.search_controller import SearchController
from gedcom.models.entity import GedcomEntity
from gedcom.parser import GedcomParser
from ui.i18n import Translator


class DummyEntity:
    """Doublure d'entité minimale pour les tests du contrôleur applicatif."""

    def __init__(self, pointer, tag):
        self.pointer = pointer
        self.tag = tag
        self.lines = [f"0 {pointer} {tag}\n"]

    def raw_block(self):
        return "\n".join(self.lines)

    def parsed_lines(self):
        """Retourne les lignes parsées minimales de l'entité."""
        return [(0, self.pointer, self.tag, "")]


class AppControllerTestMixin:
    """Prépare une façade chargée avec un jeu d'entités minimal."""

    def setUp(self):
        self.controller = AppController(translator=Translator("fr"))
        parser = GedcomParser()
        parser.entities = {
            "INDI": [DummyEntity("@I1@", "INDI")],
            "FAM": [DummyEntity("@F1@", "FAM")],
            "SOUR": [
                GedcomEntity(
                    "@S1@", "SOUR", 0, ["0 @S1@ SOUR\n", "1 TITL Sample source\n"]
                )
            ],
            "REPO": [
                GedcomEntity(
                    "@R1@", "REPO", 0, ["0 @R1@ REPO\n", "1 NAME Sample repo\n"]
                )
            ],
            "NOTE": [
                GedcomEntity(
                    "@N1@", "NOTE", 0, ["0 @N1@ NOTE\n", "1 NOTE Sample note\n"]
                )
            ],
            "OBJE": [
                GedcomEntity("@O1@", "OBJE", 0, ["0 @O1@ OBJE\n", "1 FILE image.jpg\n"])
            ],
            "SUBM": [
                GedcomEntity(
                    "@M1@", "SUBM", 0, ["0 @M1@ SUBM\n", "1 NAME Submitter Name\n"]
                )
            ],
        }
        parser._by_pointer = {
            "@I1@": parser.entities["INDI"][0],
            "@F1@": parser.entities["FAM"][0],
            "@S1@": parser.entities["SOUR"][0],
            "@R1@": parser.entities["REPO"][0],
            "@N1@": parser.entities["NOTE"][0],
            "@O1@": parser.entities["OBJE"][0],
            "@M1@": parser.entities["SUBM"][0],
        }
        self.controller.gedcom_service.parser = parser
        self.controller.entity_controller = EntityController(
            self.controller.gedcom_service.parser
        )
        self.controller.search_controller = SearchController(
            self.controller.gedcom_service,
            self.controller.entity_controller,
            entity_labels=self.controller.ENTITY_LABELS,
            translator=self.controller.translator,
        )
        self.controller.presentation_controller = PresentationController(
            self.controller.gedcom_service,
            self.controller.entity_controller,
        )
