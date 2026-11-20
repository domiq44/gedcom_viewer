"""Contrat de construction des modèles à partir des lignes déjà parsées."""

import unittest

from gedcom.models.family import Family
from gedcom.models.individual import Individual
from gedcom.models.multimedia import MultimediaObject
from gedcom.models.note import Note
from gedcom.models.repository import Repository
from gedcom.models.source import Source
from gedcom.models.submitter import Submitter


class TestModelsUseParsedLines(unittest.TestCase):
    """Contrat de construction des modèles à partir des lignes déjà parsées."""

    # Vérifie models build from parsed lines only.
    def test_models_build_from_parsed_lines_only(self):
        # Given une entité exposant uniquement parsed_lines
        class ParsedLinesOnlyEntity:
            pointer = "@I1@"

            @staticmethod
            def parsed_lines():
                return [(0, "@I1@", "INDI", "")]

        model_classes = (
            Individual,
            Family,
            Source,
            Note,
            Repository,
            MultimediaObject,
            Submitter,
        )

        # When on construit chaque modèle
        instances = [model(ParsedLinesOnlyEntity()) for model in model_classes]

        # Then aucun modèle n'accède à lines
        self.assertEqual(len(instances), len(model_classes))


if __name__ == "__main__":
    unittest.main()
