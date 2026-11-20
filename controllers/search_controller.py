"""Contrôleur de recherche et de tri des entités."""

import unicodedata

from controllers.entity_controller import EntityController
from controllers.entity_list_presenter import EntityListPresenter

SEARCH_FIELDS = {
    "INDI": ("name", "pointer"),
    "SOUR": ("pointer", "title", "repository"),
    "REPO": ("pointer", "name"),
    "NOTE": ("pointer", "text"),
    "OBJE": ("pointer", "title", "file"),
    "SUBM": ("pointer", "name", "email"),
}

ENTITY_LIST_METHODS = {
    "INDI": "list_individuals",
    "FAM": "list_families",
    "SOUR": "list_sources",
    "REPO": "list_repositories",
    "NOTE": "list_notes",
    "OBJE": "list_objects",
    "SUBM": "list_submitters",
}


class SearchController:
    """Gère les types d'entités, les listes et la recherche côté application."""

    def __init__(
        self,
        gedcom_service,
        entity_controller: EntityController,
        entity_labels=None,
        translator=None,
        citation_controller=None,
    ):
        """Initialise le contrôleur avec ses dépendances."""
        self.gedcom_service = gedcom_service
        self.entity_controller = entity_controller
        self.entity_labels = entity_labels or {}
        self.translator = translator
        self.citation_controller = citation_controller
        self.entity_list_presenter = EntityListPresenter(entity_controller, translator)

    @staticmethod
    def _normalize_search_text(value):
        """Normalise un texte de recherche (casse, accents)."""
        if not isinstance(value, str):
            return ""
        if value.isascii():
            return value.casefold()

        decomposed = unicodedata.normalize("NFKD", value)
        without_accents = "".join(
            character
            for character in decomposed
            if not unicodedata.combining(character)
        )
        return without_accents.casefold()

    def is_loaded(self):
        """Indique si le contrôleur est prêt."""
        return (
            self.gedcom_service is not None
            and self.entity_controller is not None
            and self.gedcom_service.is_loaded()
        )

    def get_entity_types(self):
        """Retourne les types d'entités disponibles."""
        if not self.is_loaded():
            return []

        entity_types = []
        for entity_type in self.entity_labels:
            if entity_type == "CITE":
                if self.citation_controller and self.citation_controller.has_citations:
                    entity_types.append(entity_type)
            elif entity_type in self.gedcom_service.entities:
                entity_types.append(entity_type)
        return entity_types

    def get_entity_type_label(self, entity_type: str):
        """Retourne le libellé d'un type d'entité."""
        if self.translator is not None:
            translated = self.translator.get(f"entity.{entity_type}")
            if translated != f"entity.{entity_type}":
                return translated
        fallback = (
            self.translator.get("entity.unknown_type")
            if self.translator is not None
            else "Unknown type"
        )
        return self.entity_labels.get(entity_type, fallback)

    def get_entity_type_menu_items(self):
        """Retourne les entrées de menu par type."""
        return [
            (entity_type, self.get_entity_type_label(entity_type))
            for entity_type in self.get_entity_types()
        ]

    def get_entity_type_menu_display_items(self):
        """Retourne les entrées de menu libellées."""
        return [
            (self.get_entity_type_label(entity_type), entity_type)
            for entity_type in self.get_entity_types()
        ]

    def get_all_entity_type_menu_display_items(self):
        """Retourne toutes les entrées de menu libellées."""
        return [
            (self.get_entity_type_label(entity_type), entity_type)
            for entity_type in self.entity_labels
        ]

    def list_entities(self, entity_type: str):
        """Liste les entités d'un type donné."""
        if not self.is_loaded():
            return []
        if entity_type == "CITE":
            if self.citation_controller is None:
                return []
            return self.citation_controller.list_citations()
        method_name = ENTITY_LIST_METHODS.get(entity_type)
        if method_name is None:
            return self.gedcom_service.entities.get(entity_type, [])
        return getattr(self.entity_controller, method_name)()

    def search_entities(self, entity_type: str, query: str):
        """Recherche les entités d'un type selon la requête."""
        if not self.is_loaded():
            return []

        entities = self.list_entities(entity_type)
        normalized = self._normalize_search_text(query)
        if not normalized:
            return entities
        return [
            entity
            for entity in entities
            if self._matches_query(entity, entity_type, normalized)
        ]

    def _matches_query(self, entity, entity_type, normalized):
        """Indique si une entité correspond à la requête normalisée."""
        return any(
            normalized in self._normalize_search_text(value)
            for value in self._searchable_values(entity, entity_type)
            if value
        )

    def _searchable_values(self, entity, entity_type):
        """Retourne les valeurs recherchables d'une entité."""
        if entity_type == "FAM":
            return [entity.pointer, *self._family_member_names(entity)]
        if entity_type == "CITE":
            return self._citation_searchable_values(entity)
        return [
            getattr(entity, field, "")
            for field in SEARCH_FIELDS.get(entity_type, ("pointer",))
        ]

    def _family_member_names(self, family):
        """Retourne les noms des membres d'une famille."""
        member_pointers = [family.husband, family.wife, *family.children]
        return [
            individual.name
            for pointer in member_pointers
            if (individual := self.entity_controller.get_individual(pointer))
            is not None
        ]

    def _citation_searchable_values(self, citation):
        """Retourne les valeurs recherchables d'une citation."""
        source = self.entity_controller.get_source(citation.source_pointer)
        repository_pointer = getattr(source, "repository", "")
        return (
            citation.source_pointer,
            citation.owner_pointer,
            citation.owner_type,
            citation.context_tag,
            citation.page,
            repository_pointer,
            self.format_entity_display_name(citation, "CITE"),
        )

    def get_entity_list(self, entity_type: str, query: str = ""):
        """Retourne la liste filtrée des entités."""
        if not self.is_loaded():
            return []

        if query:
            entities = self.search_entities(entity_type, query)
        else:
            entities = self.list_entities(entity_type)

        return self.entity_list_presenter.sort_entities(entities)

    def get_entity_list_items(self, entity_type: str, query: str = ""):
        """Retourne les éléments de liste d'un type."""
        return [
            (entity, self.format_entity_label(entity, entity_type))
            for entity in self.get_entity_list(entity_type, query)
        ]

    def format_entity_display_name(self, entity, entity_type: str | None = None):
        """Formate le nom d'affichage d'une entité."""
        return self.entity_list_presenter.format_display_name(entity, entity_type)

    def get_entity_sort_key(self, entity, entity_type: str, column: str):
        """Retourne la clé de tri d'une entité."""
        return self.entity_list_presenter.sort_key(entity, entity_type, column)

    def format_entity_label(self, entity, entity_type: str | None = None):
        """Formate le libellé d'une entité."""
        return self.entity_list_presenter.format_label(entity, entity_type)
