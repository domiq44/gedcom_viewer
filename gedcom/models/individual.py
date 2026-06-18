# gedcom/individual.py

class Individual:
    """
    Représente un individu extrait d'une entité GEDCOM INDI.
    """
    def __init__(self, entity):
        self.entity = entity

        # Champs simples
        self.pointer = entity.pointer
        self.name = entity.get_tag_value("NAME")
        self.sex = entity.get_tag_value("SEX")

        # Naissance
        self.birth_date = entity.get_subtag_value("BIRT", "DATE")
        self.birth_place = entity.get_subtag_value("BIRT", "PLAC")

        # Décès
        self.death_date = entity.get_subtag_value("DEAT", "DATE")
        self.death_place = entity.get_subtag_value("DEAT", "PLAC")

        # Familles
        self.famc = entity.get_tag_value("FAMC")  # famille où il est enfant
        self.fams = entity.get_tag_value("FAMS")  # familles où il est parent

    def __repr__(self):
        return f"<Individual {self.pointer} {self.name}>"
