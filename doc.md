# Documentation technique

## Architecture

Le projet suit trois couches :

```text
ui/          Interface Tkinter et vues
controllers/ Orchestration, recherche et résolution des références
gedcom/      Parser GEDCOM et modèles métier
```

Le chargement suit ce flux :

```text
Fichier GEDCOM -> GedcomParser -> GedcomEntity -> modèles métier -> contrôleurs -> vues Tkinter
```

## Interface

- Les types d’entités sont sélectionnés avec les onglets verticaux situés à gauche.
- La liste affiche le nom lisible et l’identifiant GEDCOM dans deux colonnes.
- Un clic sur un en-tête trie la colonne ; un second clic inverse l’ordre.
- Les individus sont triés par `SURN` lorsque le nom GEDCOM contient `/Nom/`.
- Les identifiants sont triés selon leur partie numérique, par exemple `@I2@` avant `@I10@`.
- Les formulaires longs disposent d’un défilement vertical.
- Le bloc GEDCOM brut est affiché en lecture seule et son contenu peut être copié.
- Le menu `Fichier` regroupe les commandes d’inspection et de navigation dans des sous-menus.
- `Ouvrir un fichier GEDCOM` utilise le mode tolérant ; `Ouvrir et valider un fichier GEDCOM` utilise le mode strict.
- `Fichier > Effacer la liste des fichiers récents` vide l’historique enregistré après confirmation ; les fichiers GEDCOM ne sont jamais supprimés.

## Formulaires

Les vues spécialisées couvrent `INDI`, `FAM`, `SOUR`, `REPO`, `NOTE`, `OBJE` et `SUBM`.

Les vues Famille, Source, Dépôt et Note affichent les champs métier connus ainsi que des champs GEDCOM complémentaires lorsque le fichier en contient. Les références disponibles sont présentées avec leur libellé associé et restent navigables par clic.

## Dépendances

- Python 3
- Tkinter
- Pillow pour l’aperçu des images multimédia, installé par `make install`
- PyInstaller et Black pour la distribution et le formatage

Préparer l’environnement :

```bash
make install
```

## Validation

Exécuter les tests :

```bash
python3 -m unittest discover -s tests
```

Dernier résultat vérifié : `81 tests`, `OK`.

Le chargement standard reste tolérant. La validation stricte est disponible
avec l’API Python et refuse les anomalies structurelles détectées :

```python
parser.load("fichier.ged", strict=True)
```

Le temps de chargement est affiché dans la barre de statut de l’application.

Vérifier la syntaxe :

```bash
make lint
```

Construire l’exécutable :

```bash
make dist
```
