"""Tests du formatage des détails : fusion des continuations CONT/CONC."""

import unittest

from controllers.detail_formatter import merge_text_continuations


class TestMergeTextContinuations(unittest.TestCase):
    """Vérifie la fusion des continuations dans le texte parent."""

    # Vérifie flat conc merges into preceding text.
    def test_flat_conc_merges_into_preceding_text(self):
        # Given (Arrange) un texte suivi d'une continuation CONC plate
        items = [{"tag": "TEXT", "value": "John"}, {"tag": "CONC", "value": "/Doe/"}]
        # When (Act) on fusionne les continuations
        result = merge_text_continuations(items)
        # Then (Assert) la valeur du texte intègre la continuation
        self.assertEqual(result, [{"tag": "TEXT", "value": "John/Doe/"}])

    # Vérifie flat cont inserts newline.
    def test_flat_cont_inserts_newline(self):
        # Given (Arrange) un texte suivi d'une continuation CONT plate
        items = [
            {"tag": "NOTE", "value": "line 1"},
            {"tag": "CONT", "value": "line 2"},
        ]
        # When (Act) on fusionne les continuations
        result = merge_text_continuations(items)
        # Then (Assert) la valeur contient un retour à la ligne
        self.assertEqual(result, [{"tag": "NOTE", "value": "line 1\nline 2"}])

    # Vérifie path conc merges into parent path.
    def test_path_conc_merges_into_parent_path(self):
        # Given (Arrange) un TEXT typé par chemin, suivi d'un CONT enfant
        items = [
            {"tag": "DATA/EVEN/TEXT", "value": "base"},
            {"tag": "DATA/EVEN/TEXT/CONT", "value": " suite"},
        ]
        # When (Act) on fusionne les continuations
        result = merge_text_continuations(items)
        # Then (Assert) le parent voit sa valeur complétée
        self.assertEqual(result, [{"tag": "DATA/EVEN/TEXT", "value": "base\n suite"}])

    # Vérifie non text tag is preserved as is.
    def test_non_text_tag_is_preserved_as_is(self):
        # Given (Arrange) un tag arbitraire entre deux textes
        items = [{"tag": "DATE", "value": "1900"}]
        # When (Act) on fusionne les continuations
        result = merge_text_continuations(items)
        # Then (Assert) le tag est conservé sans modification
        self.assertEqual(result, [{"tag": "DATE", "value": "1900"}])

    # Vérifie continuation without text parent is kept.
    def test_continuation_without_text_parent_is_kept(self):
        # Given (Arrange) une continuation CONT sans texte parent
        items = [{"tag": "CONT", "value": "orpheline"}]
        # When (Act) on fusionne les continuations
        result = merge_text_continuations(items)
        # Then (Assert) la continuation est conservée telle quelle
        self.assertEqual(result, [{"tag": "CONT", "value": "orpheline"}])

    # Vérifie input is not mutated.
    def test_input_is_not_mutated(self):
        # Given (Arrange) une liste d'items
        items = [{"tag": "TEXT", "value": "a"}, {"tag": "CONC", "value": "b"}]
        # When (Act) on fusionne les continuations
        merge_text_continuations(items)
        # Then (Assert) la liste d'origine est inchangée
        self.assertEqual(
            items, [{"tag": "TEXT", "value": "a"}, {"tag": "CONC", "value": "b"}]
        )
