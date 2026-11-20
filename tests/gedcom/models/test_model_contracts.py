"""Contrats transverses des modèles : paresse, mutabilité et arbres d'événements."""

import unittest

from gedcom.models.entity import GedcomEntity
from gedcom.models.event import Event
from gedcom.models.family import Family
from gedcom.models.individual import Individual
from gedcom.models.multimedia import MultimediaObject
from gedcom.models.note import Note
from gedcom.models.repository import Repository
from gedcom.models.source import Source
from gedcom.models.submitter import Submitter
from gedcom.parser import GedcomParser


class TestModelContracts(unittest.TestCase):
    """Contrats transverses des modèles : paresse, mutabilité et arbres d'événements."""

    # Vérifie individual text falls back when entity has no parser helper.
    def test_individual_text_falls_back_when_entity_has_no_parser_helper(self):
        class DummyEntity:
            pointer = "@I99@"

            @staticmethod
            def parsed_lines():
                return [
                    (1, None, "TEXT", "This is the first line"),
                    (2, None, "CONT", "continued on next line"),
                    (2, None, "CONC", " and still same paragraph"),
                ]

        individual = Individual(DummyEntity())

        self.assertEqual(
            individual.texts,
            ["This is the first line\ncontinued on next line and still same paragraph"],
        )

    # Vérifie individual text tags are loaded lazily.
    def test_individual_text_tags_are_loaded_lazily(self):
        individual = Individual(
            GedcomEntity(
                "@I101@",
                "INDI",
                0,
                [
                    "0 @I101@ INDI",
                    "1 TEXT First line",
                    "2 CONT second line",
                    "2 CONC , continued",
                ],
            )
        )

        self.assertFalse(individual._text_tags_loaded)
        self.assertIsNone(individual._texts)
        self.assertEqual(individual.texts, ["First line\nsecond line, continued"])
        self.assertTrue(individual._text_tags_loaded)

    # Vérifie individual occupations and properties are loaded lazily.
    def test_individual_occupations_and_properties_are_loaded_lazily(self):
        individual = Individual(
            GedcomEntity(
                "@I102@",
                "INDI",
                0,
                [
                    "0 @I102@ INDI",
                    "1 OCCU Baker",
                    "2 DATE 1900",
                    "1 OCCU Teacher",
                    "2 DATE 1910",
                    "1 PROP Nationality",
                ],
            )
        )

        self.assertFalse(individual._occupations_loaded)
        self.assertFalse(individual._properties_loaded)
        self.assertIsNone(individual._occupations)
        self.assertIsNone(individual._properties)
        self.assertEqual(
            individual.occupations,
            [
                {"occupation": "Baker", "date": "1900"},
                {"occupation": "Teacher", "date": "1910"},
            ],
        )
        self.assertEqual(individual.properties, ["Nationality"])

    # Vérifie individual notes are loaded lazily.
    def test_individual_notes_are_loaded_lazily(self):
        individual = Individual(
            GedcomEntity(
                "@I103@",
                "INDI",
                0,
                [
                    "0 @I103@ INDI",
                    "1 NOTE General note",
                    "2 CONT Continued note",
                    "2 CONC !",
                    "1 BIRT",
                    "2 NOTE Birth note",
                    "3 CONC !",
                    "1 DEAT",
                    "2 NOTE Death note",
                    "3 NOTE Additional death note",
                    "4 CONC ?",
                ],
            )
        )

        self.assertFalse(individual._notes_loaded)
        self.assertIsNone(individual._notes)
        self.assertEqual(
            individual.notes,
            ["General note\nContinued note!"],
        )
        self.assertTrue(individual._notes_loaded)

    # Vérifie individual family and object references are loaded lazily.
    def test_individual_family_and_object_references_are_loaded_lazily(self):
        individual = Individual(
            GedcomEntity(
                "@I104@",
                "INDI",
                0,
                [
                    "0 @I104@ INDI",
                    "1 FAMC @F0@",
                    "2 PEDI adopted",
                    "1 FAMC @F3@",
                    "2 PEDI birth",
                    "1 FAMS @F1@",
                    "1 FAMS @F2@",
                    "1 OBJE @O1@",
                    "1 OBJE *",
                    "1 OBJE @O2@",
                ],
            )
        )

        self.assertFalse(individual._fams_loaded)
        self.assertFalse(individual._obje_loaded)
        self.assertIsNone(individual._fams)
        self.assertIsNone(individual._obje)
        self.assertEqual(
            individual.famc_links,
            [
                {"pointer": "@F0@", "details": [("PEDI", "adopted")]},
                {"pointer": "@F3@", "details": [("PEDI", "birth")]},
            ],
        )
        self.assertEqual(individual.fams, ["@F1@", "@F2@"])
        self.assertTrue(individual._fams_loaded)
        self.assertFalse(individual._obje_loaded)
        self.assertEqual(individual.obje, ["@O1@", "@O2@"])
        self.assertTrue(individual._obje_loaded)

    # Vérifie empty individual lists are lazy and mutable.
    def test_empty_individual_lists_are_lazy_and_mutable(self):
        class DummyEntity:
            pointer = "@I100@"

            @staticmethod
            def parsed_lines():
                return [
                    (0, "@I100@", "INDI", ""),
                    (1, None, "NAME", "Jane /Doe/"),
                ]

        individual = Individual(DummyEntity())

        self.assertIsNone(individual._notes)
        notes = individual.notes
        self.assertEqual(notes, [])
        self.assertIs(individual.notes, notes)
        notes.append("Research note")
        self.assertEqual(individual.notes, ["Research note"])

    # Vérifie empty note lists are lazy and mutable.
    def test_empty_note_lists_are_lazy_and_mutable(self):
        note = Note(
            GedcomEntity(
                "@N20@",
                "NOTE",
                0,
                ["0 @N20@ NOTE Archival note text"],
            )
        )

        self.assertFalse(hasattr(note, "__dict__"))
        self.assertIsNone(note._sources)
        sources = note.sources
        self.assertEqual(sources, [])
        self.assertIs(note.sources, sources)
        sources.append("@S1@")
        self.assertEqual(note.sources, ["@S1@"])

    # Vérifie source keeps notes separately from text.
    def test_source_keeps_notes_separately_from_text(self):
        parser = GedcomParser()
        parser.lines = [
            "0 @S10@ SOUR",
            "1 TITL Source de test",
            "1 NOTE Première ligne",
            "2 CONT seconde ligne",
            "2 CONC , suite",
        ]
        parser._parse_entities()

        source = Source(parser.get_entity("@S10@"))

        self.assertIsNone(source.text)
        self.assertEqual(source.notes, ["Première ligne\nseconde ligne, suite"])

    # Vérifie source data events are loaded lazily.
    def test_source_data_events_are_loaded_lazily(self):
        source = Source(
            GedcomEntity(
                "@S11@",
                "SOUR",
                0,
                [
                    "0 @S11@ SOUR",
                    "1 DATA",
                    "2 EVEN Census",
                    "3 DATE 1900",
                    "3 PLAC Example place",
                    "2 AGNC Registry",
                ],
            )
        )

        self.assertFalse(source._data_events_loaded)
        self.assertIsNone(source._data_events)
        self.assertEqual(source.agency, "Registry")
        self.assertEqual(source.text, None)

        self.assertEqual(
            source.data_events,
            [
                {
                    "value": "Census",
                    "details": [
                        ("DATE", "1900"),
                        ("PLAC", "Example place"),
                    ],
                }
            ],
        )
        self.assertTrue(source._data_events_loaded)

    # Vérifie empty repository lists are lazy and mutable.
    def test_empty_repository_lists_are_lazy_and_mutable(self):
        repository = Repository(
            GedcomEntity(
                "@R20@",
                "REPO",
                0,
                ["0 @R20@ REPO", "1 NAME City archive"],
            )
        )

        self.assertFalse(hasattr(repository, "__dict__"))
        self.assertIsNone(repository._references)
        references = repository.references
        self.assertEqual(references, [])
        self.assertIs(repository.references, references)
        references.append("@S1@")
        self.assertEqual(repository.references, ["@S1@"])

    # Vérifie empty submitter lists are lazy and mutable.
    def test_empty_submitter_lists_are_lazy_and_mutable(self):
        submitter = Submitter(
            GedcomEntity(
                "@M20@",
                "SUBM",
                0,
                ["0 @M20@ SUBM", "1 NAME Archive office"],
            )
        )

        self.assertFalse(hasattr(submitter, "__dict__"))
        self.assertIsNone(submitter._phones)
        phones = submitter.phones
        self.assertEqual(phones, [])
        self.assertIs(submitter.phones, phones)
        phones.append("555-0100")
        self.assertEqual(submitter.phones, ["555-0100"])

    # Vérifie multimedia object uses slots and preserves fields.
    def test_multimedia_object_uses_slots_and_preserves_fields(self):
        multimedia = MultimediaObject(
            GedcomEntity(
                "@O20@",
                "OBJE",
                0,
                [
                    "0 @O20@ OBJE",
                    "1 FILE family-photo.jpg",
                    "2 FORM jpeg",
                    "1 TITL Family photo",
                    "1 FORM jpeg",
                    "1 FILE portrait.png",
                    "2 FORM png",
                    "2 TITL Portrait file",
                    "2 TYPE portrait",
                    "1 NOTE Scanned copy",
                    "2 CONT retouched",
                    "1 _CUSTOM Custom value",
                    "2 TYPE Extension detail",
                ],
            )
        )

        self.assertFalse(hasattr(multimedia, "__dict__"))
        self.assertEqual(multimedia.pointer, "@O20@")
        self.assertEqual(multimedia.file, "portrait.png")
        self.assertEqual(multimedia.files, ["family-photo.jpg", "portrait.png"])
        self.assertEqual(multimedia.file_records[1]["title"], "Portrait file")
        self.assertEqual(multimedia.title, "Family photo")
        self.assertEqual(multimedia.format, "png")
        self.assertEqual(multimedia.note, "Scanned copy\nretouched")
        self.assertEqual(
            multimedia.additional_fields,
            [
                {
                    "tag": "_CUSTOM",
                    "value": "Custom value",
                    "details": [("TYPE", "Extension detail")],
                }
            ],
        )

    # Vérifie multimedia object ignores malformed lines.
    def test_multimedia_object_ignores_malformed_lines(self):
        # Given un objet multimédia contenant une ligne malformée
        multimedia = MultimediaObject(
            GedcomEntity(
                "@O21@",
                "OBJE",
                0,
                ["0 @O21@ OBJE", "malformed line", "1 FILE photo.jpg"],
            )
        )

        # When on lit le fichier
        # Then la ligne malformée est ignorée
        self.assertEqual(multimedia.file, "photo.jpg")

    # Vérifie multimedia title continuations are appended.
    def test_multimedia_title_continuations_are_appended(self):
        # Given un objet multimédia avec CONT/CONC sous TITL
        multimedia = MultimediaObject(
            GedcomEntity(
                "@O23@",
                "OBJE",
                0,
                [
                    "0 @O23@ OBJE",
                    "1 TITL Family",
                    "2 CONT photo",
                    "2 CONC 2020",
                ],
            )
        )

        # When on lit le titre
        # Then les continuations sont fusionnées
        self.assertEqual(multimedia.title, "Family\nphoto2020")
        self.assertEqual(multimedia.titles, ["Family\nphoto2020"])

    # Vérifie family events use event model.
    def test_family_events_use_event_model(self):
        parser = GedcomParser()
        parser.lines = [
            "0 @F10@ FAM",
            "1 MARR",
            "2 DATE 1 JAN 1900",
            "1 DIV",
            "2 DATE 1 JAN 1910",
            "1 EVEN Reunion familiale",
            "2 TYPE Reunion",
        ]
        parser._parse_entities()

        family = Family(parser.get_entity("@F10@"))

        self.assertFalse(family._event_models_loaded)
        self.assertIsNone(family._marriages)
        self.assertIsNone(family._divorces)
        self.assertIsNone(family._events)
        self.assertIsInstance(family.marriages[0], Event)
        self.assertTrue(family._event_models_loaded)
        self.assertEqual(family.marriages[0].get("details"), [("DATE", "1 JAN 1900")])
        self.assertIsInstance(family.divorces[0], Event)
        self.assertIsInstance(family.events[0], Event)
        self.assertEqual(family.events[0].value, "Reunion familiale")

    # Vérifie individual builds nested event tree.
    def test_individual_builds_nested_event_tree(self):
        individual = Individual(
            GedcomEntity(
                "@I22@",
                "INDI",
                0,
                [
                    "0 @I22@ INDI",
                    "1 NAME John /Doe/",
                    "1 SEX M",
                    "1 FAMC @F1@",
                    "1 BAPM",
                    "2 DATE 22 JUN 1963",
                    "2 PLAC Paris",
                    "3 MAP",
                    "4 LATI N48.85",
                    "1 FACT Premiers pas",
                    "2 TYPE Croissance",
                ],
            )
        )

        self.assertIsNone(individual._events)
        tags = [event["tag"] for event in individual.events]
        self.assertIs(individual.events, individual._events)
        self.assertEqual(tags, ["BAPM", "FACT"])

        # Les tags avec un affichage dédié (SEX, FAMC, FAMS, OBJE, NOTE,
        # NAME, OCCU, PROP, TEXT) ne doivent pas apparaître dans l'arbre générique.
        self.assertNotIn("SEX", tags)
        self.assertNotIn("FAMC", tags)
        self.assertNotIn("NAME", tags)

        bapm_event = individual.events[0]
        date_node, plac_node = bapm_event["children"]
        self.assertEqual(
            (date_node["tag"], date_node["value"]), ("DATE", "22 JUN 1963")
        )
        self.assertEqual((plac_node["tag"], plac_node["value"]), ("PLAC", "Paris"))
        map_node = plac_node["children"][0]
        self.assertEqual(map_node["tag"], "MAP")
        self.assertEqual(map_node["children"][0]["tag"], "LATI")
        self.assertEqual(map_node["children"][0]["value"], "N48.85")

        fact_event = individual.events[1]
        self.assertEqual(fact_event["value"], "Premiers pas")
        self.assertEqual(
            fact_event["children"],
            [{"tag": "TYPE", "value": "Croissance", "children": []}],
        )


if __name__ == "__main__":
    unittest.main()
