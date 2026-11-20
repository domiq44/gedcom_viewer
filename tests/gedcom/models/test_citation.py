"""Tests du modèle de citation GEDCOM."""

import unittest

from gedcom.models.citation import Citation


class TestCitation(unittest.TestCase):
    """Vérifie les propriétés dérivées d'une citation."""

    # Vérifie pointer and raw block come from source lines.
    def test_pointer_and_raw_block_come_from_source_lines(self):
        # Given une citation avec ses lignes GEDCOM
        citation = Citation(
            source_pointer="@S1@",
            owner_pointer="@I1@",
            owner_type="INDI",
            level=2,
            context_tag="BIRT",
            gedcom_lines=["2 SOUR @S1@\n", "3 PAGE 12\n"],
        )

        # When on lit le pointeur et le bloc brut
        # Then ils correspondent à la source citée
        self.assertEqual(citation.pointer, "@S1@")
        self.assertEqual(citation.raw_block, "2 SOUR @S1@\n3 PAGE 12\n")

    # Vérifie details build relative tag paths.
    def test_details_build_relative_tag_paths(self):
        # Given une citation avec une page et un rôle
        citation = Citation(
            source_pointer="@S1@",
            owner_pointer="@I1@",
            owner_type="INDI",
            level=2,
            context_tag="BIRT",
            gedcom_lines=[
                "2 SOUR @S1@\n",
                "3 PAGE 12\n",
                "4 ROLE Witness\n",
            ],
        )

        # When on demande les détails
        details = citation.details

        # Then les chemins de tags sont relatifs au niveau de la citation
        self.assertEqual(
            details,
            [
                {"tag": "PAGE", "value": "12", "level": 1},
                {"tag": "PAGE/ROLE", "value": "Witness", "level": 2},
            ],
        )

    # Vérifie details merge continuations into parent field.
    def test_details_merge_continuations_into_parent_field(self):
        # Given une citation avec un texte continué par CONT et CONC
        citation = Citation(
            source_pointer="@S1@",
            owner_pointer="@I1@",
            owner_type="INDI",
            level=2,
            gedcom_lines=[
                "2 SOUR @S1@\n",
                "3 NOTE First line\n",
                "4 CONT second line\n",
                "4 CONC !\n",
            ],
        )

        # When on demande les détails
        details = citation.details

        # Then la continuation est fusionnée dans le champ parent
        self.assertEqual(
            details,
            [{"tag": "NOTE", "value": "First line\nsecond line!", "level": 1}],
        )

    # Vérifie details are cached.
    def test_details_are_cached(self):
        # Given une citation avec des détails
        citation = Citation(
            source_pointer="@S1@",
            owner_pointer="@I1@",
            owner_type="INDI",
            level=2,
            gedcom_lines=["2 SOUR @S1@\n", "3 PAGE 12\n"],
        )

        # When on demande deux fois les détails
        first = citation.details
        second = citation.details

        # Then la même liste est renvoyée
        self.assertIs(first, second)

    # Vérifie details fusionnent TEXT avec ses continuations CONT/CONC
    # pour le cas DATA > TEXT (comme dans une citation d'acte de naissance).
    def test_details_merge_text_with_multi_line_continuations(self):
        # Given une citation avec DATA > TEXT > CONT/CONC (cas utilisateur)
        citation = Citation(
            source_pointer="@S3@",
            owner_pointer="@I1@",
            owner_type="INDI",
            level=2,
            context_tag="",
            gedcom_lines=[
                "2 SOUR @S3@\n",
                "3 PAGE Naissance Crétel\n",
                "3 EVEN BIRT\n",
                "4 ROLE CHIL\n",
                "3 DATA\n",
                "4 DATE 1963\n",
                "4 TEXT Dominique Crétel\n",
                "5 CONT N°482\n",
                "5 CONT Le dix-neuf juin mil neuf cent soixante-trois\n",
                "5 CONC est né à Armentières\n",
                "3 QUAY 3\n",
            ],
        )

        # When on demande les détails
        details = citation.details

        # Then TEXT contient son texte fusionné avec toutes les continuations
        text_detail = next(d for d in details if d.get("tag") == "DATA/TEXT")
        self.assertIn("Dominique Crétel", text_detail["value"])
        self.assertIn("N°482", text_detail["value"])
        self.assertIn(
            "Le dix-neuf juin mil neuf cent soixante-trois", text_detail["value"]
        )
        self.assertIn("est né à Armentières", text_detail["value"])


if __name__ == "__main__":
    unittest.main()
