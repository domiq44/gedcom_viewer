# Développement

## Environnement

Créer l'environnement virtuel et installer les dépendances :

```bash
make install
```

Les dépendances d'exécution sont dans `requirements.txt` ; les dépendances de
développement sont dans `requirements-dev.txt`. `requirements-lock.txt` contient
les versions exactes utilisées par la CI.

## Commandes

| Commande | Action |
| --- | --- |
| `make run` | Installer les dépendances et lancer l'application |
| `make test` | Exécuter les tests unitaires (`unittest`) |
| `make format` | Formater les sources Python avec Black |
| `make lint` | Vérifier les sources (ruff + `black --check` + compilation) et la complétude des locales |
| `make typecheck` | Vérifier le typage de la production, du point d'entrée, des benchmarks et des scripts avec mypy |
| `make sanitize` | Enchaîner `lint` + `typecheck` + `test` |
| `make coverage` | Tests sous couverture + rapport lisible (seuil 93 %) + `htmlcov/index.html` |
| `make smoke` | Smoke-test de l'artefact PyInstaller (après `make dist`) |
| `make dist` | Construire l'application avec PyInstaller |
| `make clean` | Supprimer `.venv`, `build`, `dist`, `__pycache__`, les caches d'outils (`.mypy_cache`, `.ruff_cache`), la couverture (`.coverage`, `htmlcov`) et les métadonnées d'installation (`*.egg-info`) |

## Vérifications avant de finaliser

1. `make lint` passe.
2. `black --check` passe.
3. `make test` passe.
4. `make coverage` ne régresse pas.
5. Chaque module a un cartouche ; chaque fonction/méthode a une docstring.
6. Aucune donnée personnelle ni chemin absolu dans le code ou les tests.

Les choix d'architecture et la structure du dépôt sont décrits dans
[Architecture](ARCHITECTURE.md).
