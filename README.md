# GEDCOM Viewer 5.5.1

![Interface de GEDCOM Viewer](docs/screenshots/gedcom-viewer-overview.png)

GEDCOM Viewer est une application de bureau Python/Tkinter pour ouvrir et explorer des fichiers GEDCOM.

## Documentation

Le dépôt conserve une documentation minimale et ciblée :

- [README.md](README.md) : vue d’ensemble, installation, lancement, tests et utilisation quotidienne.
- [docs/architecture.md](docs/architecture.md) : description technique de l’architecture, des flux et des composants.
- [docs/analysis.md](docs/analysis.md) : analyse du projet, limites connues, points de vigilance et recommandations.
- [docs/roadmap.md](docs/roadmap.md) : priorités d’évolution et plan de refonte / consolidation.

## Fonctionnalités

- Ouverture de fichiers GEDCOM `.ged`.
- Deux modes d'ouverture : tolérant ou strict avec validation structurelle.
- Liste des entités par type : `INDI`, `FAM`, `SOUR`, `REPO`, `NOTE`, `OBJE` et `SUBM`.
- Recherche réactive dans les entités avec debounce pour limiter les recalculs.
- Bouton d'effacement rapide du filtre de recherche.
- Bouton d'effacement intégré à la palette visuelle de l'application.
- Tri par nom, titre ou identifiant, avec tri numérique des pointeurs.
- Navigation entre les pointeurs GEDCOM tels que `@I1@` ou `@F1@`.
- Historique de navigation précédent/suivant.
- Affichage du bloc GEDCOM brut avec coloration syntaxique.
- Affichage des blocs `HEAD` et `TRLR`.
- Gestion des fichiers récemment ouverts.
- Vues détaillées pour les individus, familles, sources, dépôts, notes, médias et submitters.
- Formulaire Individu avec onglets « Familles (parent) » (liste à deux colonnes
  nom/identifiant) et « Enfants ».
- Panneau de détail (bloc GEDCOM brut / formulaire d'entité) redimensionnable
  via un séparateur déplaçable.
- Prévisualisation des images locales dans l'onglet multimédia avec Pillow.
- Chargement des fichiers en arrière-plan afin de maintenir l'interface réactive,
  avec publication atomique du contrôleur après succès.
- Conservation de l'état chargé en cas d'échec et arrêt propre du polling lors de
  la fermeture de la fenêtre.
- Journalisation dans `~/.gedcom_viewer.log`.
- Affichage du temps de chargement dans la barre de statut.
- Signalement dans le journal des lignes malformées et des caractères remplacés lors de la lecture.
- Validation structurelle disponible en mode strict via `load(..., strict=True)`.
- Infrastructure d'internationalisation avec l'anglais comme langue par défaut.
- Interface disponible en anglais, français, espagnol, allemand, italien et portugais.
- Le changement de langue est appliqué au redémarrage.

L'application est en lecture seule : elle n'édite ni ne sauvegarde les fichiers GEDCOM.

## Champs utilisés par la recherche

La recherche porte sur les champs GEDCOM suivants :

| Type | Champs recherchés |
| --- | --- |
| `INDI` | Pointeur de l'individu et `NAME` |
| `FAM` | Pointeur de la famille et `NAME` des individus référencés par `HUSB`, `WIFE` ou `CHIL` |
| `SOUR` | Pointeur de la source et `TITL` |
| `REPO` | Pointeur du dépôt et `NAME` |
| `NOTE` | Pointeur de la note et texte de la note |
| `OBJE` | Pointeur du média, `TITL` et `FILE` |
| `SUBM` | Pointeur du submitter, `NAME` et `EMAIL` |

La recherche est insensible à la casse et aux accents pour tous ces champs :
`cretel` trouve notamment `crétel`, `Crétel` et `Cretel`, quel que soit le type
d'entité recherché.

## Architecture

```text
UI Tkinter (ui/)
  -> contrôleurs (controllers/) [thread principal]
        -> service GEDCOM
            -> parser et modèles métier (gedcom/)
```

Le chargement et la construction des modèles sont exécutés dans un thread de
travail. Les résultats et les erreurs sont ensuite appliqués à l'interface dans
le thread Tkinter principal.

- `gedcom/` contient le parser et les modèles métier.
- `controllers/` coordonne le chargement, la recherche, le tri et la résolution des pointeurs.
- `ui/` contient la fenêtre principale, les menus, le thème et les vues spécialisées.
- `ui/i18n.py` charge les traductions depuis les catalogues JSON de `ui/locales/`.
- `tests/` contient les tests unitaires et les tests UI Tkinter.

## Prérequis

- Python 3.x
- Tkinter
- Accès à `pip` pour installer Pillow, PyInstaller et Black

Sur Debian ou Ubuntu, Tkinter peut être installé avec :

```bash
sudo apt install python3-tk
```

## Installation

Le `Makefile` crée automatiquement `.venv` si nécessaire et installe les outils requis :

```bash
make install
```

Cette commande installe :

- Pillow pour la prévisualisation des images ;
- PyInstaller pour la génération de l'exécutable ;
- Black pour le formatage du code.

Les dépendances runtime sont listées dans `requirements.txt` et les outils de
développement dans `requirements-dev.txt`. La cible `make run` vérifie
l'environnement virtuel et installe ou met à jour les dépendances avant le
lancement.

## Lancement

Avec le script fourni :

```bash
./run.sh
```

Ou directement avec Python :

```bash
python3 main.py
```

Avec l'environnement virtuel du projet :

```bash
.venv/bin/python main.py
```

Au démarrage, l'application tente de recharger le dernier fichier GEDCOM récent lorsqu'il existe encore.

Dans le menu `Fichier`, `Ouvrir un fichier GEDCOM` conserve le mode tolérant.
`Ouvrir et valider un fichier GEDCOM` utilise le mode strict et refuse les
anomalies structurelles détectées. Les fichiers récents sont rechargés en mode
tolérant.

## Tests et vérifications

Exécuter les tests :

```bash
make test
```

Ou directement :

```bash
.venv/bin/python -m unittest discover -s tests
```

Dernière validation : 130 tests présents dans la suite.

Vérifier la syntaxe Python :

```bash
make lint
```

Formater le code avec Black :

```bash
make format
```

## Génération de l'exécutable

Créer une version autonome avec PyInstaller :

```bash
make dist
```

L'exécutable est généré dans :

```text
dist/gedcom_viewer
```

Nettoyer les artefacts de build et l'environnement virtuel :

```bash
make clean
```

Cette commande supprime `build/`, `dist/`, `.venv/` et les répertoires `__pycache__/`.

## Fichiers utilisateur

Les journaux sont écrits dans :

```text
~/.gedcom_viewer.log
```

Les préférences, le répertoire du dernier GEDCOM chargé et la liste des fichiers
récents sont enregistrés dans :

```text
~/.gedcom_viewer.json
```

## Limites connues

- Les gros fichiers sont toujours chargés entièrement en mémoire. Une mesure synthétique sur 100 000 individus a donné environ 1,45 seconde et 169 Mo de mémoire maximale. Les entités brutes utilisent `__slots__` pour limiter leur surcharge, mais il n'y a pas encore de chargement différé.
- Les événements familiaux sont représentés par le modèle `Event`, mais leur structure reste volontairement simple : un tag, une valeur et une liste de sous-tags.
- Les événements de mariage multiples sont affichés dans la vue famille, mais ne disposent pas encore d'une présentation détaillée dédiée.
- Le parser signale les anomalies, mais ne réalise pas une validation complète de conformité GEDCOM.
- L'ouverture standard reste tolérante ; le mode strict est également accessible dans le menu `Fichier` et via l'API Python.

## Structure du projet

```text
.
├── controllers/
├── gedcom/
│   └── models/
├── ui/
│   └── views/
├── tests/
├── main.py
├── Makefile
├── gedcom_viewer.spec
└── run.sh
```

## Licence et contributions

Aucun fichier de licence n'est fourni dans le dépôt. Les contributions peuvent être proposées via une branche dédiée et une pull request, accompagnées de tests pour les changements de comportement.
