# PROJECT.md — Spécificités du projet gedcom_viewer

Ce fichier décrit les spécificités d'implémentation, de domaine et de stack du
projet gedcom_viewer. Il complète `AGENTS.md` qui énonce les principes de qualité
génériques.

## Comment utiliser ces deux fichiers

- **`AGENTS.md`** énonce les principes de qualité génériques applicables à tout projet.
- **`PROJECT.md`** (à la racine de ce dépôt) définit les spécificités de stack,
  domaine et outillage du projet gedcom_viewer.
- En cas de doute, `AGENTS.md` prévaut sur les principes de qualité et
  `PROJECT.md` sur les détails d'implémentation.
- Toute modification de comportement, d'API ou d'architecture doit être répercutée
  dans les deux fichiers dans la même modification.

## 1. Projet

Application Python avec interface graphique (Tkinter) de **lecture seule** pour
explorer des fichiers GEDCOM 5.5.1. Architecture **MVP** en trois couches :
domaine (`gedcom/`), contrôleurs/présentateurs (`controllers/`), interface
(`ui/`). Le point d'entrée initialise le thème, les diagnostics puis la boucle
d'événements.

Le `README.md` est une porte d'entrée courte ; les sujets détaillés vivent dans
`docs/`, un fichier par responsabilité.

## 2. Domaine et stack technique

- Langage : Python 3.11+
- Interface : Tkinter / ttk
- Images : Pillow
- PDF : pypdfium2
- Build autonome : PyInstaller via `gedcom_viewer.spec`
- Point d'entrée : `main.py`

## 3. Arborescence

```
gedcom/           # Domaine : parsing, validation, modèles, continuations
controllers/      # Contrôleurs et présentateurs (façade, résumés, contexte)
ui/               # Interface (vues, thèmes, préférences, chargement asynchrone)
tests/            # Tests unitaires (unittest), miroirs de production
docs/             # Documentation détaillée (un fichier par responsabilité)
scripts/          # Scripts de capture et de génération
benchmarks/       # Tests de performance et de mémoire
```

## 4. Architecture

L'architecture détaillée (couches, dépendances, protocole des résolveurs,
remplacement de session, re-thème) est documentée dans `docs/ARCHITECTURE.md`.
Les spécificités de configuration du projet sont résumées ci-dessous.

- **Préférences de session** : thème, langue, fichiers récents, taille de fenêtre
  et positions des panneaux sont isolées dans un module dédié ; l'orchestrateur
  principal (`GedcomViewer`) reste responsable du cycle de vie.
- **Thème** : thèmes clair et sombre avec changement à l'exécution via un registre
  par session ; les composants exposant `apply_theme()` s'y enregistrent sans
  liste codée en dur.


## 5. Tests

- Framework : `unittest` uniquement.
- Découverte : `python3 -m unittest discover -s tests -t .`
- Arborescence : `tests/gedcom/`, `tests/controllers/`, `tests/ui/`,
  `tests/ui/views/`, `tests/benchmarks/`.
- Structure obligatoire : AAA avec commentaires Given/When/Then.
- Commentaire descriptif (`# Vérifie …`) placé juste au-dessus de chaque
  fonction de test.
- Un seul scénario par méthode de test.
- Un fichier de test par module testé ; une classe de test par unité.
- Tests de conformité : `tests/test_docstrings.py` et
  `tests/test_test_comments.py`.

## 6. Qualité & outillage

- Lint : `make lint` (ruff + `black --check` + compilation des sources).
- Format : `make format` (black) ; la CI vérifie `black --check`.
- Typage : `mypy` progressif sur les couches de production et les outils.
- Couverture : `make coverage` ; plancher à 93 %, ne pas la faire baisser.
- Dépendances : `requirements-lock.txt` contient les versions exactes utilisées
  par la CI ; `pip-audit --strict` est exécuté sur ce lock.
- CI : les actions GitHub sont épinglées à des versions explicites.
- Vérifications avant de finaliser : voir `AGENTS.md` section 15. Les
  spécificités projet sont : commande de découverte des tests
  (`python3 -m unittest discover -s tests -t .`), plancher de couverture (93 %),
  environnement headless (`xvfb-run`).

## 7. Chargement asynchrone

- Coordinateur : `ui/load_coordinator.py` (`LoadCoordinator`).
- Chargement hors thread Tkinter via `threading.Thread` et polling
  `root.after()`.
- Événement d'annulation (`threading.Event`) vérifié pendant le parsing et la
  validation.
- Callbacks de succès/erreur encadrés par `try/except`.
- Remplacement de session uniquement après chargement réussi ; restauration
  depuis un instantané en cas d'échec.

## 8. Internationalisation

- Langues supportées : anglais (défaut et fallback), français, espagnol,
  allemand, italien, portugais.
- Fichiers de locale : `ui/locales/{en,fr,es,de,it,pt}.json`.
- Toute nouvelle chaîne visible doit être ajoutée dans **tous** les fichiers de
  locale.

## 9. Build & packaging

- Spécification PyInstaller : `gedcom_viewer.spec`.
- Les tests ne sont pas embarqués dans l'exécutable.
- Un smoke test de l'artefact doit valider le démarrage.
- Gestion de l'affichage headless (X11 virtuel via `xvfb-run`).

## 10. Benchmark

- Générateur de GEDCOM représentatif : `benchmarks/generate_gedcom.py`.
- Le benchmark rapporte temps et mémoire (médiane / p95, mémoire résidente
  RSS).

## 11. Scripts

- `scripts/lancer_pour_capture.sh` : génère un GEDCOM de test pour les
  captures d'écran de l'arbre d'ascendance.
