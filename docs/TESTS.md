# Tests

## Exécution

Sur une machine avec un affichage disponible :

```bash
make test
```

Ou, après installation des dépendances avec `make install` (ou `make venv install`) :

```bash
.venv/bin/python -m unittest discover -s tests -t .
```

En environnement Linux sans affichage, exécute la suite Tkinter sous Xvfb :

```bash
xvfb-run --auto-servernum .venv/bin/python -m unittest discover -s tests -t .
```

## Organisation

Les tests suivent l'arborescence de production :

```text
tests/
├── gedcom/       parseur, validateur, continuations et modèles
├── controllers/  contrôleurs et présentation
├── ui/           interface Tkinter
├── ui/views/     vues par entité
└── benchmarks/   outils de benchmark
```

Chaque fichier de test correspond à une responsabilité de production. Les tests
du domaine sont répartis en `test_gedcom_parser.py` (parsing, extraction et
cache), `test_validator.py` (structure et pointeurs),
`test_entity_tag_values.py` (valeurs de tags d'une entité) et, sous
`tests/gedcom/models/`, un fichier par modèle plus `test_model_contracts.py`
(paresse et mutabilité), `test_model_contract.py` (construction depuis les lignes
parsées) et `test_continuations.py` (CONT/CONC). Les tests utilisent `unittest`
et la structure AAA avec commentaires `Given`/`When`/`Then`.

## Couverture

```bash
make coverage
```

La commande exécute les tests sous couverture, affiche un rapport lisible et
génère `htmlcov/index.html`. Le seuil global plancher est de 93 %. Un garde-fou
additionnel vérifie les modules critiques : `controllers/app_controller.py`,
`controllers/citation_controller.py`, `controllers/entity_controller.py`,
`controllers/presentation_controller.py`, `controllers/search_controller.py`,
`gedcom/continuations.py`, `gedcom/parser.py`, `gedcom/validator.py` et
`ui/load_coordinator.py`.

Un test de conformité vérifie notamment les cartouches et docstrings des modules
de production, ainsi que la présence d'un commentaire avant chaque méthode de
test.
