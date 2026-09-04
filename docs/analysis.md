# Analyse du projet

## Résumé

GEDCOM Viewer est un outil de lecture et d’exploration de fichiers GEDCOM. Le projet est fonctionnel, bien structuré pour une application desktop Python/Tkinter, et il est centré sur une expérience de consultation plutôt que sur une modification des données.

Le point fort majeur est qu’il ne s’agit pas seulement d’un parser : il combine parsing, modélisation métier, recherche, navigation par pointeurs et interface utilisateur dans une architecture cohérente.

## Ce qui fonctionne bien

### 1. Séparation des responsabilités

Le projet est divisé en couches relativement propres :

- `ui/` pour l’interface
- `controllers/` pour l’orchestration
- `gedcom/` pour le parsing et les modèles
- `tests/` pour la validation fonctionnelle

Cette séparation rend le code plus facile à comprendre et à faire évoluer.

### 2. Gestion GEDCOM solide

Le parser sait :

- lire des fichiers GEDCOM
- identifier les enregistrements de niveau 0
- indexer par type et par pointeur
- signaler les lignes malformées
- gérer les cas de chargement tolérant ou strict

La gestion des références comme `HUSB`, `WIFE`, `CHIL`, `SOUR`, `REPO`, `NOTE` et `OBJE` est particulièrement utile pour l’interface.

### 3. Expérience utilisateur satisfaisante

Le projet propose :

- recherche instantanée
- filtre par type d’entité
- tri numérique des identifiants
- historique de navigation
- affichage du bloc GEDCOM brut
- vues détaillées selon le type
- support multilingue

Cela donne un produit qui a un vrai aspect d’application utilisable, pas seulement une preuve de concept.

## Points faibles

### 1. UI très dense

La classe principale de l’interface dans `ui/main_window.py` est volumineuse. C’est le premier point limite du projet : elle mélange beaucoup de responsabilités.

À long terme, cela rendra le projet plus coûteux à maintenir, surtout si on ajoute des fonctionnalités ou de nouvelles vues.

### 2. Chargement entièrement en mémoire

Le README le note explicitement : le projet charge les données en mémoire intégralement. Ce choix est simple et performant pour des fichiers moyens, mais il devient une limitation pour des GEDCOM très volumineux.

C’est un point à surveiller si le projet doit gérer des bases familiales beaucoup plus importantes.

### 3. Validation GEDCOM partielle

Le mode strict est utile, mais il ne couvre pas toute la conformité GEDCOM. Le projet est fonctionnel et “fort” sur l’usage courant, mais pas encore une validation complète de standard.

Cela est acceptable pour un outil de consultation, mais il faut le garder en tête comme limite fonctionnelle.

### 4. Architecture encore orientée “application monolithique”

L’application est cohérente, mais elle n’a pas encore complètement franchi le pas vers un modèle plus modulaire. La logique de l’interface est encore très proche du reste du système.

## État actuel du projet

### Points de qualité

- bonne séparation des dossiers
- architecture globale cohérente
- logique métier lisible
- tests présents et utiles
- l’application est réellement exploitable

### Points à surveiller

- lourdeur de `ui/main_window.py`
- mémoire pour les gros GEDCOM
- validation GEDCOM standard complète
- potentiel de couplage entre UI et logique métier

### Constats vérifiés

- La suite de tests contient 124 tests et passe intégralement.
- La compilation syntaxique de tous les fichiers Python passe.
- Le parser charge les fichiers en mémoire complète dans `gedcom/parser.py`.
- Le chargement asynchrone construit un contrôleur local dans le thread de travail
  puis le publie dans le thread Tkinter après succès.
- La coordination du chargement est isolée dans `ui/load_coordinator.py`, tandis
  que `ui/main_window.py` conserve l’application du résultat à l’interface.
- Le panneau de recherche et de liste est isolé dans `ui/entity_list_panel.py`,
  tandis que la fenêtre conserve le filtrage métier et la sélection courante.
- La barre de navigation est isolée dans `ui/navigation_bar.py`, tandis que la
  fenêtre conserve la navigation métier et l'historique.
- L'historique de navigation conserve les contextes complets sans limite de taille.
- La recherche renormalise les valeurs à chaque requête, ce qui peut devenir coûteux
  sur de gros volumes.
- L'interface applique désormais un debounce de 100 ms avant de relancer la
  recherche et annule ce callback lors de la fermeture.

Le risque de concurrence initial a été traité : le parser du service actif n'est
plus remplacé depuis le thread de travail. L'ancienne session reste cohérente
pendant le chargement et est conservée en cas d'erreur. Les résultats tardifs sont
ignorés lorsque la fenêtre est en cours de fermeture.

La commande de validation utilisée est :

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests
```

Résultat : `Ran 124 tests ... OK`.

## Recommandations prioritaires

### Priorité 1 : sécuriser le chargement asynchrone

Construire une session complète dans le thread de travail, puis la publier dans
l'interface en une seule opération après succès. Ajouter un test qui vérifie que
l'ancien état reste cohérent pendant le chargement et qu'un échec ne le remplace
pas.

Cette correction est désormais implémentée dans `ui/main_window.py` : le thread
de travail construit un nouvel `AppController` local et transmet son résultat via
la file de messages. Le contrôleur actif n'est remplacé par l'interface qu'après
un chargement réussi ; en cas d'erreur, l'ancien état est conservé.

La suite UI ciblée passe avec 41 tests. Cinq tests unitaires indépendants couvrent
également `LoadCoordinator` : succès, erreur, refus d'un second chargement,
reprogrammation du polling et fermeture avec résultat en attente. Un test UI
vérifie aussi l'annulation et le remplacement du callback de recherche.

### Priorité 2 : mesurer et maîtriser la mémoire

Avant toute refonte du parser, ajouter un benchmark avec plusieurs tailles de
fichiers. Le parser conserve actuellement les lignes, les blocs bruts, les index
et les modèles métier. Selon les mesures, étudier un index plus compact ou un
chargement différé.

### Priorité 3 : borner l'historique et la recherche

Limiter l'historique à un nombre raisonnable d'entrées, ou y stocker seulement les
pointeurs. Construire ensuite un index de recherche normalisé et ajouter un léger
debounce côté interface.

### Priorité 4 : réduire le couplage UI / logique

Il serait bénéfique de découper les responsabilités de la fenêtre principale en composants plus petits :

- panneau de recherche
- liste des entités
- panneau de détail
- navigation
- gestion des paramètres

Cela améliorerait la maintenabilité.

### Priorité 5 : sécuriser la gestion des fichiers volumineux

Le projet mériterait un axe de travail sur :

- chargement paresseux
- index compact
- données calculées à la demande

Même sans changer l’API publique, on peut faire évoluer la façon dont les données sont stockées.

### Priorité 6 : consolider la validation GEDCOM

Le mode strict est une bonne base. L’étape suivante serait d’ajouter des règles de validation plus complètes, avec diagnostics plus explicites pour les fichiers GEDCOM réels.

### Priorité 7 : automatiser la qualité du projet

Ajouter une CI exécutant les tests, la compilation syntaxique, les tests Tkinter
en environnement headless et, si possible, une construction PyInstaller. Mettre à
jour le nombre de tests indiqué dans `README.md` et corriger les diagnostics
Markdown de `docs/roadmap.md`.

## Ordre d'exécution recommandé

1. Corriger l'échange atomique de la session et ajouter le test de régression.
2. Ajouter les benchmarks mémoire et recherche.
3. Borner l'historique et optimiser la recherche si les mesures le justifient.
4. Mettre en place la CI et fiabiliser les commandes du `Makefile`.
5. Extraire progressivement les responsabilités de `ui/main_window.py`.
6. Enrichir la validation GEDCOM avec des diagnostics séparés par catégorie.

## Conclusion

Le projet a une bonne base technique, une architecture pensée, et une fonctionnalité utile. Il n’a pas besoin d’être totalement réécrit, mais il gagnerait nettement à être refactoré un peu plus sur la partie interface et sur la gestion des gros volumes de données.

En l’état, c’est un projet sérieux, fonctionnel et bien orienté vers un besoin réel : lire et consulter des arbres généalogiques de manière claire et fiable.
