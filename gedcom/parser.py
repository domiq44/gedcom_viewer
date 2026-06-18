class GedcomParser:
    def __init__(self):
        self.lines = []
        self.entities = {}

    def load(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            self.lines = f.readlines()
        self.entities = self.detect_entities()

    def detect_entities(self):
        entities = {}
        for line in self.lines:
            if line.startswith("0 @"):
                parts = line.strip().split(" ")
                if len(parts) >= 3:
                    pointer = parts[1]
                    entity_type = parts[2]
                    entities.setdefault(entity_type, []).append(pointer)
        return entities

    def extract_block(self, pointer):
        block = []
        inside = False

        for line in self.lines:
            if line.startswith("0 " + pointer):
                inside = True
                block.append(line)
                continue
            if inside:
                if line.startswith("0 "):
                    break
                block.append(line)

        return "".join(block)
