"""Tests du contrôleur de présentation : résolution de pointeurs et contextes de vue."""

import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from controllers.gedcom_service import GedcomService
from controllers.presentation_controller import PresentationController

GEDCOM = """0 HEAD
1 SOUR TEST
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
1 SUBM @U1@
0 @U1@ SUBM
1 NAME John /Doe/
0 @I1@ INDI
1 NAME John /Doe/
1 SEX M
1 NOTE Une note
0 @F1@ FAM
1 HUSB @I1@
0 @N1@ NOTE
1 CONT Texte de la note
0 @S1@ SOUR
1 TITL Source
0 @R1@ REPO
1 NAME Archive
0 @O1@ OBJE
1 FILE image.jpg
0 TRLR
"""


class TestPresentationController(unittest.TestCase):
    """Vérifie la résolution de pointeurs et les contextes de vue restitués."""

    def setUp(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".ged", delete=False
        ) as handle:
            handle.write(GEDCOM)
            self.path = handle.name
        self.service = GedcomService()
        self.service.load_file(self.path)
        self.entity_controller = self.service.create_entity_controller()
        self.presentation = PresentationController(self.service, self.entity_controller)

    def tearDown(self):
        os.unlink(self.path)

    # Vérifie format details merges continuations.
    def test_format_details_merges_continuations(self):
        # Given une liste de détails contenant une continuation
        details = [
            {"tag": "NOTE", "value": "Texte"},
            {"tag": "CONT", "value": " suite"},
        ]
        # When on formate les détails
        formatted = self.presentation.format_details(details)
        # Then la continuation est concaténée avec un saut de ligne
        self.assertEqual(formatted, [{"tag": "NOTE", "value": "Texte\n suite"}])

    # Vérifie is loaded true after load.
    def test_is_loaded_true_after_load(self):
        # Given (Arrange) un contrôleur de présentation chargé
        # When (Act) on interroge l'état
        loaded = self.presentation.is_loaded()
        # Then (Assert) il est marqué comme chargé
        self.assertTrue(loaded)

    # Vérifie get entity returns raw entity.
    def test_get_entity_returns_raw_entity(self):
        # Given un pointeur d'individu
        pointer = "@I1@"
        # When on récupère l'entité brute
        entity = self.presentation.get_entity(pointer)
        # Then l'entité brute est retournée
        self.assertIsNotNone(entity)
        self.assertEqual(entity.pointer, pointer)

    # Vérifie resolve pointer returns none for empty pointer.
    def test_resolve_pointer_returns_none_for_empty_pointer(self):
        # Given un pointeur vide
        # When on résout le pointeur
        result = self.presentation.resolve_pointer("")
        # Then aucune entité n'est retournée
        self.assertIsNone(result)

    # Vérifie resolve pointer returns none for unknown pointer.
    def test_resolve_pointer_returns_none_for_unknown_pointer(self):
        # Given un pointeur inconnu
        # When on résout le pointeur
        result = self.presentation.resolve_pointer("@Z9@")
        # Then aucune entité n'est retournée
        self.assertIsNone(result)

    # Vérifie resolve pointer returns raw for unknown tag.
    def test_resolve_pointer_returns_raw_for_unknown_tag(self):
        # Given une entité dont le tag n'a pas de résolveur dédié
        raw = SimpleNamespace(tag="CUST", pointer="@X1@")
        # When on résout le pointeur
        with patch.object(self.service, "get_entity", return_value=raw):
            result = self.presentation.resolve_pointer("@X1@")
        # Then l'entité brute est retournée
        self.assertIs(result, raw)

    # Vérifie get raw block supports raw block method.
    def test_get_raw_block_supports_raw_block_method(self):
        # Given une entité exposant une méthode raw_block
        entity = SimpleNamespace(raw_block=lambda: "block")
        # When on demande le bloc brut
        block = self.presentation.get_raw_block(entity)
        # Then la valeur de l'appel est retournée
        self.assertEqual(block, "block")

    # Vérifie get raw block supports missing inner entity.
    def test_get_raw_block_supports_missing_inner_entity(self):
        # Given une entité dont l'attribut entity est absent
        entity = SimpleNamespace(entity=None)
        # When on demande le bloc brut
        block = self.presentation.get_raw_block(entity)
        # Then une chaîne vide est retournée
        self.assertEqual(block, "")

    # Vérifie get raw block handles raw block error.
    def test_get_raw_block_handles_raw_block_error(self):
        # Given une entité dont la méthode raw_block échoue
        class BrokenEntity:
            def raw_block(self):
                raise RuntimeError("boom")

        # When on demande le bloc brut
        with self.assertLogs("controllers.view_context", level="ERROR"):
            block = self.presentation.get_raw_block(BrokenEntity())

        # Then une chaîne vide est retournée
        self.assertEqual(block, "")

    # Vérifie get entity view context returns raw for none.
    def test_get_entity_view_context_returns_raw_for_none(self):
        # Given une entité absente
        # When on demande le contexte
        context = self.presentation.get_entity_view_context(None)
        # Then le contexte brut est renvoyé
        self.assertEqual(context, {"type": "raw", "entity": None, "raw_entity": None})

    # Vérifie get entity display info returns raw for none.
    def test_get_entity_display_info_returns_raw_for_none(self):
        # Given une entité absente
        # When on demande les infos d'affichage
        info = self.presentation.get_entity_display_info(None)
        # Then le contexte brut est renvoyé
        self.assertEqual(info["type"], "raw")

    # Vérifie get entity view context for family.
    def test_get_entity_view_context_for_family(self):
        # Given une famille
        family = self.entity_controller.get_family("@F1@")
        # When on demande le contexte d'affichage
        context = self.presentation.get_entity_view_context(family)
        # Then le type de contexte est "family"
        self.assertEqual(context["type"], "family")

    # Vérifie get entity view context for citation.
    def test_get_entity_view_context_for_citation(self):
        # Given une citation virtuelle avec un pointeur source
        citation = SimpleNamespace(
            source_pointer="@S1@",
            raw_block="2 SOUR @S1@\n3 PAGE 12\n",
        )

        # When on demande le contexte d'affichage
        context = self.presentation.get_entity_view_context(citation)

        # Then le type de contexte est "citation" et le bloc brut est conservé
        self.assertEqual(context["type"], "citation")
        self.assertIs(context["entity"], citation)
        self.assertIs(context["raw_entity"], citation)

    # Vérifie get entity display info for citation includes raw block.
    def test_get_entity_display_info_for_citation_includes_raw_block(self):
        # Given une citation virtuelle avec un bloc brut
        citation = SimpleNamespace(
            source_pointer="@S1@",
            raw_block="2 SOUR @S1@\n3 PAGE 12\n",
        )

        # When on demande les infos d'affichage
        info = self.presentation.get_entity_display_info(citation)

        # Then le contexte est une citation avec son bloc GEDCOM brut
        self.assertEqual(info["type"], "citation")
        self.assertEqual(info["raw_block"], citation.raw_block)

    # Vérifie resolve pointer returns source for citation source.
    def test_resolve_pointer_returns_source_for_citation_source(self):
        # Given un pointeur de source cité par une citation
        pointer = "@S1@"

        # When on résout le pointeur
        result = self.presentation.resolve_pointer(pointer)

        # Then l'enregistrement SOUR sous-jacent est retourné
        self.assertIsNotNone(result)
        self.assertEqual(result.pointer, pointer)

    # Vérifie resolve pointer returns individual.
    def test_resolve_pointer_returns_individual(self):
        # Given (Arrange) un pointeur d'individu
        pointer = "@I1@"
        # When (Act) on résout le pointeur
        entity = self.presentation.resolve_pointer(pointer)
        # Then (Assert) l'individu est retourné
        self.assertIsNotNone(entity)
        self.assertEqual(entity.pointer, pointer)

    # Vérifie get entity view context for individual.
    def test_get_entity_view_context_for_individual(self):
        # Given (Arrange) un individu
        individual = self.entity_controller.get_individual("@I1@")
        # When (Act) on demande le contexte d'affichage
        context = self.presentation.get_entity_view_context(individual)
        # Then (Assert) le type de contexte est "individual"
        self.assertEqual(context["type"], "individual")

    # Vérifie get entity display info includes raw block.
    def test_get_entity_display_info_includes_raw_block(self):
        # Given (Arrange) un individu
        individual = self.entity_controller.get_individual("@I1@")
        # When (Act) on demande les infos d'affichage
        info = self.presentation.get_entity_display_info(individual)
        # Then (Assert) le bloc GEDCOM brut est présent
        self.assertIn("NAME John /Doe/", info["raw_block"])

    # Vérifie get raw block for note.
    def test_get_raw_block_for_note(self):
        # Given (Arrange) une note
        note = self.entity_controller.get_note("@N1@")
        # When (Act) on demande le bloc brut
        block = self.presentation.get_raw_block(note)
        # Then (Assert) le bloc contient la note
        self.assertIn("Texte de la note", block)

    # Vérifie get entity view context returns raw when unloaded.
    def test_get_entity_view_context_returns_raw_when_unloaded(self):
        # Given (Arrange) un service non chargé
        empty_service = GedcomService()
        controller = PresentationController(empty_service, None)
        # When (Act) on demande le contexte
        context = controller.get_entity_view_context(object())
        # Then (Assert) le type brut est renvoyé
        self.assertEqual(context["type"], "raw")

    # Vérifie resolve pointer returns none when unloaded.
    def test_resolve_pointer_returns_none_when_unloaded(self):
        # Given (Arrange) un contrôleur non chargé
        controller = PresentationController(GedcomService(), None)
        # When (Act) on résout un pointeur
        result = controller.resolve_pointer("@I1@")
        # Then (Assert) aucune entité n'est retournée
        self.assertIsNone(result)

    # Vérifie get source returns source.
    def test_get_source_returns_source(self):
        # Given (Arrange) un pointeur de source existant
        pointer = "@S1@"
        # When (Act) on récupère la source
        source = self.presentation.get_source(pointer)
        # Then (Assert) la source est retournée
        self.assertIsNotNone(source)
        self.assertEqual(source.pointer, pointer)

    # Vérifie get repository returns repository.
    def test_get_repository_returns_repository(self):
        # Given (Arrange) un pointeur de dépôt existant
        pointer = "@R1@"
        # When (Act) on récupère le dépôt
        repository = self.presentation.get_repository(pointer)
        # Then (Assert) le dépôt est retourné
        self.assertIsNotNone(repository)
        self.assertEqual(repository.pointer, pointer)

    # Vérifie get object returns object.
    def test_get_object_returns_object(self):
        # Given (Arrange) un pointeur d'objet existant
        pointer = "@O1@"
        # When (Act) on récupère l'objet
        obj = self.presentation.get_object(pointer)
        # Then (Assert) l'objet est retourné
        self.assertIsNotNone(obj)

    # Vérifie get individual returns none when unloaded.
    def test_get_individual_returns_none_when_unloaded(self):
        # Given (Arrange) un contrôleur non chargé
        controller = PresentationController(GedcomService(), None)
        # When (Act) on récupère un individu
        result = controller.get_individual("@I1@")
        # Then (Assert) aucune entité n'est retournée
        self.assertIsNone(result)

    # Vérifie extract head returns empty when unloaded.
    def test_extract_head_returns_empty_when_unloaded(self):
        # Given (Arrange) un contrôleur non chargé
        controller = PresentationController(GedcomService(), None)
        # When (Act) on extrait l'en-tête
        result = controller.extract_head()
        # Then (Assert) une chaîne vide est renvoyée
        self.assertEqual(result, "")

    # Vérifie extract trailer returns empty when unloaded.
    def test_extract_trailer_returns_empty_when_unloaded(self):
        # Given (Arrange) un contrôleur non chargé
        controller = PresentationController(GedcomService(), None)
        # When (Act) on extrait le trailer
        result = controller.extract_trailer()
        # Then (Assert) une chaîne vide est renvoyée
        self.assertEqual(result, "")

    # Vérifie get raw block returns empty for none entity.
    def test_get_raw_block_returns_empty_for_none_entity(self):
        # Given (Arrange) un contrôleur chargé et une entité absente
        # When (Act) on demande le bloc brut
        result = self.presentation.get_raw_block(None)
        # Then (Assert) une chaîne vide est renvoyée
        self.assertEqual(result, "")

    # Vérifie get entity view context raw entity returns raw.
    def test_get_entity_view_context_raw_entity_returns_raw(self):
        # Given (Arrange) une entité brute sans attribut .entity (hors FAM)
        raw = self.service.get_entity("@S1@")
        # When (Act) on demande le contexte d'affichage
        context = self.presentation.get_entity_view_context(raw)
        # Then (Assert) le type brut est renvoyé
        self.assertEqual(context["type"], "raw")

    # Vérifie get entity view context unknown raw tag.
    def test_get_entity_view_context_unknown_raw_tag(self):
        # Given un modèle dont l'entité brute a un tag inconnu
        entity = SimpleNamespace(entity=SimpleNamespace(tag="CUST"))
        # When on demande le contexte d'affichage
        context = self.presentation.get_entity_view_context(entity)
        # Then le contexte brut est renvoyé
        self.assertEqual(context["type"], "raw")

    # Vérifie get entity view context family from raw entity.
    def test_get_entity_view_context_family_from_raw_entity(self):
        # Given (Arrange) une entité brute FAM (sans attribut .entity)
        raw = self.service.get_entity("@F1@")
        # When (Act) on demande le contexte d'affichage
        context = self.presentation.get_entity_view_context(raw)
        # Then (Assert) la famille est résolue
        self.assertEqual(context["type"], "family")


if __name__ == "__main__":
    unittest.main()
