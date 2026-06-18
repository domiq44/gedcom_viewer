class GedcomParser:
    def __init__(self):
        self.lines = []
        self.entities = {}   # dict: type → liste de GedcomEntity
        self._by_pointer = {}  # dict: pointer → GedcomEntity

    def load(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        # Normalisation minimale
        self.lines = [
            line.replace("\ufeff", "").replace("\xa0", " ").rstrip("\n\r")
            for line in raw_lines
        ]

        self._parse_entities()

    def _parse_entities(self):
        self.entities = {}
        self._by_pointer = {}

        current_lines = []
        current_pointer = None
        current_tag = None
        current_start_index = None

        for idx, line in enumerate(self.lines):
            stripped = line.strip()

            # Début d'une nouvelle entité niveau 0
            if stripped.startswith("0 "):
                # Si on avait une entité en cours, on la termine
                if current_tag is not None:
                    entity = GedcomEntity(
                        pointer=current_pointer,
                        tag=current_tag,
                        start_index=current_start_index,
                        lines=current_lines
                    )
                    self._register_entity(entity)

                # Nouvelle entité
                parts = stripped.split(" ")

                # Cas 1 : 0 @I1@ INDI
                if len(parts) >= 3 and parts[1].startswith("@") and parts[1].endswith("@"):
                    level = parts[0]      # "0"
                    pointer = parts[1]    # "@I1@"
                    tag = parts[2]        # "INDI"
                # Cas 2 : 0 HEAD / 0 NOTE sans pointeur
                elif len(parts) >= 2:
                    level = parts[0]
                    pointer = None
                    tag = parts[1]
                else:
                    # Ligne bizarre, on ignore
                    level = parts[0]
                    pointer = None
                    tag = None

                current_pointer = pointer
                current_tag = tag
                current_start_index = idx
                current_lines = [line + "\n"]  # on remet le \n pour l'affichage brut

            else:
                # Ligne de continuation / sous-niveau
                if current_tag is not None:
                    current_lines.append(line + "\n")

        # Terminer la dernière entité
        if current_tag is not None:
            entity = GedcomEntity(
                pointer=current_pointer,
                tag=current_tag,
                start_index=current_start_index,
                lines=current_lines
            )
            self._register_entity(entity)

    def _register_entity(self, entity: GedcomEntity):
        if entity.tag is None:
            return

        self.entities.setdefault(entity.tag, []).append(entity)

        if entity.pointer:
            self._by_pointer[entity.pointer] = entity


    def extract_block(self, pointer):
        """
        Retourne le bloc brut pour une entité donnée par son pointeur (@I1@).
        """
        entity = self._by_pointer.get(pointer)
        if not entity:
            return ""
        return entity.raw_block()
    
    def extract_head(self):
        """
        Retourne le bloc HEAD (0 HEAD ...), même sans pointeur.
        """
        # 1) Chercher une entité de type HEAD
        heads = self.entities.get("HEAD", [])
        if heads:
            return heads[0].raw_block()

        # 2) Fallback : recherche manuelle
        head_lines = []
        inside = False

        for line in self.lines:
            stripped = line.strip()

            if stripped.startswith("0 HEAD"):
                inside = True

            if inside:
                head_lines.append(stripped)

                if stripped.startswith("0 ") and not stripped.startswith("0 HEAD") and len(head_lines) > 1:
                    head_lines.pop()
                    break

        return "\n".join(head_lines).strip()

class GedcomEntity:
    def __init__(self, pointer, tag, start_index, lines):
        self.pointer = pointer      # ex: "@I1@" ou None
        self.tag = tag              # ex: "INDI", "FAM", "HEAD", "NOTE"
        self.start_index = start_index  # index de la ligne "0 ..."
        self.lines = lines          # liste de lignes brutes (incluant sous-niveaux)

    def raw_block(self):
        return "".join(self.lines)
    
    def get_tag_value(self, tag):
        """
        Retourne la valeur assemblée d'un tag GEDCOM (ex: NAME, NOTE, PLAC),
        en gérant CONC et CONT.
        """
        values = []
        collecting = False

        for line in self.lines:
            stripped = line.strip()
            parts = stripped.split(" ", 2)

            if len(parts) < 2:
                continue

            level = parts[0]

            # Ligne principale : ex "1 NOTE Texte..."
            if len(parts) == 3 and parts[1] == tag:
                collecting = True
                values.append(parts[2])
                continue

            # Si on est en train de collecter, regarder CONC / CONT
            if collecting:
                if len(parts) >= 3 and parts[1] == "CONC":
                    values[-1] += parts[2]  # même ligne
                elif len(parts) >= 3 and parts[1] == "CONT":
                    values.append(parts[2])  # nouvelle ligne
                else:
                    # Fin du bloc
                    break

        return "\n".join(values).strip()
