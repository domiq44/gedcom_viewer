"""Base commune des vues d'entité et protocole de résolution de pointeurs.

Ce module définit ``EntityViewBase``, socle de toutes les vues de détail par
entité. Il centralise la détection des pointeurs GEDCOM (`@I1@`), leur
résolution vers l'entité cible et le formatage de leur libellé affiché.

Protocole des résolveurs (injection de fonctions par l'interface) :
chaque ``set_*_resolver`` accepte un callable dont la signature et le rôle sont
précisés ci-dessous. Ces fonctions permettent aux vues de rester découplées du
contrôleur (aucune référence directe) et de supporter le remplacement de session.

- ``set_pointer_resolver(fn)`` : ``fn(pointer: str) -> entity | None``. Résout un
  pointeur générique vers l'entité cible ; prioritaire sur les résolveurs par type.
- ``set_name_resolver(fn)`` : ``fn(pointer: str) -> Individual | None``.
- ``set_family_name_resolver(fn)`` : ``fn(pointer: str) -> Family | None``.
- ``set_source_resolver(fn)`` : ``fn(pointer: str) -> Source | None``.
- ``set_note_resolver(fn)`` : ``fn(pointer: str) -> Note | None``.
- ``set_object_resolver(fn)`` : ``fn(pointer: str) -> MultimediaObject | None``.
- ``set_family_member_resolver(fn)`` : ``fn(pointer: str) -> Individual | None``.
- ``set_display_name_resolver(fn)`` : ``fn(entity, entity_type) -> str`` (libellé
  générique d'une entité pour un pointeur affiché).
- ``set_family_display_name_resolver(fn)`` : ``fn(entity, entity_type) -> str``.
- ``set_object_display_name_resolver(fn)`` : ``fn(entity, entity_type) -> str``.
- ``set_details_formatter_resolver(fn)`` : ``fn(details) -> list``. Regroupe les
  continuations CONT/CONC dans les détails d'affichage.

Conventions : un résolveur absent ou non applicable renvoie ``None`` ; les vues
retombent alors sur le pointeur brut. Toute exception est journalisée sans
interrompre le rendu.
"""

import logging
from tkinter import ttk

from ui.i18n import Translator

logger = logging.getLogger(__name__)


class EntityViewBase(ttk.Frame):
    """Base commune aux vues d'entité et à leur navigation par pointeur.

    Voir le cartouche de module pour le protocole complet des résolveurs.
    """

    def __init__(self, parent, on_pointer_click, translator=None, entity_type="INDI"):
        """Initialise la vue d'entité."""
        super().__init__(parent, padding=10)
        self.on_pointer_click_callback = on_pointer_click
        self.translator = translator or Translator()
        self.entity_type = entity_type
        self.pointer_resolver = None
        self.display_name_resolver = None
        self.family_name_resolver = None
        self.family_member_resolver = None
        self.family_display_name_resolver = None
        self.name_resolver = None
        self.source_resolver = None
        self.note_resolver = None
        self.object_resolver = None
        self.object_display_name_resolver = None
        self.details_formatter_resolver = None

    @staticmethod
    def _is_pointer(value):
        """Indique si une valeur est un pointeur GEDCOM."""
        return (
            isinstance(value, str)
            and value.startswith("@")
            and value.endswith("@")
            and len(value) > 2
        )

    @staticmethod
    def _resolved_entity_type(target):
        """Retourne le type d'entité résolu."""
        entity = getattr(target, "entity", None)
        entity_type = getattr(entity, "tag", None) or getattr(target, "tag", None)
        return entity_type if isinstance(entity_type, str) else None

    def _resolve_pointer_target(self, pointer):
        """Résout la cible d'un pointeur."""
        if callable(self.pointer_resolver):
            try:
                target = self.pointer_resolver(pointer)
            except Exception:
                logger.exception("Échec de résolution du pointeur %s", pointer)
                return None, None
            if target is not None:
                return target, self._resolved_entity_type(target)
            return None, None

        resolvers = (
            (self.name_resolver, "INDI"),
            (self.family_name_resolver, "FAM"),
            (self.source_resolver, "SOUR"),
            (self.note_resolver, "NOTE"),
            (self.object_resolver, "OBJE"),
        )
        for resolver, entity_type in resolvers:
            if not callable(resolver):
                continue
            try:
                target = resolver(pointer)
            except Exception:
                logger.exception("Échec de résolution du pointeur %s", pointer)
                continue
            if target is not None:
                return target, self._resolved_entity_type(target) or entity_type
        return None, None

    def _pointer_entity_type(self, pointer):
        """Retourne le type d'entité d'un pointeur."""
        target, entity_type = self._resolve_pointer_target(pointer)
        return entity_type if target is not None else None

    def _display_pointer(self, pointer):
        """Affiche un pointeur cliquable."""
        target, target_type = self._resolve_pointer_target(pointer)
        if target is None:
            return pointer

        formatter = self.display_name_resolver
        if target_type == "FAM":
            formatter = self.family_display_name_resolver or formatter
        elif target_type == "OBJE":
            formatter = self.object_display_name_resolver or formatter
        try:
            if callable(formatter):
                name = formatter(target, target_type)
            else:
                name = (
                    getattr(target, "title", None)
                    or getattr(target, "name", None)
                    or getattr(target, "text", None)
                )
            if isinstance(name, str) and name:
                return f"{name} ({pointer})"
            fallback = (
                getattr(target, "title", None)
                or getattr(target, "name", None)
                or getattr(target, "text", None)
            )
            if isinstance(fallback, str) and fallback:
                return f"{fallback} ({pointer})"
        except Exception:
            logger.exception("Échec de résolution du pointeur %s", pointer)
        return pointer

    def _navigate_pointer(self, pointer):
        """Navigue vers un pointeur."""
        if callable(self.on_pointer_click_callback):
            self.on_pointer_click_callback(pointer)

    def set_pointer_resolver(self, resolver):
        """Définit le résolveur générique ``fn(pointer) -> entity | None``."""
        self.pointer_resolver = resolver

    def set_display_name_resolver(self, resolver):
        """Définit le résolveur de libellé ``fn(entity, entity_type) -> str``."""
        self.display_name_resolver = resolver

    def set_family_name_resolver(self, resolver):
        """Définit le résolveur de famille ``fn(pointer) -> Family | None``."""
        self.family_name_resolver = resolver

    def set_family_member_resolver(self, resolver):
        """Définit le résolveur de membre de famille ``fn(pointer) -> Individual``."""
        self.family_member_resolver = resolver

    def set_family_display_name_resolver(self, resolver):
        """Définit le résolveur de libellé de famille ``fn(entity, type) -> str``."""
        self.family_display_name_resolver = resolver

    def set_name_resolver(self, resolver):
        """Définit le résolveur d'individu ``fn(pointer) -> Individual | None``."""
        self.name_resolver = resolver

    def set_source_resolver(self, resolver):
        """Définit le résolveur de source ``fn(pointer) -> Source | None``."""
        self.source_resolver = resolver

    def set_note_resolver(self, resolver):
        """Définit le résolveur de note ``fn(pointer) -> Note | None``."""
        self.note_resolver = resolver

    def set_object_resolver(self, resolver):
        """Définit le résolveur d'objet ``fn(pointer) -> MultimediaObject | None``."""
        self.object_resolver = resolver

    def set_object_display_name_resolver(self, resolver):
        """Définit le résolveur de libellé d'objet ``fn(entity, type) -> str``."""
        self.object_display_name_resolver = resolver

    def set_details_formatter_resolver(self, resolver):
        """Définit le résolveur de formatage des détails ``fn(details) -> list``."""
        self.details_formatter_resolver = resolver

    def _format_details(self, details):
        """Formate les détails via le résolveur injecté, avec repli sans erreur.

        Sans résolveur, les détails sont restitués inchangés et un avertissement
        est journalisé : les vues doivent être construites via
        ``EntityViewManager`` pour bénéficier de la fusion CONT/CONC.
        """
        resolver = self.details_formatter_resolver
        if not callable(resolver):
            logger.warning(
                "Aucun résolveur de formatage des détails ; continuations non fusionnées"
            )
            return details
        try:
            formatted = resolver(details)
        except Exception:
            logger.exception("Échec du formatage des détails")
            return details
        return formatted if isinstance(formatted, list) else details
