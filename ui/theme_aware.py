"""Registre des composants capables de se re-thémer."""

import logging
import weakref
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class ThemeAware(Protocol):
    """Protocole des composants exposant une méthode ``apply_theme``."""

    def apply_theme(self) -> None:
        """Re-applique le thème courant au composant."""
        ...


class ThemeRegistry:
    """Registre par session des composants à re-thémer."""

    def __init__(self):
        """Initialise le registre avec des références faibles."""
        self._components: weakref.WeakSet[ThemeAware] = weakref.WeakSet()

    def register(self, component):
        """Enregistre un composant exposant ``apply_theme``."""
        if callable(getattr(component, "apply_theme", None)):
            self._components.add(component)

    def apply_theme(self):
        """Re-thème tous les composants enregistrés."""
        for component in list(self._components):
            try:
                component.apply_theme()
            except Exception:
                logger.exception(
                    "Échec de l'application du thème à un composant %s",
                    type(component).__name__,
                )


def register_theme_aware_components(host):
    """Enregistre les composants de l'hôte qui savent se re-thémer."""
    names = (
        "app_header",
        "entity_type_tabs",
        "entity_browser",
        "nav_toolbar",
        "log_status_frame",
        "detail_panel",
    )
    for name in names:
        component = getattr(host, name, None)
        if component is not None:
            host.theme_registry.register(component)
    manager = getattr(host, "entity_view_manager", None)
    views = getattr(manager, "views", None)
    if isinstance(views, dict):
        for view in views.values():
            host.theme_registry.register(view)
