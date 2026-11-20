"""Tests de la gestion des continuations de texte GEDCOM (CONC/CONT)."""

import unittest

from gedcom.continuations import append_continuation


class TestAppendContinuation(unittest.TestCase):
    """Vérifie l'ajout d'une continuation CONC ou CONT à un texte."""

    # Vérifie conc concatenates without separator.
    def test_conc_concatenates_without_separator(self):
        # Given (Arrange) une valeur texte
        text = "John"
        # When (Act) on ajoute une continuation CONC
        result = append_continuation(text, "CONC", "/Doe/")
        # Then (Assert) les valeurs sont concaténées sans séparateur
        self.assertEqual(result, "John/Doe/")

    # Vérifie conc concatenates words without separator.
    def test_conc_concatenates_words_without_separator(self):
        # Given (Arrange) deux mots séparés par une continuation CONC
        text = "John"
        # When (Act) on ajoute le suffixe "William"
        result = append_continuation(text, "CONC", "William")
        # Then (Assert) aucun espace n'est inséré
        self.assertEqual(result, "JohnWilliam")

    # Vérifie cont inserts newline.
    def test_cont_inserts_newline(self):
        # Given (Arrange) une première ligne
        text = "line 1"
        # When (Act) on ajoute une continuation CONT
        result = append_continuation(text, "CONT", "line 2")
        # Then (Assert) la seconde ligne est ajoutée avec un retour à la ligne
        self.assertEqual(result, "line 1\nline 2")

    # Vérifie unknown tag leaves text unchanged.
    def test_unknown_tag_leaves_text_unchanged(self):
        # Given (Arrange) une valeur texte
        text = "text"
        # When (Act) on passe un tag de continuation inconnu
        result = append_continuation(text, "OTHER", "suffix")
        # Then (Assert) le texte est inchangé
        self.assertEqual(result, "text")

    # Vérifie none text is treated as empty for conc.
    def test_none_text_is_treated_as_empty_for_conc(self):
        # Given (Arrange) un texte absent
        text = None
        # When (Act) on ajoute une continuation CONC
        result = append_continuation(text, "CONC", "abc")
        # Then (Assert) seul le suffixe est conservé
        self.assertEqual(result, "abc")

    # Vérifie none text is treated as empty for cont.
    def test_none_text_is_treated_as_empty_for_cont(self):
        # Given (Arrange) un texte absent
        text = None
        # When (Act) on ajoute une continuation CONT
        result = append_continuation(text, "CONT", "abc")
        # Then (Assert) le suffixe est précédé d'un retour à la ligne
        self.assertEqual(result, "\nabc")

    # Vérifie none value leaves conc text unchanged.
    def test_none_value_leaves_conc_text_unchanged(self):
        # Given (Arrange) un texte de base
        text = "base"
        # When (Act) on ajoute une continuation CONC sans valeur
        result = append_continuation(text, "CONC", None)
        # Then (Assert) le texte est inchangé
        self.assertEqual(result, "base")

    # Vérifie none value leaves cont text with newline.
    def test_none_value_leaves_cont_text_with_newline(self):
        # Given (Arrange) un texte de base
        text = "base"
        # When (Act) on ajoute une continuation CONT sans valeur
        result = append_continuation(text, "CONT", None)
        # Then (Assert) un retour à la ligne est tout de même ajouté
        self.assertEqual(result, "base\n")


if __name__ == "__main__":
    unittest.main()
