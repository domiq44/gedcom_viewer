"""Tests du constructeur de la fenêtre principale."""

import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ui.main_window_builder import MainWindowBuilder
from ui.tooltip import Tooltip


class TestMainWindowBuilder(unittest.TestCase):
    """Vérifie l'assemblage des composants de la fenêtre principale."""

    # Vérifie build calls all builders.
    def test_build_calls_all_builders(self):
        # Given un constructeur et un hôte simulé
        host = Mock()
        builder = MainWindowBuilder(host)

        # When on construit la fenêtre
        with (
            patch.object(builder, "_build_app_header") as header,
            patch.object(builder, "_build_layout") as layout,
            patch.object(builder, "_build_entity_type_panel") as type_panel,
            patch.object(builder, "_build_entity_viewer") as viewer,
            patch.object(builder, "_build_detail_views") as detail_views,
        ):
            builder.build()

        # Then chaque étape de construction est appelée une fois
        header.assert_called_once()
        layout.assert_called_once()
        type_panel.assert_called_once()
        viewer.assert_called_once()
        detail_views.assert_called_once()

    # Vérifie build layout creates main panes.
    def test_build_layout_creates_main_panes(self):
        # Given une fenêtre racine
        root = tk.Tk()
        root.withdraw()
        host = SimpleNamespace(root=root)

        try:
            # When on construit la disposition
            MainWindowBuilder(host)._build_layout()

            # Then les conteneurs principaux sont créés
            self.assertIsNotNone(host.central_frame)
            self.assertIsNotNone(host.main_pane)
            self.assertIsNotNone(host.left_frame)
            self.assertIsNotNone(host.right_frame)
        finally:
            root.destroy()

    # Vérifie build app header creates and packs header.
    def test_build_app_header_creates_and_packs_header(self):
        # Given un hôte et un en-tête simulé
        host = SimpleNamespace(
            root=Mock(), translator=Mock(), show_ancestor_tree=Mock()
        )
        header = Mock()
        builder = MainWindowBuilder(host)

        # When on construit l'en-tête
        with patch("ui.main_window_builder.AppHeader", return_value=header):
            builder._build_app_header()

        # Then l'en-tête est créé et empilé
        self.assertIs(host.app_header, header)
        header.pack.assert_called_once_with(fill="x", padx=10, pady=(10, 0))

    # Vérifie build entity type panel creates browser and coordinator.
    def test_build_entity_type_panel_creates_browser_and_coordinator(self):
        # Given un hôte avec des conteneurs simulés
        root = tk.Tk()
        root.withdraw()
        host = SimpleNamespace(
            root=root,
            translator=Mock(),
            controller=Mock(),
            show_entity=Mock(),
            show_ancestor_tree=Mock(),
            _clear_empty_entity_selection=Mock(),
            entity_view_manager=Mock(),
            on_entity_type_change=Mock(),
            entity_type_tabs_frame=Mock(),
            left_frame=Mock(),
            main_pane=Mock(),
        )
        type_var = Mock()
        panel = Mock()
        browser = Mock()
        coordinator = Mock()

        try:
            # When on construit le panneau de types
            with (
                patch("ui.main_window_builder.tk.StringVar", return_value=type_var),
                patch("ui.main_window_builder.EntityTypePanel", return_value=panel),
                patch("ui.main_window_builder.EntityListBrowser", return_value=browser),
                patch(
                    "ui.main_window_builder.EntitySelectionCoordinator",
                    return_value=coordinator,
                ),
            ):
                MainWindowBuilder(host)._build_entity_type_panel()

            # Then les composants sont créés et le changement de type est tracé
            self.assertIs(host.entity_type_tabs, panel)
            self.assertIs(host.entity_browser, browser)
            self.assertIs(host.entity_selection_coordinator, coordinator)
            type_var.trace_add.assert_called_once_with(
                "write", host.on_entity_type_change
            )
        finally:
            root.destroy()

    # Vérifie build detail views delegates to manager.
    def test_build_detail_views_delegates_to_manager(self):
        # Given un hôte et un gestionnaire de vues simulé
        host = SimpleNamespace(
            detail_panel=Mock(),
            translator=Mock(),
            navigate_to=Mock(),
            controller=Mock(),
            entity_view_manager=Mock(),
        )
        view_map = {"INDI": (Mock(), Mock())}
        host.entity_view_manager.build_views.return_value = view_map

        # When on construit les vues de détail
        MainWindowBuilder(host)._build_detail_views()

        # Then le gestionnaire reçoit les résolveurs et la carte est mémorisée
        host.entity_view_manager.build_views.assert_called_once()
        self.assertEqual(
            host.entity_view_manager.build_views.call_args.args[0],
            host.detail_panel.entity_detail_container,
        )
        self.assertEqual(
            host.entity_view_manager.build_views.call_args.args[1], host.translator
        )
        self.assertEqual(
            host.entity_view_manager.build_views.call_args.args[2], host.navigate_to
        )
        self.assertEqual(
            host.entity_view_manager.build_views.call_args.kwargs["tooltip_factory"],
            Tooltip,
        )
        self.assertEqual(host._entity_view_map, view_map)

    # Vérifie build navigation and status bars.
    def test_build_navigation_and_status_bars(self):
        # Given un hôte avec un conteneur simulé et une racine Tk
        root = tk.Tk()
        root.withdraw()
        host = SimpleNamespace(
            root=root,
            right_frame=Mock(),
            translator=Mock(),
            go_back=Mock(),
            go_forward=Mock(),
        )
        host.translator.get.return_value = "Prêt"
        navigation_bar = Mock()
        status_bar = Mock()

        try:
            # When on construit les barres
            with (
                patch(
                    "ui.main_window_builder.NavigationBar", return_value=navigation_bar
                ),
                patch("ui.main_window_builder.StatusBar", return_value=status_bar),
            ):
                builder = MainWindowBuilder(host)
                builder._build_navigation_bar()
                builder._build_status_bar()

            # Then les barres sont créées et positionnées
            self.assertIs(host.nav_toolbar, navigation_bar)
            self.assertIs(host.log_status_frame, status_bar)
            navigation_bar.grid.assert_called_once()
            status_bar.grid.assert_called_once()
        finally:
            root.destroy()

    # Vérifie build registers theme aware components.
    def test_build_registers_theme_aware_components(self):
        # Given un hôte avec un registre de thème et des composants
        host = SimpleNamespace(
            theme_registry=Mock(),
            app_header=Mock(),
            entity_type_tabs=Mock(),
            entity_browser=Mock(),
            nav_toolbar=Mock(),
            log_status_frame=Mock(),
            detail_panel=Mock(),
        )
        builder = MainWindowBuilder(host)

        # When on construit la fenêtre
        with (
            patch.object(builder, "_build_app_header"),
            patch.object(builder, "_build_layout"),
            patch.object(builder, "_build_entity_type_panel"),
            patch.object(builder, "_build_entity_viewer"),
            patch.object(builder, "_build_detail_views"),
        ):
            builder.build()

        # Then chaque composant est enregistré dans le registre
        registered = {
            call.args[0] for call in host.theme_registry.register.call_args_list
        }
        self.assertEqual(
            registered,
            {
                host.app_header,
                host.entity_type_tabs,
                host.entity_browser,
                host.nav_toolbar,
                host.log_status_frame,
                host.detail_panel,
            },
        )

    # Vérifie build registers detail views.
    def test_build_registers_detail_views(self):
        # Given un hôte avec un gestionnaire de vues de détail
        first_view = Mock()
        second_view = Mock()
        host = SimpleNamespace(
            theme_registry=Mock(),
            entity_view_manager=SimpleNamespace(
                views={"individual": first_view, "family": second_view}
            ),
        )
        builder = MainWindowBuilder(host)

        # When on enregistre les composants thémables
        builder._register_theme_aware()

        # Then chaque vue de détail est enregistrée
        registered = {
            call.args[0] for call in host.theme_registry.register.call_args_list
        }
        self.assertEqual(registered, {first_view, second_view})


if __name__ == "__main__":
    unittest.main()
