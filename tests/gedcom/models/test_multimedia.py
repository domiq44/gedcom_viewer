"""Tests du modèle objet multimédia : fichiers, formats, titres et détails."""

import os
import tempfile
import unittest

from gedcom.models.multimedia import MultimediaObject
from gedcom.parser import GedcomParser

HEAD = (
    "0 HEAD\n1 SOUR T\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
    "1 CHAR UTF-8\n1 SUBM @U1@\n0 @U1@ SUBM\n1 NAME A\n"
)


def build_object(record_block):
    """Charge un GEDCOM et retourne l'objet multimédia de l'enregistrement @O1@."""
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".ged", delete=False
    ) as handle:
        handle.write(HEAD + record_block + "0 TRLR\n")
        path = handle.name
    try:
        parser = GedcomParser()
        parser.load(path)
        return MultimediaObject(parser.get_entity("@O1@"))
    finally:
        os.unlink(path)


class TestMultimediaObject(unittest.TestCase):
    """Vérifie les fichiers, formats, titres et détails d'un objet multimédia."""

    # Vérifie file form and title are parsed.
    def test_file_form_and_title_are_parsed(self):
        # Given (Arrange) un objet avec FILE, FORM et TITL
        obj = build_object("0 @O1@ OBJE\n1 FILE photo.jpg\n2 FORM jpg\n2 TITL Cover\n")
        # When (Act) on lit les champs principaux
        file = obj.file
        # Then (Assert) le fichier, le titre du fichier et le format sont renseignés
        self.assertEqual(file, "photo.jpg")
        self.assertEqual(obj.file_records[0]["title"], "Cover")
        self.assertEqual(obj.formats, ["jpg"])

    # Vérifie level one title is exposed as title.
    def test_level_one_title_is_exposed_as_title(self):
        # Given (Arrange) un objet avec un TITL de niveau 1
        obj = build_object("0 @O1@ OBJE\n1 TITL Variant title\n")
        # When (Act) on lit le titre
        title = obj.title
        # Then (Assert) le titre et la liste des titres sont renseignés
        self.assertEqual(title, "Variant title")
        self.assertEqual(obj.titles, ["Variant title"])

    # Vérifie file continuation is appended.
    def test_file_continuation_is_appended(self):
        # Given (Arrange) un fichier avec CONT puis CONC
        obj = build_object("0 @O1@ OBJE\n1 FILE photo\n2 CONT .jpg\n2 CONC v2\n")
        # When (Act) on lit le fichier
        file = obj.file
        # Then (Assert) les continuations sont fusionnées
        self.assertEqual(file, "photo\n.jpgv2")

    # Vérifie file details are collected.
    def test_file_details_are_collected(self):
        # Given (Arrange) un fichier avec un tag inconnu
        obj = build_object("0 @O1@ OBJE\n1 FILE photo.jpg\n2 EXTRA detail\n")
        # When (Act) on lit les enregistrements de fichier
        records = obj.file_records
        # Then (Assert) le détail est rattaché au fichier
        self.assertEqual(records[0]["details"], [("EXTRA", "detail")])

    # Vérifie additional fields are collected.
    def test_additional_fields_are_collected(self):
        # Given (Arrange) un objet avec un champ additionnel et un détail
        obj = build_object("0 @O1@ OBJE\n1 EXTRA custom\n2 CHILD detail\n")
        # When (Act) on lit les champs additionnels
        fields = obj.additional_fields
        # Then (Assert) le champ et son détail sont collectés
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["tag"], "EXTRA")
        self.assertEqual(fields[0]["details"], [("CHILD", "detail")])

    # Vérifie notes are collected from level one note.
    def test_notes_are_collected_from_level_one_note(self):
        # Given (Arrange) un objet avec une note
        obj = build_object("0 @O1@ OBJE\n1 NOTE caption\n")
        # When (Act) on lit les notes
        notes = obj.notes
        # Then (Assert) la note est collectée
        self.assertEqual(notes, ["caption"])
        self.assertEqual(obj.note, "caption")

    # Vérifie lazy lists are mutable.
    def test_lazy_lists_are_mutable(self):
        # Given (Arrange) un objet sans fichier
        obj = build_object("0 @O1@ OBJE\n1 NOTE caption\n")
        # When (Act) on ajoute un fichier aux listes paresseuses
        obj.files.append("extra.jpg")
        # Then (Assert) la liste reflète l'ajout
        self.assertEqual(obj.files, ["extra.jpg"])


if __name__ == "__main__":
    unittest.main()
