"""Tests du modèle de dépôt : nom, adresse, contacts et références."""

import os
import tempfile
import unittest

from gedcom.models.repository import Repository
from gedcom.parser import GedcomParser

HEAD = (
    "0 HEAD\n1 SOUR T\n1 GEDC\n2 VERS 5.5.1\n2 FORM LINEAGE-LINKED\n"
    "1 CHAR UTF-8\n1 SUBM @U1@\n0 @U1@ SUBM\n1 NAME A\n0 TRLR\n"
)


def build_repository(record_block):
    """Charge un GEDCOM et retourne l'objet Repository de l'enregistrement @R1@."""
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".ged", delete=False
    ) as handle:
        handle.write(HEAD.replace("0 TRLR\n", "") + record_block + "0 TRLR\n")
        path = handle.name
    try:
        parser = GedcomParser()
        parser.load(path)
        return Repository(parser.get_entity("@R1@"))
    finally:
        os.unlink(path)


class TestRepository(unittest.TestCase):
    """Vérifie le nom, l'adresse, les contacts et les références d'un dépôt."""

    # Vérifie name with conc continuation.
    def test_name_with_conc_continuation(self):
        # Given (Arrange) un dépôt dont le nom est continué par CONC
        repo = build_repository("0 @R1@ REPO\n1 NAME City\n2 CONC Archives\n")
        # When (Act) on lit le nom
        name = repo.name
        # Then (Assert) le nom concatène la continuation
        self.assertEqual(name, "CityArchives")

    # Vérifie address subfields.
    def test_address_subfields(self):
        # Given (Arrange) un dépôt avec une adresse détaillée
        repo = build_repository(
            "0 @R1@ REPO\n1 NAME A\n1 ADDR 1 rue X\n"
            "2 CITY Paris\n2 ADR1 line1\n2 ADR2 line2\n2 STAE IDF\n"
            "2 POST 75000\n2 CTRY France\n"
        )
        # When (Act) on lit les composants d'adresse
        components = (
            repo.city,
            repo.address_line_1,
            repo.address_line_2,
            repo.state,
            repo.postal_code,
            repo.country,
        )
        # Then (Assert) chaque composant est renseigné
        self.assertEqual(
            components, ("Paris", "line1", "line2", "IDF", "75000", "France")
        )

    # Vérifie name and address keep continuations.
    def test_name_and_address_keep_continuations(self):
        # Given (Arrange) un dépôt avec un nom et une adresse continués
        repo = build_repository(
            "0 @R1@ REPO\n1 NAME City\n2 CONT Archives\n"
            "1 ADDR 1 rue\n2 CONT X\n2 CITY Paris\n"
        )
        # When (Act) on lit le nom et l'adresse
        name = repo.name
        address = repo.address
        # Then (Assert) les continuations sont fusionnées
        self.assertEqual(name, "City\nArchives")
        self.assertEqual(address, "1 rue\nX")

    # Vérifie contacts.
    def test_contacts(self):
        # Given (Arrange) un dépôt avec téléphone, email, fax et site
        repo = build_repository(
            "0 @R1@ REPO\n1 NAME A\n1 PHON 0102\n1 EMAIL a@b.c\n"
            "1 FAX 0304\n1 WWW http://x.org\n"
        )
        # When (Act) on lit les contacts
        contacts = (repo.phone, repo.email, repo.fax, repo.website)
        # Then (Assert) chaque contact est renseigné
        self.assertEqual(contacts, ("0102", "a@b.c", "0304", "http://x.org"))

    # Vérifie references and record id.
    def test_references_and_record_id(self):
        # Given (Arrange) un dépôt avec REFN et RIN
        repo = build_repository("0 @R1@ REPO\n1 NAME A\n1 REFN RefR\n1 RIN RINR\n")
        # When (Act) on lit références et identifiant
        references = repo.references
        record_id = repo.record_id
        # Then (Assert) les deux sont renseignés
        self.assertEqual(references, ["RefR"])
        self.assertEqual(record_id, "RINR")

    # Vérifie change date and time.
    def test_change_date_and_time(self):
        # Given (Arrange) un dépôt avec CHAN/DATE/TIME
        repo = build_repository(
            "0 @R1@ REPO\n1 NAME A\n1 CHAN\n2 DATE 2 FEB 2021\n2 TIME 08:30\n"
        )
        # When (Act) on lit la date et l'heure de modification
        date = repo.change_date
        time = repo.change_time
        # Then (Assert) les deux sont renseignés
        self.assertEqual(date, "2 FEB 2021")
        self.assertEqual(time, "08:30")

    # Vérifie note with cont continuation.
    def test_note_with_cont_continuation(self):
        # Given (Arrange) un dépôt avec une note continuée par CONT
        repo = build_repository("0 @R1@ REPO\n1 NAME A\n1 NOTE first\n2 CONT second\n")
        # When (Act) on lit les notes
        notes = repo.notes
        # Then (Assert) la note intègre la continuation
        self.assertEqual(notes, ["first\nsecond"])

    # Vérifie additional fields with details.
    def test_additional_fields_with_details(self):
        # Given (Arrange) un dépôt avec un champ additionnel et un détail
        repo = build_repository(
            "0 @R1@ REPO\n1 NAME A\n1 EXTRA custom\n2 CHILD detail\n"
        )
        # When (Act) on lit les champs additionnels
        fields = repo.additional_fields
        # Then (Assert) le champ et son détail sont collectés
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["tag"], "EXTRA")
        self.assertEqual(fields[0]["details"], [("CHILD", "detail")])


if __name__ == "__main__":
    unittest.main()
