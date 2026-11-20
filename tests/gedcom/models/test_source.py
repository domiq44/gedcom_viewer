"""Tests du modèle de source : champs principaux, DATA, REPO et références."""

import unittest

from gedcom.models.entity import GedcomEntity
from gedcom.models.source import Source

SOURCE_LINES = ["0 @S1@ SOUR", "1 TITL Title"]


def build_source(extra_lines):
    """Construit une source dont les lignes suivent l'en-tête @S1@ SOUR."""
    return Source(GedcomEntity("@S1@", "SOUR", 0, SOURCE_LINES + extra_lines))


class TestSource(unittest.TestCase):
    """Vérifie les champs principaux, les événements DATA et les références d'une source."""

    # Vérifie title with conc continuation.
    def test_title_with_conc_continuation(self):
        # Given (Arrange) une source dont le titre est continué par CONT
        source = build_source(["1 TITL first", "2 CONT second"])
        # When (Act) on lit le titre
        title = source.title
        # Then (Assert) le titre intègre la continuation
        self.assertEqual(title, "first\nsecond")

    # Vérifie author under title.
    def test_author_under_title(self):
        # Given (Arrange) une source avec un auteur sous TITL
        source = build_source(["1 TITL Title", "2 AUTH John Doe"])
        # When (Act) on lit l'auteur
        author = source.author
        # Then (Assert) l'auteur est renseigné
        self.assertEqual(author, "John Doe")

    # Vérifie publication date.
    def test_publication_date(self):
        # Given (Arrange) une source avec une date de publication standard
        source = build_source(["1 DATA", "2 DATE 2020"])
        # When (Act) on lit la date de publication
        pub_date = source.pub_date
        # Then (Assert) la date est renseignée
        self.assertEqual(pub_date, "2020")

    # Vérifie publication date falls back to level one date.
    def test_publication_date_falls_back_to_level_one_date(self):
        # Given (Arrange) une source avec une date de publication non standard
        source = build_source(["1 DATE 2020"])
        # When (Act) on lit la date de publication
        pub_date = source.pub_date
        # Then (Assert) la date reste lue en repli
        self.assertEqual(pub_date, "2020")

    # Vérifie text with continuation.
    def test_text_with_continuation(self):
        # Given (Arrange) une source dont le texte standard est continué par CONC
        source = build_source(["1 DATA", "2 TEXT hello", "3 CONC world"])
        # When (Act) on lit le texte
        text = source.text
        # Then (Assert) le texte concatène la continuation
        self.assertEqual(text, "helloworld")

    # Vérifie text falls back to level one text.
    def test_text_falls_back_to_level_one_text(self):
        # Given (Arrange) une source avec un texte non standard
        source = build_source(["1 TEXT hello"])
        # When (Act) on lit le texte
        text = source.text
        # Then (Assert) le texte reste lisible en repli
        self.assertEqual(text, "hello")

    # Vérifie repository pointer.
    def test_repository_pointer(self):
        # Given (Arrange) une source rattachée à un dépôt
        source = build_source(["1 REPO @R1@"])
        # When (Act) on lit le pointeur du dépôt
        repository = source.repository
        # Then (Assert) le pointeur est renseigné
        self.assertEqual(repository, "@R1@")

    # Vérifie publication field.
    def test_publication_field(self):
        # Given (Arrange) une source avec une publication
        source = build_source(["1 PUBL Imprimerie X"])
        # When (Act) on lit la publication
        publication = source.publication
        # Then (Assert) la publication est renseignée
        self.assertEqual(publication, "Imprimerie X")

    # Vérifie abbreviation.
    def test_abbreviation(self):
        # Given (Arrange) une source avec une abréviation
        source = build_source(["1 ABBR SRC"])
        # When (Act) on lit l'abréviation
        abbreviation = source.abbreviation
        # Then (Assert) l'abréviation est renseignée
        self.assertEqual(abbreviation, "SRC")

    # Vérifie record id.
    def test_record_id(self):
        # Given (Arrange) une source avec un identifiant RIN
        source = build_source(["1 RIN SRIN"])
        # When (Act) on lit l'identifiant
        record_id = source.record_id
        # Then (Assert) l'identifiant est renseigné
        self.assertEqual(record_id, "SRIN")

    # Vérifie call number and repository note.
    def test_call_number_and_repository_note(self):
        # Given (Arrange) une source avec une cote et une note de dépôt
        source = build_source(["1 REPO @R1@", "2 CALN Cote 12", "2 NOTE Note dépôt"])
        # When (Act) on lit la cote et la note de dépôt
        call_number = source.call_number
        repo_note = source.repo_note
        # Then (Assert) les deux champs sont renseignés
        self.assertEqual(call_number, "Cote 12")
        self.assertEqual(repo_note, "Note dépôt")

    # Vérifie media under repository.
    def test_media_under_repository(self):
        # Given (Arrange) une source avec un média sous REPO
        source = build_source(["1 REPO @R1@", "2 CALN Cote", "3 MEDI photo.jpg"])
        # When (Act) on lit le média
        media = source.media
        # Then (Assert) le média est renseigné
        self.assertEqual(media, "photo.jpg")

    # Vérifie agency and data note.
    def test_agency_and_data_note(self):
        # Given (Arrange) une source avec une agence et une note sous DATA
        source = build_source(["1 DATA", "2 AGNC Registry", "2 NOTE Complementary"])
        # When (Act) on lit l'agence, le texte et les notes
        agency = source.agency
        text = source.text
        notes = source.notes
        # Then (Assert) l'agence est renseignée et la note reste une note
        self.assertEqual(agency, "Registry")
        self.assertIsNone(text)
        self.assertEqual(notes, ["Complementary"])

    # Vérifie data events details.
    def test_data_events_details(self):
        # Given (Arrange) une source avec un événement DATA détaillé
        source = build_source(
            ["1 DATA", "2 EVEN Census", "3 DATE 1900", "3 PLAC Paris"]
        )
        # When (Act) on lit les événements DATA
        events = source.data_events
        # Then (Assert) l'événement et ses détails sont collectés
        self.assertEqual(
            events,
            [{"value": "Census", "details": [("DATE", "1900"), ("PLAC", "Paris")]}],
        )

    # Vérifie data even note is not a source note.
    def test_data_even_note_is_not_a_source_note(self):
        # Given (Arrange) une note imbriquée dans DATA.EVEN
        source = build_source(["1 DATA", "2 EVEN Something", "3 NOTE Event note"])
        # When (Act) on lit les notes
        notes = source.notes
        # Then (Assert) seule une note enfant direct de DATA est retenue
        self.assertEqual(notes, [])

    # Vérifie data note keeps continuations.
    def test_data_note_keeps_continuations(self):
        # Given (Arrange) une source avec une note DATA continuée
        source = build_source(
            ["1 DATA", "2 NOTE Complementary", "3 CONT detail", "3 CONC !"]
        )
        # When (Act) on lit les notes
        notes = source.notes
        # Then (Assert) la continuation est fusionnée dans la note DATA
        self.assertEqual(notes, ["Complementary\ndetail!"])

    # Vérifie author and publication keep continuations.
    def test_author_and_publication_keep_continuations(self):
        # Given (Arrange) une source avec auteur et publication continués
        source = build_source(
            [
                "1 AUTH John",
                "2 CONT Doe",
                "1 PUBL Imprimerie",
                "2 CONT X",
            ]
        )
        # When (Act) on lit l'auteur et la publication
        author = source.author
        publication = source.publication
        # Then (Assert) les continuations sont fusionnées
        self.assertEqual(author, "John\nDoe")
        self.assertEqual(publication, "Imprimerie\nX")

    # Vérifie repository note keeps continuations.
    def test_repository_note_keeps_continuations(self):
        # Given (Arrange) une source avec une note de dépôt continuée
        source = build_source(["1 REPO @R1@", "2 NOTE Note dépôt", "3 CONT suite"])
        # When (Act) on lit la note de dépôt
        repo_note = source.repo_note
        # Then (Assert) la continuation est fusionnée
        self.assertEqual(repo_note, "Note dépôt\nsuite")

    # Vérifie notes setter none then get returns empty.
    def test_notes_setter_none_then_get_returns_empty(self):
        # Given (Arrange) une source dont les notes sont fixées à None
        source = build_source([])
        source.notes = None
        # When (Act) on relit les notes
        notes = source.notes
        # Then (Assert) la liste vide est retournée
        self.assertEqual(notes, [])

    # Vérifie sources setter none then get returns empty.
    def test_sources_setter_none_then_get_returns_empty(self):
        # Given (Arrange) une source dont les sources sont fixées à None
        source = build_source([])
        source.sources = None
        # When (Act) on relit les sources
        sources = source.sources
        # Then (Assert) la liste vide est retournée
        self.assertEqual(sources, [])

    # Vérifie references setter none then get returns empty.
    def test_references_setter_none_then_get_returns_empty(self):
        # Given (Arrange) une source dont les références sont fixées à None
        source = build_source([])
        source.references = None
        # When (Act) on relit les références
        references = source.references
        # Then (Assert) la liste vide est retournée
        self.assertEqual(references, [])

    # Vérifie data events setter none then get returns empty.
    def test_data_events_setter_none_then_get_returns_empty(self):
        # Given (Arrange) une source dont les événements sont fixés à None
        source = build_source([])
        source.data_events = None
        # When (Act) on relit les événements
        events = source.data_events
        # Then (Assert) la liste vide est retournée
        self.assertEqual(events, [])

    # Vérifie data events setter round trip.
    def test_data_events_setter_round_trip(self):
        # Given (Arrange) une source sans événement
        source = build_source([])
        # When (Act) on affecte des événements
        source.data_events = [{"value": "Custom", "details": []}]
        # Then (Assert) la valeur affectée est relue
        self.assertEqual(source.data_events, [{"value": "Custom", "details": []}])

    # Vérifie additional fields collect details.
    def test_additional_fields_collect_details(self):
        # Given (Arrange) une source avec un champ additionnel et deux niveaux de détails
        source = build_source(["1 EXTRA custom", "2 CHILD detail", "3 DEEP detail"])
        # When (Act) on lit les champs additionnels
        fields = source.additional_fields
        # Then (Assert) le champ et ses détails sont collectés
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["tag"], "EXTRA")
        self.assertEqual(
            fields[0]["details"], [("CHILD", "detail"), ("DEEP", "detail")]
        )

    # Vérifie notes are collected lazily with continuation.
    def test_notes_are_collected_lazily_with_continuation(self):
        # Given (Arrange) une source avec une note continuée par CONT
        source = build_source(["1 NOTE first", "2 CONT second"])
        # When (Act) on lit les notes
        notes = source.notes
        # Then (Assert) la note intègre la continuation
        self.assertEqual(notes, ["first\nsecond"])

    # Vérifie sources are collected lazily.
    def test_sources_are_collected_lazily(self):
        # Given (Arrange) une source avec une source secondaire
        source = build_source(["1 SOUR @S2@"])
        # When (Act) on lit les sources
        sources = source.sources
        # Then (Assert) la source secondaire est collectée
        self.assertEqual(sources, ["@S2@"])

    # Vérifie references are collected lazily.
    def test_references_are_collected_lazily(self):
        # Given (Arrange) une source avec une référence REFN
        source = build_source(["1 REFN Ref"])
        # When (Act) on lit les références
        references = source.references
        # Then (Assert) la référence est collectée
        self.assertEqual(references, ["Ref"])

    # Vérifie author at level one.
    def test_author_at_level_one(self):
        # Given (Arrange) une source avec un auteur au niveau 1
        source = build_source(["1 AUTH John Doe"])
        # When (Act) on lit l'auteur
        author = source.author
        # Then (Assert) l'auteur est renseigné
        self.assertEqual(author, "John Doe")

    # Vérifie data event without even is ignored.
    def test_data_event_without_even_is_ignored(self):
        # Given (Arrange) une source avec un sous-tag DATA autre que EVEN
        source = build_source(["1 DATA", "2 DATE 1900"])
        # When (Act) on lit les événements DATA
        events = source.data_events
        # Then (Assert) aucun événement n'est collecté
        self.assertEqual(events, [])

    # Vérifie malformed line is ignored.
    def test_malformed_line_is_ignored(self):
        # Given (Arrange) une source contenant une ligne malformée
        source = build_source(["invalid line"])
        # When (Act) on force le chargement paresseux des références
        notes = source.notes
        # Then (Assert) la ligne malformée est ignorée sans lever d'exception
        self.assertEqual(notes, [])


if __name__ == "__main__":
    unittest.main()
