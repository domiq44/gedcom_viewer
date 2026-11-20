"""Tests du contrôleur de recherche : normalisation, recherche insensible aux accents et tri."""

import os
import tempfile
import unittest
from types import SimpleNamespace

from controllers.citation_controller import CitationController
from controllers.entity_labels import get_default_entity_labels
from controllers.gedcom_service import GedcomService
from controllers.search_controller import SearchController

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
1 NAME Crétel /Marie/
1 SEX F
1 FAMS @F1@
1 SOUR @S1@
2 PAGE 42
0 @I2@ INDI
1 NAME Jean /Dupont/
1 SEX M
1 FAMS @F1@
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I1@
0 @S1@ SOUR
1 TITL Registre des naissances
1 REPO @R1@
0 @R1@ REPO
1 NAME Archives
0 TRLR
"""


class TestSearchController(unittest.TestCase):
    """Vérifie la normalisation, la recherche insensible aux accents et le tri."""

    def setUp(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".ged", delete=False
        ) as handle:
            handle.write(GEDCOM)
            self.path = handle.name
        self.service = GedcomService()
        self.service.load_file(self.path)
        self.entity_controller = self.service.create_entity_controller()
        self.citation_controller = CitationController(self.service.parser)
        self.search = SearchController(
            self.service,
            self.entity_controller,
            entity_labels=get_default_entity_labels(),
            citation_controller=self.citation_controller,
        )

    def tearDown(self):
        os.unlink(self.path)

    # Vérifie normalize removes accents.
    def test_normalize_removes_accents(self):
        # Given (Arrange) une chaîne accentuée
        value = "Crétel"
        # When (Act) on normalise
        result = SearchController._normalize_search_text(value)
        # Then (Assert) les accents sont retirés
        self.assertEqual(result, "cretel")

    # Vérifie search individuals matches accent insensitive.
    def test_search_individuals_matches_accent_insensitive(self):
        # Given (Arrange) une requête sans accent
        query = "cretel"
        # When (Act) on recherche les individus
        results = self.search.search_entities("INDI", query)
        # Then (Assert) l'individu accentué est trouvé
        self.assertEqual(len(results), 1)
        self.assertIn("Crétel", results[0].name)

    # Vérifie search individuals by pointer.
    def test_search_individuals_by_pointer(self):
        # Given (Arrange) une requête sur le pointeur
        query = "@I2@"
        # When (Act) on recherche les individus
        results = self.search.search_entities("INDI", query)
        # Then (Assert) l'individu correspondant est trouvé
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].pointer, "@I2@")

    # Vérifie search families matches member name.
    def test_search_families_matches_member_name(self):
        # Given (Arrange) une requête sur le nom d'un membre
        query = "Dupont"
        # When (Act) on recherche les familles
        results = self.search.search_entities("FAM", query)
        # Then (Assert) la famille contenant le membre est trouvée
        self.assertEqual(len(results), 1)

    # Vérifie search citations finds citation page.
    def test_search_citations_finds_citation_page(self):
        # Given (Arrange) une requête sur le numéro de page
        query = "42"
        # When (Act) on recherche les citations
        results = self.search.search_entities("CITE", query)
        # Then (Assert) la citation avec cette page est trouvée
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].page, "42")

    # Vérifie get entity list sorts pointers numerically.
    def test_get_entity_list_sorts_pointers_numerically(self):
        # Given (Arrange) une liste d'individus non triés
        # When (Act) on récupère la liste triée
        entities = self.search.get_entity_list("INDI")
        pointers = [entity.pointer for entity in entities]
        # Then (Assert) les pointeurs sont ordonnés numériquement
        self.assertEqual(pointers, ["@I1@", "@I2@"])

    # Vérifie get entity type label uses labels when no translator.
    def test_get_entity_type_label_uses_labels_when_no_translator(self):
        # Given (Arrange) un type d'entité sans traducteur
        entity_type = "INDI"
        # When (Act) on récupère le libellé
        label = self.search.get_entity_type_label(entity_type)
        # Then (Assert) le libellé par défaut est utilisé
        self.assertEqual(label, get_default_entity_labels()["INDI"])

    # Vérifie get entity types lists available types.
    def test_get_entity_types_lists_available_types(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on récupère les types disponibles
        types = self.search.get_entity_types()
        # Then (Assert) les types présents sont listés
        self.assertIn("INDI", types)
        self.assertIn("FAM", types)
        self.assertIn("CITE", types)

    # Vérifie normalize non string returns empty.
    def test_normalize_non_string_returns_empty(self):
        # Given (Arrange) une valeur qui n'est pas une chaîne
        # When (Act) on normalise
        result = SearchController._normalize_search_text(None)
        # Then (Assert) une chaîne vide est retournée
        self.assertEqual(result, "")

    # Vérifie get entity types returns empty when unloaded.
    def test_get_entity_types_returns_empty_when_unloaded(self):
        # Given (Arrange) un contrôleur sans fichier chargé
        search = SearchController(None, None)
        # When (Act) on récupère les types
        types = search.get_entity_types()
        # Then (Assert) la liste est vide
        self.assertEqual(types, [])

    # Vérifie get entity type label uses translation.
    def test_get_entity_type_label_uses_translation(self):
        # Given (Arrange) un traducteur qui traduit le type d'entité
        translator = SimpleNamespace(get=lambda key: "Individu")
        search = SearchController(
            self.service,
            self.entity_controller,
            entity_labels=get_default_entity_labels(),
            translator=translator,
        )
        # When (Act) on récupère le libellé
        label = search.get_entity_type_label("INDI")
        # Then (Assert) la traduction est utilisée
        self.assertEqual(label, "Individu")

    # Vérifie get entity type menu items pairs type and label.
    def test_get_entity_type_menu_items_pairs_type_and_label(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on récupère les entrées de menu
        items = self.search.get_entity_type_menu_items()
        # Then (Assert) chaque entrée associe un type et son libellé
        self.assertIn(("INDI", get_default_entity_labels()["INDI"]), items)

    # Vérifie get all entity type menu display items lists every type.
    def test_get_all_entity_type_menu_display_items_lists_every_type(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on récupère toutes les entrées libellées
        items = self.search.get_all_entity_type_menu_display_items()
        # Then (Assert) tous les types connus sont listés
        self.assertEqual(len(items), len(get_default_entity_labels()))

    # Vérifie list entities returns empty when unloaded.
    def test_list_entities_returns_empty_when_unloaded(self):
        # Given (Arrange) un contrôleur sans fichier chargé
        search = SearchController(None, None)
        # When (Act) on liste les individus
        entities = search.list_entities("INDI")
        # Then (Assert) la liste est vide
        self.assertEqual(entities, [])

    # Vérifie list entities returns empty for citations without controller.
    def test_list_entities_returns_empty_for_citations_without_controller(self):
        # Given (Arrange) un contrôleur sans contrôleur de citations
        search = SearchController(
            self.service,
            self.entity_controller,
            entity_labels=get_default_entity_labels(),
        )
        # When (Act) on liste les citations
        citations = search.list_entities("CITE")
        # Then (Assert) la liste est vide
        self.assertEqual(citations, [])

    # Vérifie list entities returns families.
    def test_list_entities_returns_families(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on liste les familles
        families = self.search.list_entities("FAM")
        # Then (Assert) la famille est retournée
        self.assertEqual(len(families), 1)

    # Vérifie list entities returns sources.
    def test_list_entities_returns_sources(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on liste les sources
        sources = self.search.list_entities("SOUR")
        # Then (Assert) la source est retournée
        self.assertEqual(len(sources), 1)

    # Vérifie list entities returns repositories.
    def test_list_entities_returns_repositories(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on liste les dépôts
        repositories = self.search.list_entities("REPO")
        # Then (Assert) le dépôt est retourné
        self.assertEqual(len(repositories), 1)

    # Vérifie list entities returns empty notes.
    def test_list_entities_returns_empty_notes(self):
        # Given (Arrange) un contrôleur chargé sans note
        # When (Act) on liste les notes
        notes = self.search.list_entities("NOTE")
        # Then (Assert) la liste est vide
        self.assertEqual(notes, [])

    # Vérifie list entities returns empty objects.
    def test_list_entities_returns_empty_objects(self):
        # Given (Arrange) un contrôleur chargé sans objet
        # When (Act) on liste les objets
        objects = self.search.list_entities("OBJE")
        # Then (Assert) la liste est vide
        self.assertEqual(objects, [])

    # Vérifie list entities returns submitters.
    def test_list_entities_returns_submitters(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on liste les soumetteurs
        submitters = self.search.list_entities("SUBM")
        # Then (Assert) le soumetteur est retourné
        self.assertEqual(len(submitters), 1)

    # Vérifie list entities falls back to service index.
    def test_list_entities_falls_back_to_service_index(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on liste un type sans traitement dédié
        entities = self.search.list_entities("HEAD")
        # Then (Assert) l'index du service est utilisé
        self.assertEqual(len(entities), 1)

    # Vérifie search entities returns empty when unloaded.
    def test_search_entities_returns_empty_when_unloaded(self):
        # Given (Arrange) un contrôleur sans fichier chargé
        search = SearchController(None, None)
        # When (Act) on recherche des individus
        results = search.search_entities("INDI", "a")
        # Then (Assert) la liste est vide
        self.assertEqual(results, [])

    # Vérifie search entities returns all when query empty.
    def test_search_entities_returns_all_when_query_empty(self):
        # Given (Arrange) un contrôleur chargé et une requête vide
        # When (Act) on recherche un type sans traitement dédié
        results = self.search.search_entities("HEAD", "")
        # Then (Assert) toutes les entités du type sont retournées
        self.assertEqual(len(results), 1)

    # Vérifie search entities falls back to pointer search.
    def test_search_entities_falls_back_to_pointer_search(self):
        # Given (Arrange) un service exposant un type inconnu
        service = SimpleNamespace(
            entities={"ABCD": [SimpleNamespace(pointer="ABCD")]},
            is_loaded=lambda: True,
        )
        search = SearchController(service, SimpleNamespace(), entity_labels={})
        # When (Act) on recherche ce type par son pointeur
        results = search.search_entities("ABCD", "abcd")
        # Then (Assert) l'entité correspondante est retournée
        self.assertEqual(len(results), 1)

    # Vérifie search individuals returns all when query empty.
    def test_search_individuals_returns_all_when_query_empty(self):
        # Given (Arrange) un contrôleur chargé et une requête vide
        # When (Act) on recherche les individus
        results = self.search.search_entities("INDI", "")
        # Then (Assert) tous les individus sont retournés
        self.assertEqual(len(results), 2)

    # Vérifie search sources returns all when query empty.
    def test_search_sources_returns_all_when_query_empty(self):
        # Given (Arrange) un contrôleur chargé et une requête vide
        # When (Act) on recherche les sources
        results = self.search.search_entities("SOUR", "")
        # Then (Assert) toutes les sources sont retournées
        self.assertEqual(len(results), 1)

    # Vérifie search repositories returns all when query empty.
    def test_search_repositories_returns_all_when_query_empty(self):
        # Given (Arrange) un contrôleur chargé et une requête vide
        # When (Act) on recherche les dépôts
        results = self.search.search_entities("REPO", "")
        # Then (Assert) tous les dépôts sont retournés
        self.assertEqual(len(results), 1)

    # Vérifie search notes returns all when query empty.
    def test_search_notes_returns_all_when_query_empty(self):
        # Given (Arrange) un contrôleur chargé et une requête vide
        # When (Act) on recherche les notes
        results = self.search.search_entities("NOTE", "")
        # Then (Assert) toutes les notes sont retournées
        self.assertEqual(results, [])

    # Vérifie search objects returns all when query empty.
    def test_search_objects_returns_all_when_query_empty(self):
        # Given (Arrange) un contrôleur chargé et une requête vide
        # When (Act) on recherche les objets
        results = self.search.search_entities("OBJE", "")
        # Then (Assert) tous les objets sont retournés
        self.assertEqual(results, [])

    # Vérifie search submitters returns all when query empty.
    def test_search_submitters_returns_all_when_query_empty(self):
        # Given (Arrange) un contrôleur chargé et une requête vide
        # When (Act) on recherche les soumetteurs
        results = self.search.search_entities("SUBM", "")
        # Then (Assert) tous les soumetteurs sont retournés
        self.assertEqual(len(results), 1)

    # Vérifie search citations returns all when query empty.
    def test_search_citations_returns_all_when_query_empty(self):
        # Given (Arrange) un contrôleur chargé et une requête vide
        # When (Act) on recherche les citations
        results = self.search.search_entities("CITE", "")
        # Then (Assert) toutes les citations sont retournées
        self.assertEqual(len(results), 1)

    # Vérifie get entity list returns empty when unloaded.
    def test_get_entity_list_returns_empty_when_unloaded(self):
        # Given (Arrange) un contrôleur sans fichier chargé
        search = SearchController(None, None)
        # When (Act) on récupère la liste des individus
        entities = search.get_entity_list("INDI")
        # Then (Assert) la liste est vide
        self.assertEqual(entities, [])

    # Vérifie get entity type menu display items pairs label and type.
    def test_get_entity_type_menu_display_items_pairs_label_and_type(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on récupère les entrées libellées
        items = self.search.get_entity_type_menu_display_items()
        # Then (Assert) chaque entrée associe un libellé et un type
        self.assertIn((get_default_entity_labels()["INDI"], "INDI"), items)

    # Vérifie search entities dispatches to citation search.
    def test_search_entities_dispatches_to_citation_search(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on recherche les citations
        results = self.search.search_entities("CITE", "42")
        # Then (Assert) la recherche de citations est appelée
        self.assertEqual(len(results), 1)

    # Vérifie search entities dispatches to individual search.
    def test_search_entities_dispatches_to_individual_search(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on recherche les individus
        results = self.search.search_entities("INDI", "Dupont")
        # Then (Assert) la recherche d'individus est appelée
        self.assertEqual(len(results), 1)

    # Vérifie search entities dispatches to family search.
    def test_search_entities_dispatches_to_family_search(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on recherche les familles
        results = self.search.search_entities("FAM", "Dupont")
        # Then (Assert) la recherche de familles est appelée
        self.assertEqual(len(results), 1)

    # Vérifie search entities dispatches to source search.
    def test_search_entities_dispatches_to_source_search(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on recherche les sources
        results = self.search.search_entities("SOUR", "registre")
        # Then (Assert) la recherche de sources est appelée
        self.assertEqual(len(results), 1)

    # Vérifie search entities dispatches to repository search.
    def test_search_entities_dispatches_to_repository_search(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on recherche les dépôts
        results = self.search.search_entities("REPO", "archives")
        # Then (Assert) la recherche de dépôts est appelée
        self.assertEqual(len(results), 1)

    # Vérifie search entities dispatches to note search.
    def test_search_entities_dispatches_to_note_search(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on recherche les notes
        results = self.search.search_entities("NOTE", "anything")
        # Then (Assert) la recherche de notes est appelée
        self.assertEqual(results, [])

    # Vérifie search entities dispatches to object search.
    def test_search_entities_dispatches_to_object_search(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on recherche les objets
        results = self.search.search_entities("OBJE", "anything")
        # Then (Assert) la recherche d'objets est appelée
        self.assertEqual(results, [])

    # Vérifie search entities dispatches to submitter search.
    def test_search_entities_dispatches_to_submitter_search(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on recherche les soumetteurs
        results = self.search.search_entities("SUBM", "doe")
        # Then (Assert) la recherche de soumetteurs est appelée
        self.assertEqual(len(results), 1)

    # Vérifie search families returns all when query empty.
    def test_search_families_returns_all_when_query_empty(self):
        # Given (Arrange) un contrôleur chargé et une requête vide
        # When (Act) on recherche les familles
        results = self.search.search_entities("FAM", "")
        # Then (Assert) toutes les familles sont retournées
        self.assertEqual(len(results), 1)

    # Vérifie search sources matches query.
    def test_search_sources_matches_query(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on recherche les sources par titre
        results = self.search.search_entities("SOUR", "registre")
        # Then (Assert) la source correspondante est retournée
        self.assertEqual(len(results), 1)

    # Vérifie search repositories matches query.
    def test_search_repositories_matches_query(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on recherche les dépôts par nom
        results = self.search.search_entities("REPO", "archives")
        # Then (Assert) le dépôt correspondant est retourné
        self.assertEqual(len(results), 1)

    # Vérifie search notes matches query.
    def test_search_notes_matches_query(self):
        # Given (Arrange) un contrôleur chargé sans note
        # When (Act) on recherche les notes
        results = self.search.search_entities("NOTE", "anything")
        # Then (Assert) aucune note n'est retournée
        self.assertEqual(results, [])

    # Vérifie search objects matches query.
    def test_search_objects_matches_query(self):
        # Given (Arrange) un contrôleur chargé sans objet
        # When (Act) on recherche les objets
        results = self.search.search_entities("OBJE", "anything")
        # Then (Assert) aucun objet n'est retourné
        self.assertEqual(results, [])

    # Vérifie search submitters matches query.
    def test_search_submitters_matches_query(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on recherche les soumetteurs par nom
        results = self.search.search_entities("SUBM", "doe")
        # Then (Assert) le soumetteur correspondant est retourné
        self.assertEqual(len(results), 1)

    # Vérifie get entity list uses search when query given.
    def test_get_entity_list_uses_search_when_query_given(self):
        # Given (Arrange) un contrôleur chargé et une requête
        # When (Act) on récupère la liste filtrée
        entities = self.search.get_entity_list("INDI", "Dupont")
        # Then (Assert) la recherche restreint la liste
        self.assertEqual([entity.pointer for entity in entities], ["@I2@"])

    # Vérifie get entity list items pairs entity and label.
    def test_get_entity_list_items_pairs_entity_and_label(self):
        # Given (Arrange) un contrôleur chargé
        # When (Act) on récupère les éléments de liste
        items = self.search.get_entity_list_items("INDI")
        # Then (Assert) chaque élément associe une entité et un libellé
        self.assertEqual(len(items), 2)

    # Vérifie get entity sort key delegates to presenter.
    def test_get_entity_sort_key_delegates_to_presenter(self):
        # Given (Arrange) un individu déjà chargé
        individual = self.entity_controller.list_individuals()[0]
        # When (Act) on calcule la clé de tri
        key = self.search.get_entity_sort_key(individual, "INDI", "name")
        # Then (Assert) la clé du présentateur est retournée
        self.assertEqual(
            key, self.search.entity_list_presenter.sort_key(individual, "INDI", "name")
        )

    # Vérifie format entity label delegates to presenter.
    def test_format_entity_label_delegates_to_presenter(self):
        # Given (Arrange) un individu déjà chargé
        individual = self.entity_controller.list_individuals()[0]
        # When (Act) on formate le libellé
        label = self.search.format_entity_label(individual, "INDI")
        # Then (Assert) le libellé du présentateur est retourné
        self.assertEqual(
            label, self.search.entity_list_presenter.format_label(individual, "INDI")
        )


if __name__ == "__main__":
    unittest.main()
