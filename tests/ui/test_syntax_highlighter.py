"""Tests de la coloration syntaxique GEDCOM : niveaux, pointeurs, tags et dates."""

import tkinter as tk
import unittest

from ui.syntax_highlighter import GedcomHighlighter

SAMPLE = (
    "0 @I1@ INDI\n"
    "1 NAME John /Doe/\n"
    "1 BIRT\n"
    "2 DATE 1 JAN 1900\n"
    "2 PLAC Paris\n"
)


class TestGedcomHighlighter(unittest.TestCase):
    """Vérifie la coloration des niveaux, pointeurs, tags et dates."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.text = tk.Text(self.root)
        self.highlighter = GedcomHighlighter(self.text)

    def tearDown(self):
        self.root.destroy()

    def _insert(self, content):
        self.text.insert("1.0", content)
        self.highlighter.highlight()

    # Vérifie highlights level tag.
    def test_highlights_level_tag(self):
        # Given (Arrange) un bloc GEDCOM inséré
        self._insert(SAMPLE)
        # When (Act) on applique la coloration
        ranges = self.text.tag_ranges("level")
        # Then (Assert) le tag "level" est appliqué
        self.assertTrue(ranges)

    # Vérifie highlights pointer.
    def test_highlights_pointer(self):
        # Given (Arrange) un bloc GEDCOM contenant un pointeur
        self._insert(SAMPLE)
        # When (Act) on applique la coloration
        ranges = self.text.tag_ranges("pointer")
        # Then (Assert) le tag "pointer" est appliqué
        self.assertTrue(ranges)

    # Vérifie highlights tag keyword.
    def test_highlights_tag_keyword(self):
        # Given (Arrange) un bloc GEDCOM contenant des tags
        self._insert(SAMPLE)
        # When (Act) on applique la coloration
        ranges = self.text.tag_ranges("tag")
        # Then (Assert) le tag "tag" est appliqué
        self.assertTrue(ranges)

    # Vérifie highlights date.
    def test_highlights_date(self):
        # Given (Arrange) un bloc GEDCOM contenant une date
        self._insert(SAMPLE)
        # When (Act) on applique la coloration
        ranges = self.text.tag_ranges("date")
        # Then (Assert) le tag "date" est appliqué
        self.assertTrue(ranges)

    # Vérifie no tags on empty content.
    def test_no_tags_on_empty_content(self):
        # Given (Arrange) un widget vide
        # When (Act) on applique la coloration
        self.highlighter.highlight()
        all_ranges = {
            tag: self.text.tag_ranges(tag)
            for tag in ("level", "tag", "pointer", "date", "value")
        }
        # Then (Assert) aucun tag n'est appliqué
        self.assertTrue(all(not ranges for ranges in all_ranges.values()))

    # Vérifie rehighlight clears previous pointer.
    def test_rehighlight_clears_previous_pointer(self):
        # Given (Arrange) un bloc avec un pointeur, puis remplacé par un bloc sans
        self._insert(SAMPLE)
        self.text.delete("1.0", "end")
        # When (Act) on recolore le nouveau contenu
        self._insert("0 TRLR\n")
        pointer_ranges = self.text.tag_ranges("pointer")
        # Then (Assert) aucun pointeur de l'ancien contenu ne subsiste
        pointer_text = self.text.get(*pointer_ranges) if pointer_ranges else ""
        self.assertNotIn("@I1@", pointer_text)


if __name__ == "__main__":
    unittest.main()
