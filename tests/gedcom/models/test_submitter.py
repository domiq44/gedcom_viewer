"""Tests du modèle de soumetteur GEDCOM."""

import unittest

from gedcom.models.entity import GedcomEntity
from gedcom.models.submitter import Submitter


class TestSubmitter(unittest.TestCase):
    """Vérifie l'analyse des coordonnées et des champs additionnels."""

    def _submitter(self):
        """Construit un soumetteur couvrant les champs principaux."""
        entity = GedcomEntity(
            "@M1@",
            "SUBM",
            0,
            [
                "0 @M1@ SUBM",
                "1 NAME John /Doe/",
                "1 ADDR 1 rue de Paris",
                "2 ADR1 Line 1",
                "2 CITY Paris",
                "2 POST 75001",
                "2 CTRY France",
                "1 PHON 0102030405",
                "1 EMAIL john@example.com",
                "1 FAX 0102030406",
                "1 WWW https://example.com",
                "1 LANG fr",
                "1 RFN 123",
                "1 RIN 456",
                "1 RESN privacy",
                "1 CHAN",
                "2 DATE 1 JAN 2020",
                "2 TIME 12:00",
                "1 NOTE Research contact",
            ],
        )
        return Submitter(entity)

    # Vérifie parses identity and address.
    def test_parses_identity_and_address(self):
        # Given un soumetteur complet
        submitter = self._submitter()

        # When on lit son identité et son adresse
        # Then les champs principaux sont renseignés
        self.assertEqual(submitter.name, "John /Doe/")
        self.assertEqual(submitter.address, "1 rue de Paris")
        self.assertEqual(submitter.address_line_1, "Line 1")
        self.assertEqual(submitter.city, "Paris")
        self.assertEqual(submitter.postal_code, "75001")
        self.assertEqual(submitter.country, "France")

    # Vérifie name and address keep continuations.
    def test_name_and_address_keep_continuations(self):
        # Given un soumetteur avec un nom et une adresse continués
        entity = GedcomEntity(
            "@M1@",
            "SUBM",
            0,
            [
                "0 @M1@ SUBM",
                "1 NAME John",
                "2 CONT Doe",
                "1 ADDR 1 rue",
                "2 CONT de Paris",
                "2 CITY Paris",
            ],
        )
        submitter = Submitter(entity)

        # When on lit son nom et son adresse
        name = submitter.name
        address = submitter.address

        # Then les continuations sont fusionnées sans polluer les sous-champs
        self.assertEqual(name, "John\nDoe")
        self.assertEqual(address, "1 rue\nde Paris")
        self.assertEqual(submitter.city, "Paris")

    # Vérifie parses contacts and references.
    def test_parses_contacts_and_references(self):
        # Given un soumetteur complet
        submitter = self._submitter()

        # When on lit ses coordonnées et références
        # Then chaque valeur est conservée dans son champ et sa liste
        self.assertEqual(submitter.phone, "0102030405")
        self.assertEqual(submitter.phones, ["0102030405"])
        self.assertEqual(submitter.email, "john@example.com")
        self.assertEqual(submitter.emails, ["john@example.com"])
        self.assertEqual(submitter.fax, "0102030406")
        self.assertEqual(submitter.website, "https://example.com")
        self.assertEqual(submitter.language, "fr")
        self.assertEqual(submitter.languages, ["fr"])
        self.assertEqual(submitter.registered_number, "123")
        self.assertEqual(submitter.record_id, "456")
        self.assertEqual(submitter.restriction, "privacy")

    # Vérifie parses change date and additional fields.
    def test_parses_change_date_and_additional_fields(self):
        # Given un soumetteur complet
        submitter = self._submitter()

        # When on lit la date de modification et les champs additionnels
        # Then la date est retenue et la note devient un champ additionnel
        self.assertEqual(submitter.change_date, "1 JAN 2020")
        self.assertEqual(submitter.change_time, "12:00")
        tags = {field["tag"]: field["value"] for field in submitter.additional_fields}
        self.assertEqual(tags["NOTE"], "Research contact")

    # Vérifie ignores malformed line.
    def test_ignores_malformed_line(self):
        # Given un soumetteur contenant une ligne malformée
        entity = GedcomEntity(
            "@M1@",
            "SUBM",
            0,
            ["0 @M1@ SUBM", "invalid", "1 NAME John /Doe/"],
        )

        # When on construit le soumetteur
        submitter = Submitter(entity)

        # Then le nom reste analysé
        self.assertEqual(submitter.name, "John /Doe/")

    # Vérifie parses name continuation.
    def test_parses_name_continuation(self):
        # Given un nom suivi d'une continuation CONT
        entity = GedcomEntity(
            "@M1@",
            "SUBM",
            0,
            ["0 @M1@ SUBM", "1 NAME John", "2 CONT /Doe/"],
        )

        # When on construit le soumetteur
        submitter = Submitter(entity)

        # Then la continuation est concaténée au nom
        self.assertEqual(submitter.name, "John\n/Doe/")

    # Vérifie parses name subtag as additional field.
    def test_parses_name_subtag_as_additional_field(self):
        # Given un nom avec un sous-tag inconnu
        entity = GedcomEntity(
            "@M1@",
            "SUBM",
            0,
            ["0 @M1@ SUBM", "1 NAME John /Doe/", "2 NICK Johnny"],
        )

        # When on construit le soumetteur
        submitter = Submitter(entity)

        # Then le sous-tag devient un champ additionnel
        tags = {field["tag"]: field["value"] for field in submitter.additional_fields}
        self.assertEqual(tags["NAME/NICK"], "Johnny")

    # Vérifie parses unknown change tag as additional field.
    def test_parses_unknown_change_tag_as_additional_field(self):
        # Given un changement avec un tag inconnu
        entity = GedcomEntity(
            "@M1@",
            "SUBM",
            0,
            ["0 @M1@ SUBM", "1 CHAN", "2 DATE 1 JAN 2020", "2 NOTE changed"],
        )

        # When on construit le soumetteur
        submitter = Submitter(entity)

        # Then le tag inconnu devient un champ additionnel
        tags = {field["tag"]: field["value"] for field in submitter.additional_fields}
        self.assertEqual(tags["CHAN/NOTE"], "changed")

    # Vérifie parses unknown subtag as additional field.
    def test_parses_unknown_subtag_as_additional_field(self):
        # Given un champ spécial avec un sous-tag inconnu
        entity = GedcomEntity(
            "@M1@",
            "SUBM",
            0,
            ["0 @M1@ SUBM", "1 RESN privacy", "2 NOTE restricted"],
        )

        # When on construit le soumetteur
        submitter = Submitter(entity)

        # Then le sous-tag devient un champ additionnel
        tags = {field["tag"]: field["value"] for field in submitter.additional_fields}
        self.assertEqual(tags["RESN/NOTE"], "restricted")

    # Vérifie parses address continuation.
    def test_parses_address_continuation(self):
        # Given une adresse suivie d'une continuation CONT
        entity = GedcomEntity(
            "@M1@",
            "SUBM",
            0,
            ["0 @M1@ SUBM", "1 ADDR 1 rue de Paris", "2 CONT 75001"],
        )

        # When on construit le soumetteur
        submitter = Submitter(entity)

        # Then la continuation est concaténée à l'adresse
        self.assertEqual(submitter.address, "1 rue de Paris\n75001")

    # Vérifie parses unknown address tag as additional field.
    def test_parses_unknown_address_tag_as_additional_field(self):
        # Given une adresse avec un sous-tag inconnu
        entity = GedcomEntity(
            "@M1@",
            "SUBM",
            0,
            ["0 @M1@ SUBM", "1 ADDR 1 rue de Paris", "2 NOTE building B"],
        )

        # When on construit le soumetteur
        submitter = Submitter(entity)

        # Then le sous-tag devient un champ additionnel
        tags = {field["tag"]: field["value"] for field in submitter.additional_fields}
        self.assertEqual(tags["ADDR/NOTE"], "building B")

    # Vérifie parses nested details of additional field.
    def test_parses_nested_details_of_additional_field(self):
        # Given un champ additionnel avec des sous-tags imbriqués
        entity = GedcomEntity(
            "@M1@",
            "SUBM",
            0,
            ["0 @M1@ SUBM", "1 NOTE note", "2 SOUR source", "3 DATA data"],
        )

        # When on construit le soumetteur
        submitter = Submitter(entity)

        # Then les sous-tags sont conservés dans les détails
        note = next(
            field for field in submitter.additional_fields if field["tag"] == "NOTE"
        )
        self.assertEqual(note["details"], [("SOUR", "source"), ("DATA", "data")])


if __name__ == "__main__":
    unittest.main()
