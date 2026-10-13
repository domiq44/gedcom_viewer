# GEDCOM Viewer 5.5.1

![Interface de GEDCOM Viewer](docs/screenshots/gedcom-viewer-overview.png)

GEDCOM Viewer est une application de bureau Python/Tkinter pour lire et explorer
des fichiers GEDCOM. Elle fonctionne en lecture seule : les fichiers ne sont
pas modifiés ni sauvegardés.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Installation et lancement](#installation-et-lancement)
- [Utilisation](#utilisation)
- [Recherche](#recherche)
- [Formats et limites](#formats-et-limites)
- [Développement](#développement)
- [Tests](#tests)
- [Benchmarks](#benchmarks)
- [Exécutable](#exécutable)
- [Données utilisateur](#données-utilisateur)
- [Structure du dépôt](#structure-du-dépôt)
- [Licence](#licence)

## Fonctionnalités

- Ouverture de fichiers `.ged` et affichage des entités `INDI`, `FAM`, `SOUR`,
  `REPO`, `NOTE`, `OBJE` et `SUBM`.
- Recherche filtrée, insensible à la casse et aux accents, avec tri par nom,
  titre ou identifiant.
- Navigation par pointeurs GEDCOM (`@I1@`, `@F1@`, etc.) et historique
  précédent/suivant.
- Vues détaillées des entités, avec liens entre les références reconnues.
- Fiches Individu avec événements, familles parentes, enfants, notes et galerie
  multimédia; fiche Famille avec enfants, sources, notes et événements.
- Affichage du bloc GEDCOM brut avec coloration syntaxique, indentation
  optionnelle et copie dans le presse-papiers; accès aux blocs `HEAD` et `TRLR`.
- Prévisualisation des images locales avec Pillow.
- Chargement en arrière-plan : une nouvelle session remplace la session active
  uniquement après un chargement réussi.
- Historique des fichiers récents et mémorisation du dernier répertoire utilisé.
- Interface disponible en anglais, français, espagnol, allemand, italien et
  portugais. L'anglais est la langue par défaut; un changement de langue prend
  effet au redémarrage.

## Installation et lancement

### Prérequis

- Python 3 et Tkinter.
- `make` pour utiliser les commandes du projet.

### Dépendances par usage

| Usage | Dépendance | Source / rôle |
| --- | --- | --- |
| Application | `Pillow>=12.0` | `requirements.txt`; prévisualisation des images |
| Interface | Tkinter | Module Python avec dépendance système possible; non installé par `pip` |
| Tests | `unittest` | Bibliothèque standard Python; aucun paquet `pytest` requis |
| Tests sans affichage | Xvfb (`xvfb-run`) | Paquet système facultatif pour exécuter les tests Tkinter en mode headless |
| Développement | `black>=26.0` | Formatage du code, dans `requirements-dev.txt` |
| Génération | `pyinstaller>=6.0` | Création de l'exécutable, dans `requirements-dev.txt` |

`requirements-dev.txt` inclut `requirements.txt`, Black et PyInstaller. Pour
installer uniquement la dépendance Python de l'application :

```bash
python3 -m pip install -r requirements.txt
```

Sous Fedora Linux 44, installe les prérequis système de base avec :

```bash
sudo dnf install python3 python3-pip python3-tkinter make
```

Pour lancer les tests Tkinter sans session graphique, installe Xvfb, qui fournit
la commande `xvfb-run` :

```bash
sudo dnf install xvfb-run
```

Sur Fedora, cette commande installe le paquet RPM `xorg-x11-server-Xvfb`,
fournisseur de l'exécutable `xvfb-run`.

`ripgrep` (`rg`) est facultatif; il permet de rechercher rapidement dans le
code, mais n'est requis ni par l'application ni par les tests :

```bash
sudo dnf install ripgrep
```

Sous Debian ou Ubuntu, le paquet Tkinter s'installe avec :

```bash
sudo apt install python3-tk
```

### Démarrage rapide

La commande crée `.venv` si nécessaire, installe les dépendances de
`requirements-dev.txt`, puis lance l'application :

```bash
make run
```

Le script `run.sh` lance l'application avec `.venv/bin/python` si cet
environnement existe, sinon avec `python3` ou `python`. Il ne procède pas à
l'installation des dépendances. Après installation, l'application peut aussi
être lancée directement :

```bash
.venv/bin/python main.py
```

Au démarrage, le dernier fichier récent est rouvert s'il existe toujours.

## Utilisation

Dans le menu **Fichier**, **Ouvrir un fichier GEDCOM** charge le fichier en mode
tolérant. **Ouvrir et valider un fichier GEDCOM** active le mode strict et refuse
le fichier si les anomalies prises en charge par le validateur sont détectées.
Les fichiers ouverts depuis la liste des récents sont chargés en mode tolérant.

La fenêtre permet de sélectionner un type d'entité, d'ouvrir sa fiche, puis de
suivre les pointeurs cliquables. Le panneau de détail est redimensionnable entre
la fiche et le bloc GEDCOM brut. L'application affiche le temps de chargement et
les messages de journalisation dans son interface.

## Recherche

La recherche s'applique au type d'entité sélectionné. Elle ignore la casse et
les accents : `cretel` trouve aussi `crétel`, `Crétel` et `Cretel`. La liste est
mise à jour après une courte temporisation afin d'éviter les recalculs à chaque
frappe.

| Type | Champs recherchés |
| --- | --- |
| `INDI` | Pointeur et `NAME` |
| `FAM` | Pointeur et noms des individus `HUSB`, `WIFE` et `CHIL` référencés |
| `SOUR` | Pointeur et `TITL` |
| `REPO` | Pointeur et `NAME` |
| `NOTE` | Pointeur et texte |
| `OBJE` | Pointeur, `TITL` et `FILE` |
| `SUBM` | Pointeur, `NAME` et `EMAIL` |

Les pointeurs sont triés numériquement lorsque c'est possible. Le tri par nom ou
titre dépend des données de l'entité et de ses références.

## Formats et limites

### Lecture et encodage

Les fichiers sont décodés en UTF-8, avec ou sans BOM. La valeur `HEAD.CHAR` est
vérifiée en mode strict pour les règles GEDCOM prises en charge, mais ne choisit
pas le décodeur. Les séquences qui ne sont pas valides en UTF-8 sont remplacées;
leur nombre est signalé dans le journal. Les espaces répétés dans les valeurs
sont préservés.

### Validation stricte

Le mode strict contrôle notamment la structure des lignes et des enregistrements,
les pointeurs requis, les références connues et certains contextes de tags. Pour
un en-tête déclaré GEDCOM 5.5.1, il vérifie aussi la présence, l'unicité et la
validité de `HEAD.SOUR`, `HEAD.CHAR` et `HEAD.SUBM`, ainsi que plusieurs règles
sur `HEAD.GEDC`, `VERS` et `FORM`.

Cette validation est ciblée et ne garantit pas la conformité complète au
standard GEDCOM. En mode tolérant, les anomalies sont signalées dans le journal
et le chargement continue lorsque c'est possible.

### Mémoire

Le fichier est chargé intégralement en mémoire. Les données optionnelles et
certains arbres d'événements sont construits à la demande pour réduire les
allocations initiales, mais la mémoire nécessaire augmente avec la taille du
GEDCOM. Utilise le benchmark ci-dessous sur tes propres fichiers pour mesurer
leur coût dans ton environnement.

## Développement

Créer l'environnement virtuel et installer Pillow, PyInstaller et Black :

```bash
make install
```

Les dépendances d'exécution sont dans `requirements.txt`; les dépendances de
développement sont dans `requirements-dev.txt`.

Commandes disponibles :

| Commande | Action |
| --- | --- |
| `make run` | Installer les dépendances et lancer l'application |
| `make test` | Installer les dépendances et exécuter les tests |
| `make lint` | Compiler les fichiers Python pour vérifier leur syntaxe |
| `make format` | Formater les sources Python avec Black |
| `make dist` | Construire l'application avec PyInstaller |
| `make clean` | Supprimer `.venv`, `build`, `dist` et les `__pycache__` |

## Tests

Sur une machine avec un affichage disponible :

```bash
make test
```

Ou, après installation des dépendances :

```bash
.venv/bin/python -m unittest discover -s tests
```

En environnement Linux sans affichage, exécute la suite Tkinter sous Xvfb :

```bash
xvfb-run --auto-servernum .venv/bin/python -m unittest discover -s tests
```

La CI compile les sources, vérifie le format avec Black, exécute les tests sous
Xvfb et construit l'application PyInstaller.

## Benchmarks

Le benchmark mesure le temps de chargement, la recherche et les allocations
Python suivies par `tracemalloc`. Ces allocations ne représentent pas toute la
mémoire résidente du processus et les temps dépendent de la machine.

Lancer les scénarios synthétiques par défaut (10 000, 50 000 et 100 000
individus) :

```bash
python3 benchmarks/benchmark_search.py
```

Mesurer un fichier existant sans afficher son chemin ni ses valeurs GEDCOM :

```bash
python3 benchmarks/benchmark_search.py --file /path/to/family.ged --repeats 1
```

Ajouter des familles ou des enregistrements auxiliaires :

```bash
python3 benchmarks/benchmark_search.py --sizes 100000 --families 50000 --repeats 1
python3 benchmarks/benchmark_search.py --sizes 10000 --other-entities 10000 --events-per-source 2 --repeats 1
```

Options de données synthétiques :

| Option | Données ajoutées |
| --- | --- |
| `--families` | Nombre de familles reliées aux individus |
| `--other-entities` | Ce nombre d'enregistrements `NOTE`, `SOUR`, `REPO`, `SUBM` et `OBJE` |
| `--texts-per-individual`, `--notes-per-individual` | Textes ou notes avec continuation |
| `--occupations-per-individual`, `--properties-per-individual` | Occupations datées ou tags `PROP` |
| `--fams-per-individual`, `--obje-per-individual` | Références aux familles ou médias; nécessitent respectivement `--families` ou `--other-entities` |
| `--events-per-family`, `--events-per-source` | Événements familiaux `MARR` ou événements `DATA/EVEN` dans les sources |
| `--metadata-per-source` | Notes, références `SOUR` et `REFN`; nécessite `--other-entities` |

`--file` ne peut pas être combiné avec les options qui génèrent des données
synthétiques. `--query` et `--repeats` permettent de régler la recherche
mesurée; consulte `python3 benchmarks/benchmark_search.py --help` pour la liste
complète des paramètres.

## Exécutable

Construire une version autonome avec PyInstaller :

```bash
make dist
```

Le résultat est placé dans `dist/`.

## Données utilisateur

L'application conserve les préférences, la taille de la fenêtre, le dernier
répertoire et la liste des fichiers récents dans `~/.gedcom_viewer.json`. Les
journaux sont écrits dans `~/.gedcom_viewer.log`.

## Structure du dépôt

```text
.
├── benchmarks/   mesures de recherche et de mémoire
├── controllers/  orchestration et logique applicative
├── gedcom/       parser et modèles métier
├── tests/        tests unitaires et tests Tkinter
├── ui/           interface, traductions et vues
├── main.py       point d'entrée
└── Makefile      commandes de développement et de build
```

Le chargement est coordonné par `ui/load_coordinator.py`. Un thread de travail
construit un nouvel `AppController` via les contrôleurs et le service GEDCOM;
la nouvelle session est publiée dans Tkinter uniquement après succès. En cas
d'erreur, la session courante reste disponible.

## Licence

Aucun fichier de licence n'est présent dans le dépôt. Aucune licence n'est donc
déclarée pour le moment.
