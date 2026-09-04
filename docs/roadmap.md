# Feuille de route

## Objectif

Donner une trajectoire claire pour faire évoluer GEDCOM Viewer sans casser
l’architecture existante ni perdre la simplicité d’usage actuelle.

## Priorité 1 — stabiliser le chargement asynchrone

### Statut

Terminée.

### Réalisations

- construction d’un `AppController` isolé dans le thread de travail ;
- publication de la nouvelle session uniquement après succès ;
- conservation de l’ancienne session en cas d’erreur ;
- gestion de la fermeture de la fenêtre et des résultats tardifs ;
- ajout de tests d’intégration et de cinq tests unitaires dédiés au chargement
  asynchrone.

## Priorité 2 — améliorer la maintenabilité de l’interface

### Statut

En cours — refactor UI partiellement terminé.

### Réalisations

- isolation de la coordination du chargement dans `ui/load_coordinator.py` ;
- extraction du panneau de recherche et de liste dans `ui/entity_list_panel.py` ;
- extraction de la barre de navigation dans `ui/navigation_bar.py` ;
- extraction du sélecteur de type d’entité dans `ui/entity_type_panel.py` ;
- extraction du panneau de contenu et vues détaillées dans `ui/detail_panel.py` ;
- mise en place d’un debounce de 100 ms sur la recherche côté interface ;
- réduction de la logique UI dans `ui/main_window.py`.

### Objectif interface

Rendre la fenêtre principale plus facile à maintenir et à faire évoluer.

### Actions interface

- extraire les sous-parties de la fenêtre en composants plus petits ;
- isoler la coordination du chargement dans `ui/load_coordinator.py` ;
- isoler le panneau de recherche et de liste dans `ui/entity_list_panel.py` ;
- isoler la barre de navigation dans `ui/navigation_bar.py` ;
- séparer la logique de recherche, de tri et de navigation ;
- limiter les recalculs de recherche avec un debounce côté interface ;
- isoler les vues détaillées derrière une API cohérente ;
- limiter la logique UI dans `ui/main_window.py`.

### Bénéfice interface

- code plus lisible ;
- moins de couplage ;
- ajout de fonctionnalités plus simple.

## Priorité 3 — gérer les gros GEDCOM plus proprement

### Objectif performance

Réduire le coût mémoire et améliorer la scalabilité.

### Actions performance

- identifier les points de chargement en mémoire complète ;
- introduire des structures d’index plus compactes ;
- étudier un chargement partiel ou paresseux pour les gros fichiers ;
- conserver une API stable pour les contrôleurs existants.

### Bénéfice performance

- meilleure tolérance aux fichiers volumineux ;
- plus d’aisance dans les cas de grande généalogie ;
- réduction des risques de saturation mémoire.

## Priorité 4 — enrichir la validation GEDCOM

### Objectif validation

Aller au-delà des anomalies structurelles de base.

### Actions validation

- formaliser les règles de validation GEDCOM ;
- distinguer les erreurs de structure et les erreurs de sémantique ;
- exposer des diagnostics plus explicites dans l’interface ;
- étendre la couverture de tests sur les cas non conformes.

### Bénéfice validation

- meilleure fiabilité du chargement ;
- plus de confiance pour les fichiers réels ;
- meilleure qualité des messages utilisateur.

## Priorité 5 — renforcer la robustesse des vues et des références

### Objectif robustesse

Rendre l’application plus stable face aux données incomplètes ou mal formées.

### Actions robustesse

- sécuriser davantage les résolutions de pointeurs ;
- traiter proprement les entités inconnues ou manquantes ;
- normaliser les messages d’erreur autour des liens brisés ;
- augmenter la couverture des scénarios de navigation.

### Bénéfice robustesse

- moins de bugs sur les fichiers hétérogènes ;
- meilleure expérience dans les cas limites ;
- plus de confiance sur les liens internes.

## Priorité 6 — automatiser la qualité du projet

### Objectif automatisation

Rendre les validations reproductibles pour les futures évolutions.

### Actions automatisation

- ajouter une CI exécutant les tests et la compilation syntaxique ;
- exécuter les tests Tkinter en environnement headless ;
- vérifier la construction PyInstaller ;
- documenter les conventions de développement.

## Plan d’exécution recommandé

1. Extraire progressivement les responsabilités de `ui/main_window.py`.
2. Ajouter les benchmarks mémoire et recherche.
3. Borner l’historique et optimiser la recherche si les mesures le justifient.
4. Enrichir la validation GEDCOM avec des diagnostics séparés par catégorie.
5. Mettre en place la CI et fiabiliser les commandes du `Makefile`.

## Conclusion

Le chargement asynchrone est stabilisé et couvert par les tests. La suite logique
porte désormais sur la maintenabilité de l’interface, la mémoire des gros fichiers,
la validation GEDCOM et l’automatisation de la qualité.
