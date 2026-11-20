"""Tests du modèle de famille : membres, événements, notes et champs additionnels."""

import unittest

from gedcom.models.entity import GedcomEntity
from gedcom.models.family import Family

FAMILY_LINES = ["0 @F1@ FAM", "1 HUSB @I1@", "1 WIFE @I2@"]


def build_family(extra_lines):
    """Construit une famille dont les lignes suivent l'en-tête @F1@ FAM."""
    return Family(GedcomEntity("@F1@", "FAM", 0, FAMILY_LINES + extra_lines))


class TestFamily(unittest.TestCase):
    """Vérifie les membres, les événements et les champs additionnels d'une famille."""

    # Vérifie children are collected.
    def test_children_are_collected(self):
        # Given (Arrange) une famille avec deux enfants
        family = build_family(["1 CHIL @I3@", "1 CHIL @I4@"])
        # When (Act) on lit les enfants
        children = family.children
        # Then (Assert) les deux enfants sont collectés
        self.assertEqual(children, ["@I3@", "@I4@"])

    # Vérifie number of children converts to int.
    def test_number_of_children_converts_to_int(self):
        # Given (Arrange) une famille avec un nombre d'enfants numérique
        family = build_family(["1 NCHI 3"])
        # When (Act) on lit le nombre d'enfants
        count = family.number_of_children
        # Then (Assert) la valeur est convertie en entier
        self.assertEqual(count, 3)

    # Vérifie number of children keeps text when not numeric.
    def test_number_of_children_keeps_text_when_not_numeric(self):
        # Given (Arrange) une famille avec un nombre d'enfants non numérique
        family = build_family(["1 NCHI unknown"])
        # When (Act) on lit le nombre d'enfants
        count = family.number_of_children
        # Then (Assert) la valeur texte est conservée
        self.assertEqual(count, "unknown")

    # Vérifie engagement and marriage fields map to attributes.
    def test_engagement_and_marriage_fields_map_to_attributes(self):
        # Given (Arrange) une famille avec engagement, bans, contrat, licence et règlement
        family = build_family(
            [
                "1 ENGA Engagement",
                "1 MARB Bans",
                "1 MARC Contract",
                "1 MARL License",
                "1 MARS Settlement",
            ]
        )
        # When (Act) on lit les attributs correspondants
        values = (
            family.engagement,
            family.marriage_banns,
            family.marriage_contract,
            family.marriage_license,
            family.marriage_settlement,
        )
        # Then (Assert) chaque attribut est renseigné
        self.assertEqual(
            values, ("Engagement", "Bans", "Contract", "License", "Settlement")
        )

    # Vérifie divorce final and annulment map to attributes.
    def test_divorce_final_and_annulment_map_to_attributes(self):
        # Given (Arrange) une famille avec divorce final et annulation
        family = build_family(["1 DIVF Final", "1 ANUL Annulment"])
        # When (Act) on lit les attributs correspondants
        values = (family.divorce_final, family.annulment)
        # Then (Assert) chaque attribut est renseigné
        self.assertEqual(values, ("Final", "Annulment"))

    # Vérifie marriage date and place.
    def test_marriage_date_and_place(self):
        # Given (Arrange) une famille avec une date et un lieu de mariage
        family = build_family(["1 MARR", "2 DATE 2 FEB 2001", "2 PLAC Paris"])
        # When (Act) on lit la date et le lieu du mariage
        date = family.marriage_date
        place = family.marriage_place
        # Then (Assert) les deux champs sont renseignés
        self.assertEqual(date, "2 FEB 2001")
        self.assertEqual(place, "Paris")

    # Vérifie divorce date and place.
    def test_divorce_date_and_place(self):
        # Given (Arrange) une famille avec une date et un lieu de divorce
        family = build_family(["1 DIV", "2 DATE 2 FEB 2002", "2 PLAC Lyon"])
        # When (Act) on lit la date et le lieu du divorce
        date = family.divorce_date
        place = family.divorce_place
        # Then (Assert) les deux champs sont renseignés
        self.assertEqual(date, "2 FEB 2002")
        self.assertEqual(place, "Lyon")

    # Vérifie notes are collected with continuation.
    def test_notes_are_collected_with_continuation(self):
        # Given (Arrange) une famille avec une note continuée par CONT
        family = build_family(["1 NOTE first", "2 CONT second"])
        # When (Act) on lit les notes
        notes = family.notes
        # Then (Assert) la note intègre la continuation
        self.assertEqual(notes, ["first\nsecond"])

    # Vérifie sources are collected.
    def test_sources_are_collected(self):
        # Given (Arrange) une famille avec une source
        family = build_family(["1 SOUR @S1@"])
        # When (Act) on lit les sources
        sources = family.sources
        # Then (Assert) la source est collectée
        self.assertEqual(sources, ["@S1@"])

    # Vérifie additional fields collect details.
    def test_additional_fields_collect_details(self):
        # Given (Arrange) une famille avec un champ additionnel et deux niveaux de détails
        family = build_family(["1 EXTRA custom", "2 CHILD detail", "3 DEEP detail"])
        # When (Act) on lit les champs additionnels
        fields = family.additional_fields
        # Then (Assert) le champ et ses détails sont collectés
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["tag"], "EXTRA")
        self.assertEqual(
            fields[0]["details"], [("CHILD", "detail"), ("DEEP", "detail")]
        )

    # Vérifie marriages are loaded lazily.
    def test_marriages_are_loaded_lazily(self):
        # Given (Arrange) une famille avec un mariage et un détail
        family = build_family(["1 MARR", "2 DATE 2 FEB 2001"])
        # When (Act) on lit les mariages
        marriages = family.marriages
        # Then (Assert) le mariage et son détail sont exposés
        self.assertEqual(len(marriages), 1)
        self.assertEqual(marriages[0].tag, "MARR")
        self.assertEqual(marriages[0].details, [("DATE", "2 FEB 2001")])

    # Vérifie divorces are loaded lazily.
    def test_divorces_are_loaded_lazily(self):
        # Given (Arrange) une famille avec un divorce
        family = build_family(["1 DIV"])
        # When (Act) on lit les divorces
        divorces = family.divorces
        # Then (Assert) le divorce est exposé
        self.assertEqual(len(divorces), 1)
        self.assertEqual(divorces[0].tag, "DIV")

    # Vérifie events are loaded lazily.
    def test_events_are_loaded_lazily(self):
        # Given (Arrange) une famille avec un événement générique
        family = build_family(["1 EVEN Custom", "2 TYPE Note"])
        # When (Act) on lit les événements
        events = family.events
        # Then (Assert) l'événement et son détail sont exposés
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].value, "Custom")
        self.assertEqual(events[0].details, [("TYPE", "Note")])

    # Vérifie marriages setter none then get returns empty.
    def test_marriages_setter_none_then_get_returns_empty(self):
        # Given (Arrange) une famille sans mariage
        family = build_family([])
        family.marriages = None
        # When (Act) on relit les mariages
        marriages = family.marriages
        # Then (Assert) la liste vide est retournée
        self.assertEqual(marriages, [])

    # Vérifie divorces setter round trip.
    def test_divorces_setter_round_trip(self):
        # Given (Arrange) une famille sans divorce
        family = build_family([])
        # When (Act) on affecte un divorce
        family.divorces = ["custom"]
        # Then (Assert) la valeur affectée est relue
        self.assertEqual(family.divorces, ["custom"])

    # Vérifie events setter none then get returns empty.
    def test_events_setter_none_then_get_returns_empty(self):
        # Given (Arrange) une famille sans événement
        family = build_family([])
        family.events = None
        # When (Act) on relit les événements
        events = family.events
        # Then (Assert) la liste vide est retournée
        self.assertEqual(events, [])

    # Vérifie malformed line is ignored.
    def test_malformed_line_is_ignored(self):
        # Given (Arrange) une famille contenant une ligne malformée
        family = build_family(["invalid line"])
        # When (Act) on lit les événements
        events = family.events
        # Then (Assert) la ligne malformée est ignorée sans lever d'exception
        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
