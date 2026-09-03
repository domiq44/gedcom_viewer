# Analyse du projet GEDCOM Viewer

## Périmètre de l'analyse

Cette analyse porte sur le code Python, les tests, le `Makefile`, le script de lancement et la configuration PyInstaller. Elle décrit l'état observé le 3 septembre 2026.

## Vue d'ensemble

GEDCOM Viewer est une application de bureau Python/Tkinter destinée à ouvrir et explorer des fichiers GEDCOM. Le projet est fonctionnel, modulaire et dispose d'une suite de tests unitaires couvrant le parsing, les contrôleurs et une grande partie de l'interface simulée.

## Architecture

```text
main.py
  -> ui.main_window.GedcomViewer
      -> controllers.app_controller.AppController
          -> controllers.gedcom_service.GedcomService
              -> gedcom.parser.GedcomParser
          -> EntityController
          -> SearchController
          -> PresentationController
      -> ui.views/*
```

### Responsabilités principales

| Composant | Rôle |
|---|---|
| `gedcom/parser.py` | Lit le fichier, conserve les lignes brutes et crée un index des entités par type et pointeur. |
| `gedcom/models/` | Transforme les entités brutes en objets `Individual`, `Family`, `Source`, `Repository`, `Note`, `MultimediaObject` et `Submitter`. |
| `controllers/gedcom_service.py` | Encapsule le chargement et l'accès au parser. |
| `controllers/entity_controller.py` | Construit les modèles métier et fournit les recherches spécialisées. |
| `controllers/search_controller.py` | Gère les types affichés, le filtrage, le tri et les libellés. |
| `controllers/presentation_controller.py` | Résout les pointeurs et prépare le contexte des vues. |
| `ui/main_window.py` | Coordonne la fenêtre principale, les listes, la navigation et l'historique. |
| `ui/views/` | Affiche les fiches détaillées des différents types GEDCOM. |

## Fonctionnalités présentes

- Ouverture de fichiers GEDCOM.
- Conservation et affichage du contenu brut avec coloration syntaxique.
- Support des entités `INDI`, `FAM`, `SOUR`, `REPO`, `NOTE`, `OBJE` et `SUBM`.
- Recherche instantanée et tri des entités.
- Tri numérique des pointeurs tels que `@I2@` et `@I10@`.
- Navigation entre les pointeurs GEDCOM.
- Historique précédent/suivant.
- Gestion des fichiers récemment ouverts.
- Affichage de l'en-tête `HEAD` et du trailer `TRLR`.
- Prévisualisation d'images locales lorsque Pillow est installé.
- Journalisation dans `~/.gedcom_viewer.log`.
- Interface avec zones de texte et formulaires défilants.

## Points forts

1. La séparation parser, modèles, contrôleurs et vues est claire.
2. Le parser conserve le bloc brut, ce qui permet de comparer les données interprétées avec leur représentation d'origine.
3. Les recherches par pointeur et par attribut sont simples à suivre.
4. La résolution centralisée des pointeurs facilite la navigation entre fiches.
5. Les tests couvrent plusieurs cas GEDCOM délicats, notamment `CONC`, `CONT`, les sous-tags imbriqués et les blocs `HEAD`/`TRLR`.

## Défauts confirmés

### 1. Les notes des sources ne sont pas stockées

Dans `gedcom/models/source.py`, deux branches traitent `tag == "NOTE"`. La première affecte `self.text`, ce qui rend la seconde inaccessible. Une note de source se retrouve donc dans `source.text` et jamais dans `source.notes`.

### 2. Un tag `DEAT` est toujours marqué comme confirmé

Dans `gedcom/models/individual.py`, la présence du tag `DEAT` positionne `death_confirmed` à `True`, même lorsque le tag ne contient pas la valeur `Y`. Le modèle ne distingue donc pas l'existence d'un événement de son niveau de confirmation.

### 3. Les erreurs de parsing peuvent passer inaperçues

Les lignes malformées sont ignorées par `gedcom/parser.py`. La lecture utilise également `errors="replace"`, ce qui remplace les caractères invalides sans avertissement explicite. Le résultat peut être incomplet sans que l'utilisateur en soit informé.

### 4. Plusieurs erreurs d'affichage sont masquées

Certaines vues utilisent `except Exception: pass` lors de la résolution des pointeurs. Une erreur de modèle ou de callback peut ainsi produire un affichage incomplet sans trace exploitable.

### 5. Les gros fichiers sont chargés entièrement en mémoire

Le parser conserve toutes les lignes, puis `EntityController` construit tous les modèles au chargement. Cette stratégie est adaptée aux fichiers courants, mais peut ralentir l'ouverture et augmenter fortement la mémoire utilisée pour une généalogie volumineuse.

### 6. Le modèle d'événement n'est pas implémenté

`gedcom/models/event.py` est vide. Les événements familiaux sont actuellement représentés par des dictionnaires dans `Family`, sans classe métier dédiée.

## Tests et validation

La commande de test est :

```bash
python3 -m unittest discover -s tests -v
```

Résultat de la dernière validation :

- 69 tests exécutés.
- 69 tests réussis.
- Tous les fichiers Python compilent avec `py_compile`.

### Couverture manquante

- Cas d'encodage invalide et signalement des lignes ignorées.
- Notes de sources et sémantique précise de `DEAT`.
- Fichiers GEDCOM de très grande taille.
- Tests des erreurs de résolution dans les vues.
- Installation et fonctionnement avec ou sans Pillow.
- Tests de construction PyInstaller.

## Dépendances et exécution

| Élément | Utilisation |
|---|---|
| Python 3 | Langage principal |
| Tkinter | Interface graphique |
| Pillow | Prévisualisation des images, installé par `make install` |
| unittest | Tests intégrés à Python |
| Black | Formatage |
| PyInstaller | Génération de l'exécutable |

Les principales cibles du `Makefile` sont `make test`, `make lint`, `make run`, `make format` et `make dist`. Le script `run.sh` lance directement `main.py` avec l'interpréteur Python disponible.

## Priorités recommandées

1. Corriger le traitement des notes dans `Source` et ajouter un test de régression.
2. Clarifier la sémantique de `DEAT` et tester les variantes `DEAT` et `DEAT Y`.
3. Remplacer les exceptions silencieuses par des logs ciblés ou des erreurs contrôlées.
4. Signaler les lignes GEDCOM ignorées et les remplacements d'encodage.
5. Évaluer un chargement différé ou une stratégie de limitation pour les très gros fichiers.
6. Introduire un modèle `Event` seulement si cela apporte une vraie valeur à la gestion des événements aujourd'hui stockés sous forme de dictionnaires.

## Conclusion

Le projet fournit une base fonctionnelle et bien découpée pour explorer des fichiers GEDCOM. Les tests actuels sont entièrement verts, mais ils ne couvrent pas encore plusieurs règles métier importantes. Les corrections prioritaires concernent la fidélité des données interprétées, la visibilité des erreurs et la disponibilité explicite de la prévisualisation multimédia.
