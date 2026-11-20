"""Construction du contexte d'affichage et résolution de pointeurs."""

import functools
import logging

from controllers.detail_formatter import merge_text_continuations

logger = logging.getLogger(__name__)

RESOLVER_BY_TAG = {
    "INDI": "get_individual",
    "FAM": "get_family",
    "SOUR": "get_source",
    "REPO": "get_repository",
    "NOTE": "get_note",
    "OBJE": "get_object",
    "SUBM": "get_submitter",
}


def _requires_loaded(default=None):
    """Décore une méthode pour la court-circuiter si le contrôleur n'est pas chargé."""

    def decorator(method):
        """Enveloppe la méthode avec la garde de chargement."""

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            """Retourne la valeur par défaut si le contrôleur n'est pas chargé."""
            if not self.is_loaded():
                return default() if callable(default) else default
            return method(self, *args, **kwargs)

        return wrapper

    return decorator


class ViewContextBuilder:
    """Construit le contexte d'affichage d'une entité et résout les pointeurs."""

    def __init__(self, gedcom_service, entity_controller, translator=None):
        """Initialise le constructeur avec le service et le contrôleur d'entités."""
        self.gedcom_service = gedcom_service
        self.entity_controller = entity_controller
        self.translator = translator

    def is_loaded(self):
        """Indique si les dépendances sont chargées."""
        return (
            self.gedcom_service is not None
            and self.entity_controller is not None
            and self.gedcom_service.is_loaded()
        )

    @_requires_loaded()
    def get_entity(self, pointer: str):
        """Retourne l'entité correspondant au pointeur."""
        return self.gedcom_service.get_entity(pointer)

    @_requires_loaded()
    def get_individual(self, pointer: str):
        """Retourne l'individu correspondant au pointeur."""
        return self.entity_controller.get_individual(pointer)

    @_requires_loaded()
    def get_family(self, pointer: str):
        """Retourne la famille correspondant au pointeur."""
        return self.entity_controller.get_family(pointer)

    @_requires_loaded()
    def get_source(self, pointer: str):
        """Retourne la source correspondant au pointeur."""
        return self.entity_controller.get_source(pointer)

    @_requires_loaded()
    def get_repository(self, pointer: str):
        """Retourne le dépôt correspondant au pointeur."""
        return self.entity_controller.get_repository(pointer)

    @_requires_loaded()
    def get_note(self, pointer: str):
        """Retourne la note correspondant au pointeur."""
        return self.entity_controller.get_note(pointer)

    @_requires_loaded()
    def get_object(self, pointer: str):
        """Retourne l'objet multimédia correspondant au pointeur."""
        return self.entity_controller.get_object(pointer)

    @_requires_loaded()
    def get_submitter(self, pointer: str):
        """Retourne le soumetteur correspondant au pointeur."""
        return self.entity_controller.get_submitter(pointer)

    @_requires_loaded()
    def resolve_pointer(self, pointer: str):
        """Résout un pointeur vers l'entité cible (tout type).

        Les pointeurs de citations sont résolus vers l'enregistrement `SOUR`
        qu'ils référencent, jamais vers une entité `CITE` fictive.
        """
        if not pointer:
            return None

        raw_entity = self.gedcom_service.get_entity(pointer)
        if raw_entity is None:
            return None

        getter_name = RESOLVER_BY_TAG.get(raw_entity.tag)
        if getter_name is None:
            return self.get_entity(pointer)
        return getattr(self, getter_name)(pointer)

    @_requires_loaded(default="")
    def get_raw_block(self, entity):
        """Retourne le bloc GEDCOM brut d'une entité."""
        if entity is None:
            return ""

        inner = getattr(entity, "entity", None)
        try:
            source = inner if inner is not None else entity
            raw_block = getattr(source, "raw_block", None)
            if callable(raw_block):
                raw_block = raw_block()
            return raw_block if isinstance(raw_block, str) else ""
        except Exception:
            logger.exception("Échec de lecture du bloc brut")
            return ""

    def format_details(self, details):
        """Fusionne les continuations CONT/CONC d'une liste de détails."""
        return merge_text_continuations(details)

    @_requires_loaded(
        default=lambda: {"type": "raw", "entity": None, "raw_entity": None}
    )
    def get_entity_view_context(self, entity):
        """Retourne le contexte de vue d'une entité."""
        if entity is None:
            return {"type": "raw", "entity": None, "raw_entity": None}

        raw_entity = getattr(entity, "entity", None)
        if raw_entity is not None:
            from controllers.entity_types import ENTITY_CONTEXT_BY_TYPE

            context_type = ENTITY_CONTEXT_BY_TYPE.get(raw_entity.tag)
            if context_type and context_type != "citation":
                return {
                    "type": context_type,
                    "entity": entity,
                    "raw_entity": raw_entity,
                }
            return {"type": "raw", "entity": entity, "raw_entity": raw_entity}

        if getattr(entity, "source_pointer", None) is not None:
            return {"type": "citation", "entity": entity, "raw_entity": entity}

        if getattr(entity, "tag", None) == "FAM":
            pointer = getattr(entity, "pointer", None)
            family = self.get_family(pointer) if pointer else None
            if family:
                return {
                    "type": "family",
                    "entity": family,
                    "raw_entity": family.entity,
                }

        return {"type": "raw", "entity": entity, "raw_entity": entity}

    @_requires_loaded(
        default=lambda: {
            "type": "raw",
            "entity": None,
            "raw_entity": None,
            "raw_block": "",
        }
    )
    def get_entity_display_info(self, entity):
        """Retourne le contexte d'affichage complet d'une entité."""
        if entity is None:
            return {
                "type": "raw",
                "entity": None,
                "raw_entity": None,
                "raw_block": "",
            }

        context = self.get_entity_view_context(entity)
        raw_entity = context.get("raw_entity")
        context["raw_block"] = self.get_raw_block(raw_entity) if raw_entity else ""
        return context

    @_requires_loaded(default="")
    def extract_head(self):
        """Retourne le bloc HEAD du fichier."""
        return self.gedcom_service.extract_head()

    @_requires_loaded(default="")
    def extract_trailer(self):
        """Retourne le bloc TRLR du fichier."""
        return self.gedcom_service.extract_trailer()

    @staticmethod
    def default_display_info(entity):
        """Construit un contexte d'affichage minimal sans contrôleurs chargés."""
        raw_entity = getattr(entity, "entity", entity)
        raw_block = ""
        if hasattr(raw_entity, "raw_block"):
            try:
                raw_block = raw_entity.raw_block()
            except Exception:
                raw_block = ""
        return {
            "type": "raw",
            "entity": entity,
            "raw_entity": raw_entity,
            "raw_block": raw_block,
        }
