"""Façade principale exposant les opérations de l'application."""

from types import MappingProxyType
from typing import Any

from controllers.citation_controller import CitationController
from controllers.detail_formatter import merge_text_continuations
from controllers.entity_labels import get_default_entity_labels
from controllers.entity_list_presenter import EntityListPresenter
from controllers.gedcom_service import GedcomService
from controllers.presentation_controller import PresentationController
from controllers.search_controller import SearchController
from gedcom.errors import GedcomLoadCancelled


class AppController:
    """Façade principale exposant les opérations de l'application."""

    ENTITY_LABELS = MappingProxyType(get_default_entity_labels())

    def __init__(self, gedcom_service=None, translator=None):
        """Initialise la façade et ses contrôleurs (non chargés)."""
        self.gedcom_service = gedcom_service or GedcomService()
        self.translator = translator
        self.entity_controller: Any = None
        self.citation_controller: Any = None
        self.search_controller: Any = None
        self.presentation_controller: Any = None

    def load_file(self, filename: str, strict=False, cancel_event=None):
        """Charge un fichier GEDCOM et initialise les contrôleurs."""
        self.gedcom_service.load_file(
            filename, strict=strict, cancel_event=cancel_event
        )
        if cancel_event is not None and cancel_event.is_set():
            self.reset()
            raise GedcomLoadCancelled("Chargement GEDCOM annulé")
        try:
            self._initialize_controllers()
        except Exception:
            self.reset()
            raise

    def reset(self):
        """Décharge le fichier et remet les contrôleurs à zéro."""
        if hasattr(self.gedcom_service, "reset"):
            self.gedcom_service.reset()
        self.entity_controller = None
        self.citation_controller = None
        self.search_controller = None
        self.presentation_controller = None

    def _initialize_controllers(self):
        """Crée les contrôleurs spécialisés après chargement."""
        self.entity_controller = self.gedcom_service.create_entity_controller()
        self.citation_controller = CitationController(self.gedcom_service.parser)
        self.search_controller = SearchController(
            self.gedcom_service,
            self.entity_controller,
            entity_labels=self.ENTITY_LABELS,
            translator=self.translator,
            citation_controller=self.citation_controller,
        )
        self.presentation_controller = PresentationController(
            self.gedcom_service,
            self.entity_controller,
            translator=self.translator,
        )

    def _entity_list_presenter(self):
        """Retourne le présentateur de liste, même sans chargement."""
        if self.search_controller is not None:
            return self.search_controller.entity_list_presenter
        return EntityListPresenter(None, self.translator)

    def is_loaded(self):
        """Indique si un fichier est chargé et les contrôleurs prêts."""
        return (
            self.gedcom_service.is_loaded()
            and self.entity_controller is not None
            and self.search_controller is not None
            and self.presentation_controller is not None
        )

    def get_entity_types(self):
        """Retourne les types d'entités disponibles."""
        if not self.is_loaded():
            return []
        return self.search_controller.get_entity_types()

    def get_entity_type_label(self, entity_type: str):
        """Retourne le libellé d'un type d'entité."""
        if self.search_controller is None:
            if self.translator is not None:
                translated = self.translator.get(f"entity.{entity_type}")
                if translated != f"entity.{entity_type}":
                    return translated
            return self.ENTITY_LABELS.get(entity_type, entity_type)
        return self.search_controller.get_entity_type_label(entity_type)

    def get_entity_type_menu_items(self):
        """Retourne les entrées de menu par type."""
        if self.search_controller is None:
            return []
        return self.search_controller.get_entity_type_menu_items()

    def get_entity_type_menu_display_items(self):
        """Retourne les entrées de menu libellées par type."""
        if self.search_controller is None:
            return []
        return self.search_controller.get_entity_type_menu_display_items()

    def get_all_entity_type_menu_display_items(self):
        """Retourne toutes les entrées de menu, même sans chargement."""
        if self.search_controller is None:
            return [
                (
                    (
                        self.translator.get(f"entity.{entity_type}")
                        if self.translator is not None
                        else label
                    ),
                    entity_type,
                )
                for entity_type, label in self.ENTITY_LABELS.items()
            ]
        return self.search_controller.get_all_entity_type_menu_display_items()

    def list_entities(self, entity_type: str):
        """Liste les entités d'un type donné."""
        if self.search_controller is None:
            return []
        return self.search_controller.list_entities(entity_type)

    def search_entities(self, entity_type: str, query: str):
        """Recherche les entités d'un type correspondant à la requête."""
        if self.search_controller is None:
            return []
        return self.search_controller.search_entities(entity_type, query)

    def get_entity_list(self, entity_type: str, query: str = ""):
        """Retourne la liste filtrée des entités d'un type."""
        if self.search_controller is None:
            return []
        return self.search_controller.get_entity_list(entity_type, query)

    def get_entity_list_items(self, entity_type: str, query: str = ""):
        """Retourne les éléments de liste (libellé, pointeur) d'un type."""
        if self.search_controller is None:
            return []
        return self.search_controller.get_entity_list_items(entity_type, query)

    def get_entity_display_info(self, entity):
        """Retourne le contexte d'affichage d'une entité."""
        if self.presentation_controller is None:
            return PresentationController.default_display_info(entity)
        return self.presentation_controller.get_entity_display_info(entity)

    def get_entity(self, pointer: str):
        """Retourne l'entité correspondant au pointeur."""
        if not self.is_loaded():
            return None
        return self.gedcom_service.get_entity(pointer)

    def get_individual(self, pointer: str):
        """Retourne l'individu correspondant au pointeur."""
        if not self.is_loaded():
            return None
        return self.entity_controller.get_individual(pointer)

    def format_details(self, details):
        """Fusionne les continuations CONT/CONC d'une liste de détails."""
        if self.presentation_controller is None:
            return merge_text_continuations(details)
        return self.presentation_controller.format_details(details)

    def format_entity_summary(self, entity_type, entity):
        """Retourne le résumé d'en-tête d'une entité."""
        if self.presentation_controller is None:
            return {"title": "", "subtitle": "", "facts": []}
        return self.presentation_controller.format_entity_summary(entity_type, entity)

    def format_entity_label(self, entity, entity_type: str | None = None):
        """Formate le libellé d'une entité."""
        if self.search_controller is None:
            return str(getattr(entity, "pointer", "") or "")
        return self.search_controller.format_entity_label(entity, entity_type)

    def format_entity_display_name(self, entity, entity_type: str | None = None):
        """Formate le nom d'affichage d'une entité."""
        return self._entity_list_presenter().format_display_name(entity, entity_type)

    def get_entity_sort_key(self, entity, entity_type: str, column: str):
        """Retourne la clé de tri d'une entité pour une colonne."""
        return self._entity_list_presenter().sort_key(entity, entity_type, column)

    def get_family(self, pointer: str):
        """Retourne la famille correspondant au pointeur."""
        if not self.is_loaded():
            return None
        return self.entity_controller.get_family(pointer)

    def get_source(self, pointer: str):
        """Retourne la source correspondant au pointeur."""
        if not self.is_loaded():
            return None
        return self.entity_controller.get_source(pointer)

    def get_repository(self, pointer: str):
        """Retourne le dépôt correspondant au pointeur."""
        if not self.is_loaded():
            return None
        return self.entity_controller.get_repository(pointer)

    def get_note(self, pointer: str):
        """Retourne la note correspondant au pointeur."""
        if not self.is_loaded():
            return None
        return self.entity_controller.get_note(pointer)

    def get_object(self, pointer: str):
        """Retourne l'objet multimédia correspondant au pointeur."""
        if not self.is_loaded():
            return None
        return self.entity_controller.get_object(pointer)

    def get_submitter(self, pointer: str):
        """Retourne le soumetteur correspondant au pointeur."""
        if not self.is_loaded():
            return None
        return self.entity_controller.get_submitter(pointer)

    def get_raw_block(self, entity):
        """Retourne le bloc GEDCOM brut d'une entité."""
        if self.presentation_controller is None:
            if entity is None:
                return ""
            raw_entity = getattr(entity, "entity", entity)
            if hasattr(raw_entity, "raw_block"):
                try:
                    return raw_entity.raw_block()
                except Exception:
                    return ""
            return ""
        return self.presentation_controller.get_raw_block(entity)

    def resolve_pointer(self, pointer: str):
        """Résout un pointeur vers l'entité cible."""
        if self.presentation_controller is None:
            return None
        return self.presentation_controller.resolve_pointer(pointer)

    def get_entity_view_context(self, entity):
        """Retourne le contexte de vue d'une entité."""
        if self.presentation_controller is None:
            return PresentationController.default_display_info(entity)
        return self.presentation_controller.get_entity_view_context(entity)

    def extract_head(self):
        """Retourne le bloc HEAD du fichier."""
        return self.gedcom_service.extract_head()

    def extract_trailer(self):
        """Retourne le bloc TRLR du fichier."""
        return self.gedcom_service.extract_trailer()
