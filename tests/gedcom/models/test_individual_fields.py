"""Tests des champs principaux du modèle Individual (INDI)."""

import unittest

from gedcom.models.entity import GedcomEntity
from gedcom.models.individual import Individual


def make_individual(lines):
    """Construit un individu à partir de lignes GEDCOM."""
    entity = GedcomEntity("@I1@", "INDI", 0, lines=lines)
    return Individual(entity)


class TestIndividualFields(unittest.TestCase):
    """Vérifie les champs principaux de l'individu."""

    # Vérifie all level one and two fields are parsed.
    def test_all_level_one_and_two_fields_are_parsed(self):
        # Given un individu avec les champs principaux
        individual = make_individual(
            [
                "0 @I1@ INDI\n",
                "1 NAME John /Doe/\n",
                "1 SEX M\n",
                "1 NICK Johnny\n",
                "1 NMR 2\n",
                "1 BIRT\n",
                "2 DATE 1800\n",
                "2 PLAC Lyon\n",
                "1 DEAT\n",
                "2 DATE 1900\n",
                "2 PLAC Paris\n",
                "2 AGE 40\n",
                "1 CHR\n",
                "2 DATE 1801\n",
                "2 PLAC Nice\n",
                "1 FAMC @F1@\n",
                "2 NOTE child\n",
            ]
        )
        # When on lit les champs
        # Then chaque champ est renseigné
        self.assertEqual(individual.name, "John /Doe/")
        self.assertEqual(individual.sex, "M")
        self.assertEqual(individual.nickname, "Johnny")
        self.assertEqual(individual.marriage_count, 2)
        self.assertEqual(individual.birth_date, "1800")
        self.assertEqual(individual.birth_place, "Lyon")
        self.assertEqual(individual.death_date, "1900")
        self.assertEqual(individual.death_place, "Paris")
        self.assertEqual(individual.age_at_death, "40")
        self.assertEqual(individual.baptism_date, "1801")
        self.assertEqual(individual.baptism_place, "Nice")
        self.assertEqual(individual.famc, "@F1@")
        self.assertEqual(individual.famc_links[0]["details"], [("NOTE", "child")])

    # Vérifie death year confirms death.
    def test_death_year_confirms_death(self):
        # Given un individu avec DEAT Y
        individual = make_individual(["0 @I1@ INDI\n", "1 DEAT\n", "2 Y\n"])
        # When on lit le décès
        # Then le décès est confirmé
        self.assertTrue(individual.death_confirmed)

    # Vérifie invalid marriage count is ignored.
    def test_invalid_marriage_count_is_ignored(self):
        # Given un individu avec un NMR non numérique
        individual = make_individual(["0 @I1@ INDI\n", "1 NMR abc\n"])
        # When on lit le nombre de mariages
        # Then la valeur reste absente
        self.assertIsNone(individual.marriage_count)

    # Vérifie name continuation is appended.
    def test_name_continuation_is_appended(self):
        # Given un individu avec un NAME suivi d'un CONT
        individual = make_individual(
            ["0 @I1@ INDI\n", "1 NAME John\n", "2 CONT /Doe/\n"]
        )
        # When on lit le nom
        # Then la continuation est ajoutée avec un retour à la ligne
        self.assertEqual(individual.name, "John\n/Doe/")

    # Vérifie notes collect only top level notes.
    def test_notes_collect_only_top_level_notes(self):
        # Given un individu avec une note de niveau 1 et une note d'événement
        individual = make_individual(
            [
                "0 @I1@ INDI\n",
                "1 NOTE top\n",
                "1 BIRT\n",
                "2 NOTE birth\n",
                "2 DATE 1900\n",
            ]
        )
        # When on lit les notes
        # Then seule la note de niveau 1 est collectée
        self.assertEqual(individual.notes, ["top"])

    # Vérifie note continuation is appended.
    def test_note_continuation_is_appended(self):
        # Given un individu avec une note suivie d'un CONT puis d'un autre tag
        individual = make_individual(
            [
                "0 @I1@ INDI\n",
                "1 NOTE first\n",
                "2 CONT second\n",
                "2 SOUR @S1@\n",
            ]
        )
        # When on lit les notes
        # Then la continuation est fusionnée et la collecte s'arrête
        self.assertEqual(individual.notes, ["first\nsecond"])

    # Vérifie note loading skips malformed line.
    def test_note_loading_skips_malformed_line(self):
        # Given un individu contenant une ligne malformée
        individual = make_individual(
            ["0 @I1@ INDI\n", "PAS UN NIVEAU\n", "1 NOTE top\n"]
        )
        # When on lit les notes
        # Then la ligne malformée est ignorée
        self.assertEqual(individual.notes, ["top"])

    # Vérifie notes ignore event notes.
    def test_notes_ignore_event_notes(self):
        # Given un individu avec des notes sous BAPM et FACT
        individual = make_individual(
            [
                "0 @I1@ INDI\n",
                "1 BAPM\n",
                "2 NOTE Baptism note\n",
                "3 CONT continued\n",
                "1 FACT\n",
                "2 NOTE Fact note\n",
            ]
        )
        # When on lit les notes
        # Then les notes d'événement restent dans les événements
        self.assertEqual(individual.notes, [])

    # Vérifie multiple names are preserved.
    def test_multiple_names_are_preserved(self):
        # Given un individu avec plusieurs noms
        individual = make_individual(
            [
                "0 @I1@ INDI\n",
                "1 NAME John /Doe/\n",
                "1 NAME Johnny /Doe/\n",
            ]
        )
        # When on lit les noms
        names = individual.names
        name = individual.name
        # Then tous les noms sont conservés et le préféré est le premier
        self.assertEqual(names, ["John /Doe/", "Johnny /Doe/"])
        self.assertEqual(name, "John /Doe/")

    # Vérifie obje collects inline file references.
    def test_obje_collects_inline_file_references(self):
        # Given un individu avec un OBJE inline
        individual = make_individual(
            ["0 @I1@ INDI\n", "1 OBJE\n", "2 FILE photo.jpg\n"]
        )
        # When on lit les objets
        obje = individual.obje
        # Then le fichier inline est exposé
        self.assertEqual(obje, ["photo.jpg"])


if __name__ == "__main__":
    unittest.main()
