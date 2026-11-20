"""Tests du contrôleur des citations GEDCOM."""

import threading
import unittest
from unittest.mock import patch

from controllers.citation_controller import CitationController
from gedcom.parser import GedcomParser


def _parser(lines):
    """Construit un parseur GEDCOM à partir de lignes."""
    parser = GedcomParser()
    parser.lines = lines
    parser._parse_entities()
    return parser


class TestCitationController(unittest.TestCase):
    """Vérifie l'indexation des citations SOUR."""

    # Vérifie builds citations with page.
    def test_builds_citations_with_page(self):
        # Given un individu citant une source avec une page
        parser = _parser(
            [
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "1 BIRT",
                "2 SOUR @S1@",
                "3 PAGE 12",
                "0 @S1@ SOUR",
                "1 TITRE Source",
            ]
        )

        # When on construit le contrôleur
        controller = CitationController(parser)

        # Then la citation expose son contexte et sa page
        citations = controller.list_citations()
        self.assertTrue(controller.has_citations)
        self.assertEqual(len(citations), 1)
        citation = citations[0]
        self.assertEqual(citation.source_pointer, "@S1@")
        self.assertEqual(citation.owner_pointer, "@I1@")
        self.assertEqual(citation.owner_type, "INDI")
        self.assertEqual(citation.level, 2)
        self.assertEqual(citation.context_tag, "BIRT")
        self.assertEqual(citation.page, "12")

    # Vérifie ignores non pointer and unknown sources.
    def test_ignores_non_pointer_and_unknown_sources(self):
        # Given des sources qui ne pointent pas vers un enregistrement SOUR
        parser = _parser(
            [
                "0 @I1@ INDI",
                "1 NAME John /Doe/",
                "1 BIRT",
                "2 SOUR @I1@",
                "2 SOUR not-a-pointer",
                "0 @S1@ SOUR",
            ]
        )

        # When on construit le contrôleur
        controller = CitationController(parser)

        # Then aucune citation n'est indexée
        self.assertFalse(controller.has_citations)
        self.assertEqual(controller.list_citations(), [])

    # Vérifie indexes citations from any record type.
    def test_indexes_citations_from_any_record_type(self):
        # Given une note de niveau 1 citant une source
        parser = _parser(
            [
                "0 @N1@ NOTE",
                "1 SOUR @S1@",
                "0 @S1@ SOUR",
            ]
        )

        # When on construit le contrôleur
        controller = CitationController(parser)

        # Then la citation conserve le type de son propriétaire
        citation = controller.list_citations()[0]
        self.assertEqual(citation.owner_type, "NOTE")
        self.assertEqual(citation.owner_pointer, "@N1@")
        self.assertEqual(citation.context_tag, "")

    # Vérifie duplicate pointer produces one citation.
    def test_duplicate_pointer_produces_one_citation(self):
        # Given deux enregistrements partageant le même pointeur et la même citation
        parser = _parser(
            [
                "0 @I1@ INDI",
                "1 BIRT",
                "2 SOUR @S1@",
                "0 @I1@ INDI",
                "1 BIRT",
                "2 SOUR @S1@",
                "0 @S1@ SOUR",
            ]
        )

        # When on construit le contrôleur
        controller = CitationController(parser)

        # Then une seule citation est indexée
        self.assertEqual(len(controller.list_citations()), 1)

    # Vérifie qu'une citation citant la même source deux fois dans le même
    # enregistrement n'est pas doublonnée.
    def test_duplicate_citation_within_same_record_is_deduplicated(self):
        # Given un enregistrement citant la même source à deux niveaux 2 distincts
        parser = _parser(
            [
                "0 @I1@ INDI",
                "1 BIRT",
                "2 SOUR @S1@",
                "3 PAGE 12",
                "1 DEAT",
                "2 SOUR @S1@",
                "3 PAGE 13",
                "0 @S1@ SOUR",
            ]
        )

        # When on construit le contrôleur
        controller = CitationController(parser)

        # Then deux citations distinctes (pages différentes) sont indexées
        citations = controller.list_citations()
        self.assertEqual(len(citations), 2)
        pages = sorted(c.page for c in citations)
        self.assertEqual(pages, ["12", "13"])

    # Vérifie qu'un niveau 1 non-SOUR réinitialise la citation active.
    def test_non_sour_level_one_resets_active_citation(self):
        # Given un enregistrement avec une citation suivie d'un autre niveau 1
        # puis des lignes de niveau 2 qui ne doivent pas retomber sur la citation
        parser = _parser(
            [
                "0 @I1@ INDI",
                "1 BIRT",
                "2 SOUR @S1@",
                "3 PAGE 12",
                "1 NAME John /Doe/",
                "2 GIVN John",
                "2 SURN Doe",
                "0 @S1@ SOUR",
            ]
        )

        # When on construit le contrôleur
        controller = CitationController(parser)

        # Then une seule citation est indexée (la citation BIRT, pas NAME)
        citations = controller.list_citations()
        self.assertEqual(len(citations), 1)
        citation = citations[0]
        self.assertEqual(citation.context_tag, "BIRT")
        self.assertEqual(citation.page, "12")

    # Vérifie white box citations are built lazily.
    def test_white_box_citations_are_built_lazily(self):
        # Given un contrôleur de citations
        parser = _parser(["0 @S1@ SOUR", "1 TITL Source"])
        controller = CitationController(parser)

        # When on accède aux citations
        with patch.object(
            controller, "_build_citations", wraps=controller._build_citations
        ) as build:
            self.assertIsNone(controller._citations)
            controller.list_citations()

        # Then l'index est construit une seule fois
        self.assertEqual(build.call_count, 1)

    # Vérifie malformed record does not break citation index.
    def test_malformed_record_does_not_break_citation_index(self):
        # Given un enregistrement dont les lignes ne peuvent pas être lues
        class BrokenRecord:
            pointer = "@I1@"
            tag = "INDI"

            @property
            def lines(self):
                raise RuntimeError("boom")

        parser = _parser(["0 @S1@ SOUR"])
        parser.entities["INDI"] = [BrokenRecord()]

        # When on construit le contrôleur
        controller = CitationController(parser)

        # Then l'index reste vide sans propager l'exception
        self.assertEqual(controller.list_citations(), [])

    # Vérifie citation index is built once under concurrency.
    def test_citation_index_is_built_once_under_concurrency(self):
        # Given un contrôleur et plusieurs threads qui forcent le lazy loading
        parser = _parser(
            [
                "0 @I1@ INDI",
                "1 BIRT",
                "2 SOUR @S1@",
                "0 @S1@ SOUR",
            ]
        )
        controller = CitationController(parser)
        barrier = threading.Barrier(4)
        errors = []

        def worker():
            try:
                barrier.wait()
                controller.list_citations()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(4)]

        # When on lance les threads
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Then aucune erreur ne survient et l'index est unique
        self.assertEqual(errors, [])
        self.assertEqual(len(controller.list_citations()), 1)


if __name__ == "__main__":
    unittest.main()
