"""Tests du service de construction d'arbre d'ascendance."""

import unittest

from controllers.ancestor_tree_service import AncestorNode, AncestorTreeService


class _FakeIndividual:
    """Individu factice pour les tests."""

    def __init__(
        self,
        pointer,
        name,
        birth_date="",
        death_date="",
        sex=None,
        famc=None,
        obje=None,
    ):
        """Initialise l'individu factice."""
        self.pointer = pointer
        self.name = name
        self.birth_date = birth_date
        self.death_date = death_date
        self.sex = sex
        self.famc = famc
        self.obje = obje or []


class _FakeFamily:
    """Famille factice pour les tests."""

    def __init__(self, pointer, husband=None, wife=None):
        """Initialise la famille factice."""
        self.pointer = pointer
        self.husband = husband
        self.wife = wife


class _FakeMultimediaObject:
    """Objet multimédia factice pour les tests."""

    def __init__(self, pointer, file=None):
        """Initialise l'objet multimédia factice."""
        self.pointer = pointer
        self.file = file


class _FakeController:
    """Contrôleur factice avec des individus et familles en mémoire."""

    def __init__(self, individuals, families, objects=None):
        """Initialise le contrôleur factice."""
        self._individuals = {i.pointer: i for i in individuals}
        self._families = {f.pointer: f for f in families}
        self._objects = {o.pointer: o for o in (objects or [])}

    def get_individual(self, pointer):
        """Retourne l'individu correspondant au pointeur."""
        return self._individuals.get(pointer)

    def get_family(self, pointer):
        """Retourne la famille correspondant au pointeur."""
        return self._families.get(pointer)

    def get_object(self, pointer):
        """Retourne l'objet multimédia correspondant au pointeur."""
        return self._objects.get(pointer)


class TestAncestorTreeService(unittest.TestCase):
    """Vérifie la construction de l'arbre d'ascendance."""

    # Vérifie build_tree retourne None pour un pointeur None.
    def test_build_tree_none_pointer_returns_none(self):
        # Given (Arrange) un service avec un contrôleur vide
        controller = _FakeController([], [])
        service = AncestorTreeService(controller)
        # When (Act) on construit l'arbre avec un pointeur None
        result = service.build_tree(None)
        # Then (Assert) le résultat est None
        self.assertIsNone(result)

    # Vérifie build_tree crée un nœud racine sans parents.
    def test_build_tree_root_without_parents(self):
        # Given (Arrange) un individu sans famille parent
        indi = _FakeIndividual("@I1@", "John /Doe/", "1 JAN 1900", "", "M")
        controller = _FakeController([indi], [])
        service = AncestorTreeService(controller)
        # When (Act) on construit l'arbre avec 3 générations
        root = service.build_tree("@I1@", 3)
        # Then (Assert) le nœud racine contient les données de l'individu
        self.assertIsNotNone(root)
        self.assertEqual(root.pointer, "@I1@")
        self.assertEqual(root.name, "Doe, John")
        self.assertEqual(root.birth_date, "1900-01-01")
        self.assertIsNone(root.father)
        self.assertIsNone(root.mother)

    # Vérifie build_tree récupère le père via FAMC/HUSB.
    def test_build_tree_retrieves_father(self):
        # Given (Arrange) un individu avec un père dans une famille
        father = _FakeIndividual("@I2@", "William /Doe/", "", "", "M")
        child = _FakeIndividual("@I1@", "John /Doe/", "", "", "M", famc="@F1@")
        family = _FakeFamily("@F1@", husband="@I2@")
        controller = _FakeController([father, child], [family])
        service = AncestorTreeService(controller)
        # When (Act) on construit l'arbre
        root = service.build_tree("@I1@", 2)
        # Then (Assert) le père est le nœud père du racine
        self.assertIsNotNone(root)
        self.assertIsNotNone(root.father)
        self.assertEqual(root.father.pointer, "@I2@")
        self.assertEqual(root.father.name, "Doe, William")

    # Vérifie build_tree récupère la mère via FAMC/WIFE.
    def test_build_tree_retrieves_mother(self):
        # Given (Arrange) un individu avec une mère dans une famille
        mother = _FakeIndividual("@I3@", "Jane /Smith/", "", "", "F")
        child = _FakeIndividual("@I1@", "John /Doe/", "", "", "M", famc="@F1@")
        family = _FakeFamily("@F1@", wife="@I3@")
        controller = _FakeController([mother, child], [family])
        service = AncestorTreeService(controller)
        # When (Act) on construit l'arbre
        root = service.build_tree("@I1@", 2)
        # Then (Assert) la mère est le nœud mère du racine
        self.assertIsNotNone(root)
        self.assertIsNotNone(root.mother)
        self.assertEqual(root.mother.pointer, "@I3@")
        self.assertEqual(root.mother.name, "Smith, Jane")

    # Vérifie build_tree récupère les grands-parents paternels.
    def test_build_tree_retrieves_paternal_grandparents(self):
        # Given (Arrange) un individu, son père et les grands-parents paternels
        grandpa = _FakeIndividual("@I4@", "Robert /Doe/", "", "", "M")
        grandma = _FakeIndividual("@I5@", "Alice /Doe/", "", "", "F")
        father = _FakeIndividual("@I2@", "William /Doe/", "", "", "M", famc="@F2@")
        child = _FakeIndividual("@I1@", "John /Doe/", "", "", "M", famc="@F1@")
        family_child = _FakeFamily("@F1@", husband="@I2@")
        family_father = _FakeFamily("@F2@", husband="@I4@", wife="@I5@")
        controller = _FakeController(
            [grandpa, grandma, father, child], [family_child, family_father]
        )
        service = AncestorTreeService(controller)
        # When (Act) on construit l'arbre avec 3 générations
        root = service.build_tree("@I1@", 3)
        # Then (Assert) les grands-parents paternels sont présents
        self.assertIsNotNone(root)
        self.assertIsNotNone(root.father)
        self.assertIsNotNone(root.father.father)
        self.assertIsNotNone(root.father.mother)
        self.assertEqual(root.father.father.pointer, "@I4@")
        self.assertEqual(root.father.mother.pointer, "@I5@")

    # Vérifie generations limite la profondeur de l'arbre.
    def test_build_tree_limits_generations(self):
        # Given (Arrange) une chaîne d'ancêtres sur 4 générations
        g3 = _FakeIndividual("@I4@", "Gen3", "", "", "M")
        g2 = _FakeIndividual("@I3@", "Gen2", "", "", "M", famc="@F3@")
        g1 = _FakeIndividual("@I2@", "Gen1", "", "", "M", famc="@F2@")
        g0 = _FakeIndividual("@I1@", "Gen0", "", "", "M", famc="@F1@")
        f3 = _FakeFamily("@F3@", husband="@I4@")
        f2 = _FakeFamily("@F2@", husband="@I3@")
        f1 = _FakeFamily("@F1@", husband="@I2@")
        controller = _FakeController([g3, g2, g1, g0], [f3, f2, f1])
        service = AncestorTreeService(controller)
        # When (Act) on construit l'arbre avec 2 générations seulement
        root = service.build_tree("@I1@", 2)
        # Then (Assert) l'arbre s'arrête à la génération demandée
        self.assertIsNotNone(root)
        self.assertEqual(root.pointer, "@I1@")
        self.assertIsNotNone(root.father)
        self.assertEqual(root.father.pointer, "@I2@")
        self.assertIsNone(root.father.father)

    # Vérifie qu'à partir de la 5e génération, la date de naissance n'est pas
    # affichée mais que la date de décès est conservée (témoin de décès).
    def test_build_tree_no_dates_from_fifth_generation(self):
        # Given (Arrange) une chaîne d'ancêtres sur 5 générations avec dates
        g4 = _FakeIndividual("@I5@", "Gen4", "1 JAN 1800", "1 JAN 1850", "M")
        g3 = _FakeIndividual("@I4@", "Gen3", "1 JAN 1830", "", "M", famc="@F4@")
        g2 = _FakeIndividual("@I3@", "Gen2", "1 JAN 1860", "", "M", famc="@F3@")
        g1 = _FakeIndividual("@I2@", "Gen1", "1 JAN 1890", "", "M", famc="@F2@")
        g0 = _FakeIndividual("@I1@", "Gen0", "1 JAN 1920", "", "M", famc="@F1@")
        f4 = _FakeFamily("@F4@", husband="@I5@")
        f3 = _FakeFamily("@F3@", husband="@I4@")
        f2 = _FakeFamily("@F2@", husband="@I3@")
        f1 = _FakeFamily("@F1@", husband="@I2@")
        controller = _FakeController([g4, g3, g2, g1, g0], [f4, f3, f2, f1])
        service = AncestorTreeService(controller)
        # When (Act) on construit l'arbre sur 5 générations
        root = service.build_tree("@I1@", 5)
        # Then (Assert) les générations 0-3 ont les dates, la 4e a birth_date
        # vide mais death_date conservée pour le témoin de décès
        self.assertIsNotNone(root)
        self.assertEqual(root.birth_date, "1920-01-01")
        self.assertIsNotNone(root.father)
        self.assertEqual(root.father.birth_date, "1890-01-01")
        self.assertIsNotNone(root.father.father)
        self.assertEqual(root.father.father.birth_date, "1860-01-01")
        self.assertIsNotNone(root.father.father.father)
        self.assertEqual(root.father.father.father.birth_date, "1830-01-01")
        self.assertIsNotNone(root.father.father.father.father)
        self.assertEqual(root.father.father.father.father.birth_date, "")
        self.assertEqual(root.father.father.father.father.death_date, "1850-01-01")

    # Vérifie AncestorNode.label affiche nom et dates.
    def test_ancestor_node_label(self):
        # Given (Arrange) un nœud avec nom et dates
        node = AncestorNode("@I1@", "John /Doe/", "1 JAN 1900", "1 JAN 2000", "M")
        # When (Act) on lit le libellé
        label = node.label
        # Then (Assert) le libellé contient le nom et les dates
        self.assertEqual(label, "Doe, John \u2013 * 1900-01-01 \u2013 ✝ 2000-01-01")

    # Vérifie AncestorNode.label sans dates.
    def test_ancestor_node_label_without_dates(self):
        # Given (Arrange) un nœud avec seulement un nom
        node = AncestorNode("@I1@", "John /Doe/")
        # When (Act) on lit le libellé
        label = node.label
        # Then (Assert) le libellé contient seulement le nom nettoyé
        self.assertEqual(label, "Doe, John")

    # Vérifie _find_photo_path retourne un chemin de fichier inline.
    def test_find_photo_path_with_inline_file(self):
        # Given un individu avec un chemin de fichier photo dans OBJE
        individual = _FakeIndividual("@I1@", "John /Doe/", obje=["photos/john.jpg"])
        controller = _FakeController([individual], [])
        service = AncestorTreeService(controller)
        # When on cherche le chemin de la photo
        path = service._find_photo_path(individual)
        # Then le chemin inline est retourné
        self.assertEqual(path, "photos/john.jpg")

    # Vérifie _find_photo_path résout un pointeur OBJE.
    def test_find_photo_path_with_obje_pointer(self):
        # Given un individu avec un pointeur OBJE et un objet multimédia
        obje = _FakeMultimediaObject("@O1@", "photos/ancestor.png")
        individual = _FakeIndividual("@I1@", "John /Doe/", obje=["@O1@"])
        controller = _FakeController([individual], [], objects=[obje])
        service = AncestorTreeService(controller)
        # When on cherche le chemin de la photo
        path = service._find_photo_path(individual)
        # Then le fichier de l'objet multimédia est retourné
        self.assertEqual(path, "photos/ancestor.png")

    # Vérifie _find_photo_path retourne une chaîne vide sans photo.
    def test_find_photo_path_without_photo(self):
        # Given un individu sans OBJE photo
        individual = _FakeIndividual("@I1@", "John /Doe/", obje=["notes.txt"])
        controller = _FakeController([individual], [])
        service = AncestorTreeService(controller)
        # When on cherche le chemin de la photo
        path = service._find_photo_path(individual)
        # Then aucune photo n'est trouvée
        self.assertEqual(path, "")

    # Vérifie _find_photo_path ignore une référence non-chaîne.
    def test_find_photo_path_ignores_non_string_ref(self):
        # Given un individu avec une référence None dans OBJE
        individual = _FakeIndividual("@I1@", "John /Doe/", obje=[None, 123])
        controller = _FakeController([individual], [])
        service = AncestorTreeService(controller)
        # When on cherche le chemin de la photo
        path = service._find_photo_path(individual)
        # Then aucune photo n'est trouvée (pas de crash)
        self.assertEqual(path, "")

    # Vérifie _find_photo_path ignore une référence vide ou "*".
    def test_find_photo_path_ignores_empty_or_star(self):
        # Given un individu avec des références vides et "*"
        individual = _FakeIndividual("@I1@", "John /Doe/", obje=["", "*", "   "])
        controller = _FakeController([individual], [])
        service = AncestorTreeService(controller)
        # When on cherche le chemin de la photo
        path = service._find_photo_path(individual)
        # Then aucune photo n'est trouvée
        self.assertEqual(path, "")

    # Vérifie _find_photo_path ignore un pointeur OBJE sans fichier.
    def test_find_photo_path_obje_pointer_without_file(self):
        # Given un individu avec un pointeur OBJE vers un objet sans fichier
        obje = _FakeMultimediaObject("@O1@", None)
        individual = _FakeIndividual("@I1@", "John /Doe/", obje=["@O1@"])
        controller = _FakeController([individual], [], objects=[obje])
        service = AncestorTreeService(controller)
        # When on cherche le chemin de la photo
        path = service._find_photo_path(individual)
        # Then aucune photo n'est trouvée
        self.assertEqual(path, "")


if __name__ == "__main__":
    unittest.main()
