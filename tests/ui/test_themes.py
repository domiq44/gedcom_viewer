"""Tests du module de thèmes : palettes et changement de thème à l'exécution."""

import unittest

from ui.themes import (
    COLORS,
    DARK_COLORS,
    LIGHT_COLORS,
    THEMES,
    current_theme,
    set_theme,
)


class TestThemes(unittest.TestCase):
    """Vérifie la cohérence des palettes et l'activation d'un thème."""

    def tearDown(self):
        # Given (Arrange) un thème potentiellement modifié par le test
        # When (Act) on revient au thème clair par défaut
        set_theme("light")
        # Then (Assert) le thème clair est bien restauré
        self.assertEqual(current_theme(), "light")

    # Vérifie light and dark palettes share keys.
    def test_light_and_dark_palettes_share_keys(self):
        # Given (Arrange) les deux palettes de couleurs
        # When (Act) on compare leurs clés
        # Then (Assert) elles définissent exactement les mêmes rôles
        self.assertEqual(set(LIGHT_COLORS), set(DARK_COLORS))

    # Vérifie new theme roles are defined.
    def test_new_theme_roles_are_defined(self):
        # Given (Arrange) la palette claire
        # When (Act) on vérifie la présence des rôles ajoutés
        # Then (Assert) chaque rôle existe dans les deux palettes
        for role in (
            "header_background",
            "section_title",
            "tooltip_background",
            "syntax_tag",
        ):
            self.assertIn(role, LIGHT_COLORS)
            self.assertIn(role, DARK_COLORS)

    # Vérifie set theme updates colors.
    def test_set_theme_updates_colors(self):
        # Given (Arrange) le thème clair actif
        set_theme("light")
        # When (Act) on active le thème sombre
        set_theme("dark")
        # Then (Assert) COLORS reflète la palette sombre
        self.assertEqual(COLORS["background"], DARK_COLORS["background"])
        self.assertEqual(current_theme(), "dark")

    # Vérifie set theme restores light.
    def test_set_theme_restores_light(self):
        # Given (Arrange) le thème sombre actif
        set_theme("dark")
        # When (Act) on repasse au thème clair
        set_theme("light")
        # Then (Assert) COLORS reflète la palette claire
        self.assertEqual(COLORS["background"], LIGHT_COLORS["background"])

    # Vérifie set theme rejects unknown.
    def test_set_theme_rejects_unknown(self):
        # Given (Arrange) un nom de thème inconnu
        name = "inconnu"
        # When (Act) / Then (Assert) une erreur est levée
        with self.assertRaises(ValueError):
            set_theme(name)

    # Vérifie themes registry exposes both palettes.
    def test_themes_registry_exposes_both_palettes(self):
        # Given (Arrange) le registre des thèmes
        # When (Act) on lit ses clés
        # Then (Assert) il contient les thèmes clair et sombre
        self.assertEqual(set(THEMES), {"light", "dark"})


if __name__ == "__main__":
    unittest.main()
