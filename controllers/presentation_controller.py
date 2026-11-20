"""Contrôleur de mise en forme des entités pour l'affichage.

Orchestre trois composants à responsabilité unique :
- ``ViewContextBuilder`` : résolution de pointeurs et contexte d'affichage.
- ``SummaryFormatter`` : construction des résumés (titre, sous-titre, faits).
- ``TextFormatter`` : formatage de texte (nettoyage de nom, durée de vie, etc.).
"""

import functools
import logging

from controllers.summary_formatter import SummaryFormatter
from controllers.text_formatting import TextFormatter
from controllers.view_context import ViewContextBuilder

logger = logging.getLogger(__name__)

SUMMARY_MAX_FACTS = 4


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


class PresentationController:
    """Transforme les entités en contexte d'affichage pour l'UI.

    Délègue à des sous-composants à responsabilité unique :
    résolution de pointeurs/contexte, formatage des résumés et formatage texte.
    """

    RESOLVER_BY_TAG = {
        "INDI": "get_individual",
        "FAM": "get_family",
        "SOUR": "get_source",
        "REPO": "get_repository",
        "NOTE": "get_note",
        "OBJE": "get_object",
        "SUBM": "get_submitter",
    }

    def __init__(self, gedcom_service, entity_controller, translator=None):
        """Initialise le contrôleur avec le service et le contrôleur d'entités."""
        self.gedcom_service = gedcom_service
        self.entity_controller = entity_controller
        self.translator = translator
        self._text_formatter = TextFormatter(translator)
        self._summary_formatter = SummaryFormatter(self._text_formatter)
        self._view_context_builder = ViewContextBuilder(
            gedcom_service, entity_controller, translator
        )

    def is_loaded(self):
        """Indique si les dépendances sont chargées."""
        return self._view_context_builder.is_loaded()

    @_requires_loaded()
    def get_entity(self, pointer: str):
        """Retourne l'entité correspondant au pointeur."""
        return self._view_context_builder.get_entity(pointer)

    @_requires_loaded()
    def get_individual(self, pointer: str):
        """Retourne l'individu correspondant au pointeur."""
        return self._view_context_builder.get_individual(pointer)

    @_requires_loaded()
    def get_family(self, pointer: str):
        """Retourne la famille correspondant au pointeur."""
        return self._view_context_builder.get_family(pointer)

    @_requires_loaded()
    def get_source(self, pointer: str):
        """Retourne la source correspondant au pointeur."""
        return self._view_context_builder.get_source(pointer)

    @_requires_loaded()
    def get_repository(self, pointer: str):
        """Retourne le dépôt correspondant au pointeur."""
        return self._view_context_builder.get_repository(pointer)

    @_requires_loaded()
    def get_note(self, pointer: str):
        """Retourne la note correspondant au pointeur."""
        return self._view_context_builder.get_note(pointer)

    @_requires_loaded()
    def get_object(self, pointer: str):
        """Retourne l'objet multimédia correspondant au pointeur."""
        return self._view_context_builder.get_object(pointer)

    @_requires_loaded()
    def get_submitter(self, pointer: str):
        """Retourne le soumetteur correspondant au pointeur."""
        return self._view_context_builder.get_submitter(pointer)

    @_requires_loaded()
    def resolve_pointer(self, pointer: str):
        """Résout un pointeur vers l'entité cible (tout type).

        Les pointeurs de citations sont résolus vers l'enregistrement `SOUR`
        qu'ils référencent, jamais vers une entité `CITE` fictive.
        """
        return self._view_context_builder.resolve_pointer(pointer)

    @_requires_loaded(default="")
    def get_raw_block(self, entity):
        """Retourne le bloc GEDCOM brut d'une entité."""
        return self._view_context_builder.get_raw_block(entity)

    def format_details(self, details):
        """Fusionne les continuations CONT/CONC d'une liste de détails."""
        return self._view_context_builder.format_details(details)

    def format_entity_summary(self, entity_type, entity):
        """Retourne le titre, le sous-titre et les faits d'une entité."""
        return self._summary_formatter.format_entity_summary(entity_type, entity)

    def get_entity_view_context(self, entity):
        """Retourne le contexte de vue d'une entité."""
        return self._view_context_builder.get_entity_view_context(entity)

    def get_entity_display_info(self, entity):
        """Retourne le contexte d'affichage complet d'une entité."""
        return self._view_context_builder.get_entity_display_info(entity)

    def extract_head(self):
        """Retourne le bloc HEAD du fichier."""
        return self._view_context_builder.extract_head()

    def extract_trailer(self):
        """Retourne le bloc TRLR du fichier."""
        return self._view_context_builder.extract_trailer()

    @staticmethod
    def default_display_info(entity):
        """Construit un contexte d'affichage minimal sans contrôleurs chargés."""
        return ViewContextBuilder.default_display_info(entity)
