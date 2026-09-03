# GEDCOM Viewer 5.5.1

<p align="center">
  <img src="docs/screenshots/gedcom-viewer-overview.png" alt="Capture d’écran du projet GEDCOM Viewer" width="1000" />
</p>

Un visualiseur GEDCOM écrit en **Python + Tkinter** pour explorer des fichiers au format **GEDCOM 5.5.1**.

## Vue d’ensemble

Le projet fournit une interface desktop légère pour ouvrir un fichier GEDCOM, visualiser le contenu brut, filtrer les entités, parcourir les relations entre objets et afficher les détails d’une entité dans des vues dédiées.

L’application est structurée en trois couches :

- `gedcom/` : parser GEDCOM, modèles métier et logique de représentation des entités
- `controllers/` : orchestration de la lecture, de la recherche, de l’affichage et de la résolution des pointeurs
- `ui/` : fenêtre principale, menus, thème, vues Tkinter et onglets d’affichage

### Flux de données

```text
UI (ui/) → Controller (controllers/) → GEDCOM model (gedcom/)
```

## Fonctionnalités prises en charge

- Chargement de fichiers GEDCOM (`.ged`)
- Sélection par type d’entité
- Recherche instantanée dans la liste des entités
- Onglets verticaux à gauche pour sélectionner le type d’entité
- Liste des entités en deux colonnes : nom lisible et identifiant GEDCOM
- Tri croissant/décroissant en cliquant sur les en-têtes de colonnes
- Tri des individus par nom de famille (`SURN`) et des identifiants par partie numérique
- Navigation par pointeurs GEDCOM (`@I...@`, `@F...@`, etc.)
- Affichage du bloc GEDCOM brut dans le panneau gauche
- Mise en surbrillance syntaxique basique du bloc brut
- Navigation avec boutons précédent / suivant
- Historique de navigation pour l’exploration des entités
- Menu `Fichier > Récents` pour recharger rapidement les derniers GEDCOM ouverts
- Menu `Fichier > Effacer la liste des fichiers récents` pour vider l’historique enregistré sans supprimer les fichiers GEDCOM
- Sous-menus `Inspecter` et `Navigation` pour garder le menu `Fichier` organisé
- Vues détaillées pour :
  - `INDI` (individu)
  - `FAM` (famille)
  - `SOUR` (source)
  - `REPO` (dépôt)
  - `NOTE` (note)
  - `OBJE` (multimédia)
  - `SUBM` (submitter)
- Prévisualisation d’images multimédia dans l’onglet `Multimédia`
- Scroll vertical dans la vue multimédia pour accéder aux champs texte en dessous de l’image
- Défilement vertical dans les formulaires longs
- Affichage des références avec leur libellé associé, lorsque l’entité est disponible
- Formulaires enrichis pour Famille, Note, Source et Dépôt
- Journalisation locale vers `~/.gedcom_viewer.log`
- Panneau d’état `Dernière erreur log` dans l’interface

## Types d’entités supportés

- `INDI` — Individu
- `FAM` — Famille
- `OBJE` — Multimédia
- `NOTE` — Note
- `SOUR` — Source
- `SUBM` — Submitter
- `REPO` — Dépôt
- `HEAD` — En-tête GEDCOM
- `TRLR` — Fin de fichier

## Prérequis

Le projet dépend principalement de :

- Python 3.x
- Tkinter
- Pillow pour la prévisualisation d’images dans l’onglet multimédia

> Sur la plupart des systèmes, Tkinter est livré avec Python. Pillow est recommandé pour la prévisualisation des images multimédia.

Installation manuelle de Pillow :

```bash
python -m pip install Pillow
```

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/<votre-utilisateur>/gedcom-viewer.git
cd gedcom-viewer
```

### 2. Préparer l’environnement

Le dépôt fournit un `Makefile` pour installer les dépendances de build et lancer l’application.

```bash
make install
```

Si vous utilisez un environnement virtuel local, le projet s’appuie sur `.venv/bin/python` lorsque ce dossier existe.

## Lancer l’application

### Via le script fourni

```bash
./run.sh
```

### Via Python directement

```bash
python main.py
```

### Si vous utilisez l’environnement virtuel du projet

```bash
.venv/bin/python main.py
```

## Tests

Le projet contient une suite de tests unitaires couvrant notamment :

- le parser GEDCOM
- les contrôleurs applicatifs
- la résolution des entités et des blocs `HEAD` / `TRLR`
- la fenêtre principale et la vue multimédia

### Exécuter la suite de tests

```bash
make test
```

ou directement :

```bash
python -m unittest discover -s tests
```

### Vérifier la syntaxe Python

```bash
make lint
```

## Build et distribution

Un `Makefile` facilite la création d’un exécutable autonome avec PyInstaller.

### Commandes utiles

```bash
make install
make run
make test
make lint
make dist
make clean
```

### Générer l’exécutable

```bash
make dist
```

Le binaire est produit dans :

```text
dist/gedcom_viewer
```

### Nettoyer les artefacts

```bash
make clean
```

Cette commande supprime :

- `build/`
- `dist/`
- `gedcom_viewer.spec`

## Journalisation

L’application enregistre ses messages de runtime dans un fichier local du profil utilisateur :

```text
~/.gedcom_viewer.log
```

Cette journalisation est utilisée pour diagnostiquer les erreurs d’affichage, le chargement des médias et les problèmes de runtime dans le binaire distribué.

## Fichiers récents

Lorsqu’un GEDCOM est ouvert, l’application mémorise les chemins récents dans :

```text
~/.gedcom_viewer_recent.json
```

Le menu `Fichier > Récents` permet de relancer rapidement un fichier déjà ouvert.

## Structure du dépôt

```text
.
├── controllers/
│   ├── app_controller.py
│   ├── entity_controller.py
│   ├── entity_labels.py
│   ├── gedcom_service.py
│   ├── presentation_controller.py
│   └── search_controller.py
├── gedcom/
│   ├── __init__.py
│   ├── parser.py
│   └── models/
│       ├── event.py
│       ├── family.py
│       ├── individual.py
│       ├── note.py
│       ├── object.py
│       ├── repository.py
│       ├── source.py
│       └── submitter.py
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── menus.py
│   ├── syntax_highlighter.py
│   ├── themes.py
│   └── views/
│       ├── family_view.py
│       ├── individual_view.py
│       ├── multimedia_view.py
│       ├── note_view.py
│       ├── repo_view.py
│       ├── source_view.py
│       └── submitter_view.py
├── main.py
├── Makefile
├── README.md
├── run.sh
└── tests/
```

## Développement et contribution

- Ouvrir une issue pour signaler un bug ou proposer une amélioration
- Travailler dans une branche dédiée
- Soumettre une pull request avec une description concise des changements

## Vérifications effectuées

La suite actuelle a été exécutée et validée dans l’environnement du projet :

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Résultat vérifié : `61 tests` exécutés, `OK`.
