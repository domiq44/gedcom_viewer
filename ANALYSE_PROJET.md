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
| --- | --- |
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
- Effacement rapide du filtre de recherche avec le bouton `×`.
- Style du bouton harmonisé avec les couleurs de surface, de séparation et de survol de l'interface.
- Tri numérique des pointeurs comme `@I2@` et `@I10@`.
- Navigation entre pointeurs GEDCOM et historique précédent/suivant.
- Gestion des fichiers récents.
- Extraction et affichage de `HEAD` et `TRLR`.
- Coloration syntaxique du contenu GEDCOM brut.
- Prévisualisation des images locales avec Pillow.
- Journalisation locale et affichage du dernier message dans la barre de statut.
- Affichage du temps de chargement du GEDCOM dans cette barre de statut.
- Chargement GEDCOM en arrière-plan, avec application des résultats dans le thread Tkinter principal.
- Formulaires défilants pour les données détaillées.

## Corrections déjà réalisées

- Les notes `NOTE` des sources sont conservées dans `Source.notes`, avec leurs continuations, au lieu d'être perdues dans une branche inaccessible.
- `Individual.death_confirmed` n'est activé par la valeur `Y` du tag `DEAT` ou par un sous-tag `Y`, et non par la seule présence de `DEAT`.
- Les lignes GEDCOM malformées sont enregistrées dans `GedcomParser.malformed_lines` et journalisées.
- Les caractères remplacés par `errors="replace"` sont comptabilisés dans `encoding_replacements` et journalisés.
- Pillow est installé par `make install` avec PyInstaller et Black.
- Le temps de chargement est mesuré avec `time.perf_counter()` et publié dans le log de succès.
- Les tests UI utilisent la langue active au lieu de textes codés en dur.
- Les objets `GedcomEntity` utilisent `__slots__` pour réduire leur surcharge mémoire.
- `run.sh` utilise `.venv/bin/python` lorsqu'il est disponible.

## Défauts et limites encore présents

### 1. Chargement entièrement en mémoire

Le parser conserve toutes les lignes et `EntityController` construit immédiatement tous les modèles. Une mesure synthétique sur 100 000 individus donne environ 1,45 seconde et 169 Mo de mémoire maximale. `GedcomEntity` utilise désormais `__slots__`, mais la mémoire consommée justifie encore une future conception d'index compact ou de chargement différé. Cette évolution devra préserver l'API actuelle, qui expose des listes et objets métier matérialisés.

Le chargement est maintenant exécuté dans un thread de travail afin d'éviter le gel de l'interface. Tkinter reste manipulé uniquement dans le thread principal.

### 2. Gestion d'erreurs périphériques

Les résolveurs de noms et de pointeurs des vues ainsi que la sauvegarde des fichiers récents journalisent désormais les exceptions tout en conservant un affichage ou un résultat de repli. Le handler UI protège encore sa mise à jour par une exception silencieuse lorsque le widget Tkinter n'est plus disponible, afin d'éviter une récursion du logger pendant la fermeture.

### 3. Validation GEDCOM configurable

Le parser reste tolérant par défaut : les lignes invalides et fichiers incomplets sont signalés, mais peuvent être chargés. La méthode `load(..., strict=True)` refuse désormais les anomalies structurelles détectées, notamment les lignes malformées, les sauts de niveau, les pointeurs dupliqués et l'absence ou la multiplicité de `HEAD`/`TRLR`. Cette validation ne couvre pas encore toutes les règles sémantiques de GEDCOM.

Le menu `Fichier` propose maintenant les deux comportements : l'ouverture
standard reste tolérante et `Ouvrir et valider un fichier GEDCOM` active le mode
strict. Le service charge le nouveau parser avant de le rendre actif, afin qu'un
échec de validation conserve la session précédente.

## Tests et validation

Commande utilisée :

```bash
python3 -m unittest discover -s tests
```

Dernier résultat :

- 94 tests présents dans la suite.
- Compilation Python réussie sur les fichiers du projet.
- `git diff --check` réussi.

La suite couvre principalement le parser, les services, les contrôleurs et des scénarios Tkinter. Les principales lacunes concernent les gros fichiers réels, la validation GEDCOM sémantique et les scénarios de concurrence pendant un chargement.

## Dépendances et exécution

| Élément | Utilisation |
| --- | --- |
| Python 3 | Langage principal |
| Tkinter | Interface graphique |
| Pillow | Prévisualisation des images, installé par `make install` |
| `unittest` | Tests |
| Black | Formatage |
| PyInstaller | Exécutable autonome |

Les cibles principales sont `make test`, `make lint`, `make run`, `make format` et `make dist`. `run.sh` utilise l'interpréteur du venv lorsqu'il existe, puis retombe sur Python 3 ou Python système.

## Priorités recommandées

1. Réduire la mémoire utilisée par les gros fichiers sans casser l'API des contrôleurs.
2. Décider du niveau de validation GEDCOM attendu et ajouter des diagnostics adaptés.

## Conclusion

Le projet fournit une base fonctionnelle, testée et correctement structurée pour explorer des données GEDCOM. Les corrections récentes ont amélioré la fidélité des données, la visibilité des anomalies et le suivi du chargement. Les principaux travaux restants concernent la mémoire, la validation sémantique et la couverture des cas GEDCOM multiples ou non conformes.
