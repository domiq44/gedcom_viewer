# Analyse du projet GEDCOM Viewer

## Périmètre

Analyse réalisée le 3 septembre 2026 à partir du code Python, des tests, du `Makefile`, de `run.sh` et de la configuration PyInstaller. Les autres documents du dépôt n'ont pas été utilisés comme source d'information.

## Vue d'ensemble

GEDCOM Viewer est une application de bureau Python/Tkinter permettant d'ouvrir, rechercher et explorer des fichiers GEDCOM. Le projet est fonctionnel et organisé en couches distinctes : parsing, modèles métier, contrôleurs et interface utilisateur.

## Architecture

```text
main.py
  -> ui.main_window.GedcomViewer
      -> controllers.app_controller.AppController
          -> GedcomService -> GedcomParser
          -> EntityController
          -> SearchController
          -> PresentationController
      -> ui.views/*
```

| Composant | Responsabilité |
|---|---|
| `gedcom/parser.py` | Lecture du fichier, découpage en blocs, indexation par type et pointeur, extraction des valeurs et continuations. |
| `gedcom/models/` | Conversion des blocs bruts en modèles `Individual`, `Family`, `Source`, `Repository`, `Note`, `MultimediaObject` et `Submitter`. |
| `controllers/gedcom_service.py` | Encapsulation du parser et accès aux données chargées. |
| `controllers/entity_controller.py` | Construction et indexation des modèles métier. |
| `controllers/search_controller.py` | Recherche, tri, formatage et libellés des entités. |
| `controllers/presentation_controller.py` | Résolution des pointeurs et préparation du contexte d'affichage. |
| `ui/main_window.py` | Fenêtre principale, listes, chargement, navigation et historique. |
| `ui/views/` | Vues spécialisées pour les sept types d'entités pris en charge. |

## Fonctionnalités observées

- Chargement de fichiers GEDCOM et affichage du bloc brut.
- Support des types `INDI`, `FAM`, `SOUR`, `REPO`, `NOTE`, `OBJE` et `SUBM`.
- Recherche instantanée et tri par nom, titre ou identifiant.
- Tri numérique des pointeurs comme `@I2@` et `@I10@`.
- Navigation entre pointeurs GEDCOM et historique précédent/suivant.
- Gestion des fichiers récents.
- Extraction et affichage de `HEAD` et `TRLR`.
- Coloration syntaxique du contenu GEDCOM brut.
- Prévisualisation des images locales avec Pillow.
- Journalisation locale et affichage du dernier message dans la barre de statut.
- Affichage du temps de chargement du GEDCOM dans cette barre de statut.
- Formulaires défilants pour les données détaillées.

## Corrections déjà réalisées

- Les notes `NOTE` des sources sont conservées dans `Source.notes`, avec leurs continuations, au lieu d'être perdues dans une branche inaccessible.
- `Individual.death_confirmed` n'est activé par la valeur `Y` du tag `DEAT` ou par un sous-tag `Y`, et non par la seule présence de `DEAT`.
- Les lignes GEDCOM malformées sont enregistrées dans `GedcomParser.malformed_lines` et journalisées.
- Les caractères remplacés par `errors="replace"` sont comptabilisés dans `encoding_replacements` et journalisés.
- Pillow est installé par `make install` avec PyInstaller et Black.
- Le temps de chargement est mesuré avec `time.perf_counter()` et publié dans le log de succès.

## Défauts et limites encore présents

### 1. Chargement entièrement en mémoire

Le parser conserve toutes les lignes et `EntityController` construit immédiatement tous les modèles. Une mesure synthétique sur 100 000 individus donne environ 1,45 seconde et 169 Mo de mémoire maximale. Le temps est acceptable, mais la mémoire consommée justifie une future conception d'index compact ou de chargement différé. Cette évolution devra préserver l'API actuelle, qui expose des listes et objets métier matérialisés.

### 2. Exceptions encore silencieuses dans certaines vues

Les résolveurs de noms et de pointeurs de plusieurs vues utilisent encore `except Exception: pass`. Une erreur peut donc produire un libellé incomplet sans trace exploitable. Ce point doit être traité avec des logs ciblés ou des erreurs contrôlées.

### 3. Événements représentés par des dictionnaires

`gedcom/models/event.py` est vide. Les événements de `Family` sont stockés sous forme de dictionnaires, ce qui limite le typage et la réutilisation. Une classe `Event` ne doit être ajoutée que si le domaine nécessite davantage de comportement.

### 4. Modèle `Submitter` limité

`Submitter` conserve un seul téléphone et un seul email. Si un fichier contient plusieurs tags `PHON` ou `EMAIL`, les valeurs précédentes sont remplacées.

### 5. Mariages multiples peu exploités

`Family` collecte plusieurs événements de mariage dans `marriages`, mais l'affichage met surtout en avant `marriage_date` et `marriage_place`. Les mariages supplémentaires ne sont pas présentés comme tels dans la vue.

### 6. Validation GEDCOM non stricte

Le parser est volontairement tolérant : certaines lignes invalides sont ignorées et les fichiers incomplets peuvent être chargés. Les anomalies sont maintenant signalées, mais aucune validation complète de conformité GEDCOM n'est réalisée.

### 7. Gestion d'erreurs périphériques silencieuse

La sauvegarde de la liste des fichiers récents et la mise à jour du widget de statut ignorent certaines exceptions. Cela protège l'interface, mais peut masquer un problème d'accès disque ou de widget.

## Tests et validation

Commande utilisée :

```bash
python3 -m unittest discover -s tests
```

Dernier résultat :

- 70 tests exécutés.
- 70 tests réussis.
- Compilation Python réussie sur les fichiers du projet.
- `git diff --check` réussi.

La suite couvre principalement le parser, les services, les contrôleurs et des scénarios Tkinter. Les principales lacunes concernent les gros fichiers réels, les valeurs multiples de `Submitter`, les mariages multiples, la validation GEDCOM stricte et les erreurs périphériques de l'interface.

## Dépendances et exécution

| Élément | Utilisation |
|---|---|
| Python 3 | Langage principal |
| Tkinter | Interface graphique |
| Pillow | Prévisualisation des images, installé par `make install` |
| `unittest` | Tests |
| Black | Formatage |
| PyInstaller | Exécutable autonome |

Les cibles principales sont `make test`, `make lint`, `make run`, `make format` et `make dist`. `run.sh` lance l'application avec Python 3 ou Python si Python 3 n'est pas disponible.

## Priorités recommandées

1. Réduire la mémoire utilisée par les gros fichiers sans casser l'API des contrôleurs.
2. Remplacer les exceptions silencieuses des vues et opérations périphériques par des logs ciblés.
3. Ajouter des tests pour les valeurs multiples de `Submitter` et les mariages multiples.
4. Décider du niveau de validation GEDCOM attendu et ajouter des diagnostics adaptés.
5. Introduire un modèle `Event` uniquement si les besoins métier le justifient.

## Conclusion

Le projet fournit une base fonctionnelle, testée et correctement structurée pour explorer des données GEDCOM. Les corrections récentes ont amélioré la fidélité des données, la visibilité des anomalies et le suivi du chargement. Les principaux travaux restants concernent la mémoire, la gestion des erreurs encore silencieuses et la couverture des cas GEDCOM multiples ou non conformes.
