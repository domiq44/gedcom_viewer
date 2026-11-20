"""Tests du présentateur de listes d'entités : libellés, noms et clés de tri."""

import unittest
from types import SimpleNamespace

from controllers.entity_list_presenter import EntityListPresenter
from gedcom.models.citation import Citation


class FakeEntityController:
    """Doublure du contrôleur d'entités pour le présentateur."""

    def __init__(self, individuals=None, families=None, sources=None):
        """Initialise la doublure avec ses tables de correspondance."""
        self.individuals = individuals or {}
        self.families = families or {}
        self.sources = sources or {}

    def get_individual(self, pointer):
        """Retourne l'individu correspondant au pointeur."""
        return self.individuals.get(pointer)

    def get_family(self, pointer):
        """Retourne la famille correspondant au pointeur."""
        return self.families.get(pointer)

    def get_source(self, pointer):
        """Retourne la source correspondant au pointeur."""
        return self.sources.get(pointer)

    def get_repository(self, pointer):
        """Retourne le dépôt correspondant au pointeur."""
        return None

    def get_note(self, pointer):
        """Retourne la note correspondant au pointeur."""
        return None

    def get_object(self, pointer):
        """Retourne l'objet correspondant au pointeur."""
        return None

    def get_submitter(self, pointer):
        """Retourne le soumetteur correspondant au pointeur."""
        return None


class FakeTranslator:
    """Traducteur de test renvoyant les libellés français attendus."""

    LABELS = {
        "entity.unknown_type": "Type inconnu",
        "entity.family_without_members": "Famille sans membres",
        "entity.unnamed": "Entité",
        "entity.without_pointer": "(sans pointeur)",
    }

    def get(self, key, **_values):
        """Retourne le libellé de test associé à la clé."""
        return self.LABELS.get(key, key)


class TestEntityListPresenter(unittest.TestCase):
    """Vérifie l'extraction d'identifiants, les libellés et les clés de tri."""

    def setUp(self):
        # Given (Arrange) un présentateur sans dépendance
        self.presenter = EntityListPresenter(FakeEntityController(), FakeTranslator())

    # Vérifie extract numeric id reads pointer from nested entity.
    def test_extract_numeric_id_reads_pointer_from_nested_entity(self):
        # Given (Arrange) une entité sans pointeur propre mais dotée d'un pointeur imbriqué
        entity = SimpleNamespace(entity=SimpleNamespace(pointer="@I5@"))
        # When (Act) on extrait l'identifiant numérique
        numeric_id, pointer = self.presenter.extract_numeric_id(entity)
        # Then (Assert) le pointeur imbriqué est utilisé
        self.assertEqual((numeric_id, pointer), (5, "@I5@"))

    # Vérifie extract numeric id without pointer returns infinite.
    def test_extract_numeric_id_without_pointer_returns_infinite(self):
        # Given (Arrange) une entité dépourvue de pointeur
        entity = SimpleNamespace()
        # When (Act) on extrait l'identifiant numérique
        numeric_id, pointer = self.presenter.extract_numeric_id(entity)
        # Then (Assert) l'identifiant est infini et le pointeur vide
        self.assertEqual(numeric_id, float("inf"))
        self.assertEqual(pointer, "")

    # Vérifie extract numeric id without digits returns infinite.
    def test_extract_numeric_id_without_digits_returns_infinite(self):
        # Given (Arrange) un pointeur sans partie numérique
        entity = SimpleNamespace(pointer="REF")
        # When (Act) on extrait l'identifiant numérique
        numeric_id, pointer = self.presenter.extract_numeric_id(entity)
        # Then (Assert) l'identifiant est infini et le pointeur conservé
        self.assertEqual(numeric_id, float("inf"))
        self.assertEqual(pointer, "REF")

    # Vérifie clean gedcom name returns empty for non string.
    def test_clean_gedcom_name_returns_empty_for_non_string(self):
        # Given (Arrange) une valeur qui n'est pas une chaîne
        # When (Act) on nettoie le nom
        cleaned = self.presenter.clean_gedcom_name(None)
        # Then (Assert) une chaîne vide est retournée
        self.assertEqual(cleaned, "")

    # Vérifie format individual name keeps surname without given name.
    def test_format_individual_name_keeps_surname_without_given_name(self):
        # Given (Arrange) un nom sans prénom
        # When (Act) on formate le nom
        formatted = self.presenter.format_individual_name(" /Smith/")
        # Then (Assert) seul le nom de famille est conservé
        self.assertEqual(formatted, "Smith,")

    # Vérifie format individual name without surname keeps given name.
    def test_format_individual_name_without_surname_keeps_given_name(self):
        # Given (Arrange) un nom sans nom de famille
        # When (Act) on formate le nom
        formatted = self.presenter.format_individual_name("John")
        # Then (Assert) seul le prénom est conservé
        self.assertEqual(formatted, "John")

    # Vérifie format display name returns empty for none.
    def test_format_display_name_returns_empty_for_none(self):
        # Given (Arrange) aucune entité
        # When (Act) on formate le nom d'affichage
        display_name = self.presenter.format_display_name(None)
        # Then (Assert) une chaîne vide est retournée
        self.assertEqual(display_name, "")

    # Vérifie format display name note uses text.
    def test_format_display_name_note_uses_text(self):
        # Given (Arrange) une note avec un texte espacé
        entity = SimpleNamespace(text="  hello   world  ")
        # When (Act) on formate le nom d'affichage
        display_name = self.presenter.format_display_name(entity, "NOTE")
        # Then (Assert) les espaces sont normalisés
        self.assertEqual(display_name, "hello world")

    # Vérifie format display name falls back to entity type.
    def test_format_display_name_falls_back_to_entity_type(self):
        # Given (Arrange) une entité sans titre, nom ni fichier
        # When (Act) on formate le nom d'affichage
        display_name = self.presenter.format_display_name(SimpleNamespace(), "OBJE")
        # Then (Assert) le type d'entité est retourné
        self.assertEqual(display_name, "OBJE")

    # Vérifie format label returns empty for none.
    def test_format_label_returns_empty_for_none(self):
        # Given (Arrange) aucune entité
        # When (Act) on formate le libellé
        label = self.presenter.format_label(None)
        # Then (Assert) une chaîne vide est retournée
        self.assertEqual(label, "")

    # Vérifie format label reads pointer from nested entity.
    def test_format_label_reads_pointer_from_nested_entity(self):
        # Given (Arrange) une entité dont le pointeur est porté par l'entité sous-jacente
        entity = SimpleNamespace(entity=SimpleNamespace(pointer="@I7@"))
        # When (Act) on formate le libellé
        label = self.presenter.format_label(entity)
        # Then (Assert) le pointeur imbriqué est utilisé
        self.assertEqual(label, "@I7@")

    # Vérifie format label reports tag without pointer.
    def test_format_label_reports_tag_without_pointer(self):
        # Given (Arrange) une entité sans pointeur mais avec un tag
        entity = SimpleNamespace(tag="INDI")
        # When (Act) on formate le libellé
        label = self.presenter.format_label(entity)
        # Then (Assert) le tag est signalé comme sans pointeur
        self.assertEqual(label, "INDI (sans pointeur)")

    # Vérifie format label reports missing pointer without tag.
    def test_format_label_reports_missing_pointer_without_tag(self):
        # Given (Arrange) une entité sans pointeur ni tag
        entity = SimpleNamespace()
        # When (Act) on formate le libellé
        label = self.presenter.format_label(entity)
        # Then (Assert) le libellé signale l'absence de pointeur
        self.assertEqual(label, "(sans pointeur)")

    # Vérifie format label uses name when type is none.
    def test_format_label_uses_name_when_type_is_none(self):
        # Given (Arrange) une entité nommée sans type explicite
        entity = SimpleNamespace(pointer="@I1@", name="John")
        # When (Act) on formate le libellé
        label = self.presenter.format_label(entity)
        # Then (Assert) le libellé associe le pointeur et le nom
        self.assertEqual(label, "@I1@ – John")

    # Vérifie format label uses source title.
    def test_format_label_uses_source_title(self):
        # Given (Arrange) une source avec un titre
        entity = SimpleNamespace(pointer="@S1@", title="Title")
        # When (Act) on formate le libellé
        label = self.presenter.format_label(entity, "SOUR")
        # Then (Assert) le libellé associe le pointeur et le titre
        self.assertEqual(label, "@S1@ – Title")

    # Vérifie format label uses repository name.
    def test_format_label_uses_repository_name(self):
        # Given (Arrange) un dépôt avec un nom
        entity = SimpleNamespace(pointer="@R1@", name="Archives")
        # When (Act) on formate le libellé
        label = self.presenter.format_label(entity, "REPO")
        # Then (Assert) le libellé associe le pointeur et le nom
        self.assertEqual(label, "@R1@ – Archives")

    # Vérifie format label uses object file.
    def test_format_label_uses_object_file(self):
        # Given (Arrange) un objet avec un fichier
        entity = SimpleNamespace(pointer="@O1@", file="photo.jpg")
        # When (Act) on formate le libellé
        label = self.presenter.format_label(entity, "OBJE")
        # Then (Assert) le libellé associe le pointeur et le fichier
        self.assertEqual(label, "@O1@ – photo.jpg")

    # Vérifie format label citation uses display name.
    def test_format_label_citation_uses_display_name(self):
        # Given (Arrange) un présentateur résolvant une citation
        controller = FakeEntityController(
            individuals={"@I1@": SimpleNamespace(name="John /Doe/")},
            sources={"@S1@": SimpleNamespace(title="Source Title")},
        )
        presenter = EntityListPresenter(controller)
        citation = Citation(
            source_pointer="@S1@",
            owner_pointer="@I1@",
            owner_type="INDI",
            level=2,
            context_tag="BIRT",
            page="12",
        )
        # When (Act) on formate le libellé
        label = presenter.format_label(citation, "CITE")
        # Then (Assert) le libellé décrit la source, le propriétaire et la page
        self.assertEqual(label, "Source Title — Doe, John · BIRT · p. 12")

    # Vérifie sort key individual without surname uses cleaned name.
    def test_sort_key_individual_without_surname_uses_cleaned_name(self):
        # Given (Arrange) un individu sans nom de famille
        entity = SimpleNamespace(pointer="@I1@", name="John")
        # When (Act) on calcule la clé de tri
        key = self.presenter.sort_key(entity, "INDI", "name")
        # Then (Assert) le nom nettoyé est utilisé
        self.assertEqual(key, "john")

    # Vérifie sort key non individual uses display name.
    def test_sort_key_non_individual_uses_display_name(self):
        # Given (Arrange) une source avec un titre
        entity = SimpleNamespace(pointer="@S1@", title="Title")
        # When (Act) on calcule la clé de tri
        key = self.presenter.sort_key(entity, "SOUR", "name")
        # Then (Assert) le nom d'affichage est utilisé
        self.assertEqual(key, "title")

    # Vérifie sort key pointer column uses numeric id.
    def test_sort_key_pointer_column_uses_numeric_id(self):
        # Given (Arrange) un individu dont le pointeur porte un numéro
        entity = SimpleNamespace(pointer="@I2@")
        # When (Act) on calcule la clé de tri de la colonne pointeur
        key = self.presenter.sort_key(entity, "INDI", "pointer")
        # Then (Assert) la clé combine l'indice numérique et le pointeur
        self.assertEqual(key, (False, 2, "@i2@"))

    # Vérifie sort key individual with surname uses surname.
    def test_sort_key_individual_with_surname_uses_surname(self):
        # Given (Arrange) un individu avec un nom de famille
        entity = SimpleNamespace(pointer="@I1@", name="John /Doe/")
        # When (Act) on calcule la clé de tri
        key = self.presenter.sort_key(entity, "INDI", "name")
        # Then (Assert) le nom de famille est utilisé
        self.assertEqual(key, "doe")

    # Vérifie sort entities orders by numeric id.
    def test_sort_entities_orders_by_numeric_id(self):
        # Given (Arrange) deux entités dont les pointeurs sont numérotés
        entities = [
            SimpleNamespace(pointer="@I10@"),
            SimpleNamespace(pointer="@I2@"),
        ]
        # When (Act) on trie les entités
        ordered = self.presenter.sort_entities(entities)
        # Then (Assert) l'ordre suit la partie numérique
        self.assertEqual([entity.pointer for entity in ordered], ["@I2@", "@I10@"])

    # Vérifie format individual name returns empty for non string.
    def test_format_individual_name_returns_empty_for_non_string(self):
        # Given (Arrange) une valeur qui n'est pas une chaîne
        # When (Act) on formate le nom
        formatted = self.presenter.format_individual_name(None)
        # Then (Assert) une chaîne vide est retournée
        self.assertEqual(formatted, "")

    # Vérifie format display name family lists members.
    def test_format_display_name_family_lists_members(self):
        # Given (Arrange) un présentateur résolvant les membres d'une famille
        controller = FakeEntityController(
            individuals={
                "@I1@": SimpleNamespace(name="John /Doe/"),
                "@I2@": SimpleNamespace(name="Jane /Smith/"),
            }
        )
        presenter = EntityListPresenter(controller)
        entity = SimpleNamespace(husband="@I1@", wife="@I2@")
        # When (Act) on formate le nom d'affichage
        display_name = presenter.format_display_name(entity, "FAM")
        # Then (Assert) les deux membres sont listés
        self.assertEqual(display_name, "Doe, John & Smith, Jane")

    # Vérifie format display name family without members.
    def test_format_display_name_family_without_members(self):
        # Given (Arrange) une famille sans membres connus
        entity = SimpleNamespace(husband=None, wife=None)
        # When (Act) on formate le nom d'affichage
        display_name = self.presenter.format_display_name(entity, "FAM")
        # Then (Assert) un libellé par défaut est retourné
        self.assertEqual(display_name, "Famille sans membres")

    # Vérifie format label individual uses name.
    def test_format_label_individual_uses_name(self):
        # Given (Arrange) un individu avec un nom GEDCOM
        entity = SimpleNamespace(pointer="@I1@", name="John /Doe/")
        # When (Act) on formate le libellé
        label = self.presenter.format_label(entity, "INDI")
        # Then (Assert) le libellé associe le pointeur et le nom formaté
        self.assertEqual(label, "@I1@ – Doe, John")

    # Vérifie format label family uses members.
    def test_format_label_family_uses_members(self):
        # Given (Arrange) un présentateur résolvant les membres d'une famille
        controller = FakeEntityController(
            individuals={
                "@I1@": SimpleNamespace(name="John /Doe/"),
                "@I2@": SimpleNamespace(name="Jane /Smith/"),
            }
        )
        presenter = EntityListPresenter(controller)
        entity = SimpleNamespace(pointer="@F1@", husband="@I1@", wife="@I2@")
        # When (Act) on formate le libellé
        label = presenter.format_label(entity, "FAM")
        # Then (Assert) le libellé associe le pointeur et les membres
        self.assertEqual(label, "@F1@ – Doe, John & Smith, Jane")

    # Vérifie format display name citation without controller uses pointers.
    def test_format_display_name_citation_without_controller_uses_pointers(self):
        # Given (Arrange) un présentateur sans contrôleur d'entités
        presenter = EntityListPresenter(None, FakeTranslator())
        citation = Citation(
            source_pointer="@S1@",
            owner_pointer="@I1@",
            owner_type="INDI",
            level=2,
            context_tag="BIRT",
            page="12",
        )

        # When (Act) on formate le nom d'affichage
        display_name = presenter.format_display_name(citation, "CITE")

        # Then (Assert) les pointeurs servent de repli
        self.assertEqual(display_name, "@S1@ — @I1@ · BIRT · p. 12")

    # Vérifie format display name family without controller uses default.
    def test_format_display_name_family_without_controller_uses_default(self):
        # Given (Arrange) un présentateur sans contrôleur d'entités
        presenter = EntityListPresenter(None, FakeTranslator())
        entity = SimpleNamespace(husband="@I1@", wife="@I2@")

        # When (Act) on formate le nom d'affichage
        display_name = presenter.format_display_name(entity, "FAM")

        # Then (Assert) le libellé par défaut est retourné
        self.assertEqual(display_name, "Famille sans membres")


if __name__ == "__main__":
    unittest.main()
