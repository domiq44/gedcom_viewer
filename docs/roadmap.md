# Feuille de route

## Objectif

Donner une trajectoire claire pour faire évoluer GEDCOM Viewer sans casser l’architecture existante ni perdre la simplicité d’usage actuelle.

## Priorité 1 — améliorer la maintenabilité de l’interface

### Objectif
Rendre la fenêtre principale plus facile à maintenir et à faire évoluer.

### Actions
- extraire les sous-parties de la fenêtre en composants plus petits
- séparer la logique de recherche, de tri et de navigation
- isoler les vues détaillées derrière une API cohérente
- limiter la logique UI dans `ui/main_window.py`

### Bénéfice
- code plus lisible
- moins de couplage
- ajout de fonctionnalités plus simple

## Priorité 2 — gérer les gros GEDCOM plus proprement

### Objectif
Réduire le coût mémoire et améliorer la scalabilité.

### Actions
- identifier les points de chargement en mémoire complète
- introduire des structures d’index plus compactes
- étudier un chargement partiel ou paresseux pour les gros fichiers
- conserver une API stable pour les contrôleurs existants

### Bénéfice
- meilleure tolérance aux fichiers volumineux
- plus d’aisance dans les cas de grande généalogie
- réduction des risques de saturation mémoire

## Priorité 3 — enrichir la validation GEDCOM

### Objectif
Aller au-delà des anomalies structurelles de base.

### Actions
- formaliser les règles de validation GEDCOM
- distinguer mieux les erreurs de structure et les erreurs de sémantique
- exposer des diagnostics plus explicites dans l’interface
- étendre la couverture de tests sur les cas non conformes

### Bénéfice
- meilleure fiabilité du chargement
- plus de confiance pour les fichiers réels
- meilleure qualité des messages utilisateur

## Priorité 4 — renforcer la robustesse des vues et des références

### Objectif
Rendre l’application plus stable face aux données incomplètes ou mal formées.

### Actions
- sécuriser davantage les résolutions de pointeurs
- traiter proprement les entités inconnues ou manquantes
- normaliser les messages d’erreur autour des liens brisés
- augmenter la couverture des scénarios de navigation

### Bénéfice
- moins de bugs sur les fichiers hétérogènes
- meilleure UX dans les cas limites
- plus de confiance sur les liens internes

## Priorité 5 — préparer l’avenir de la base fonctionnelle

### Objectif
Faire du projet un outil plus durable et plus facile à faire évoluer.

### Actions
- documenter les conventions de développement
- clarifier les interfaces entre couches
- stabiliser les tests autour des cas critiques
- garder le niveau de complexité du projet compatible avec sa taille actuelle

### Bénéfice
- évolution maîtrisée
- moins de régressions
- meilleure contribution de nouveaux développeurs

## Plan d’exécution recommandé

### Phase 1 : stabilisation
- refactorer l’UI sans modifier le comportement
- renforcer les tests autour de la recherche et de la navigation
- corriger les petits défauts de robustesse

### Phase 2 : performance
- réduire la charge mémoire
- optimiser les traitements de recherche et de tri
- garder l’API applicative stable

### Phase 3 : qualité GEDCOM
- enrichir la validation
- améliorer les diagnostics
- couvrir davantage de cas réels

### Phase 4 : évolutivité
- modulariser davantage la couche interface
- sécuriser la structure du projet
- préparer les prochaines fonctionnalités sans rupture

## Conclusion

Le projet est déjà fonctionnel et cohérent. La feuille de route la plus utile n’est pas de “tout réécrire”, mais de consolider les bases existantes en améliorant la maintenabilité, la performance et la qualité de validation.

C’est le bon niveau d’évolution pour un outil de consultation GEDCOM qui a déjà une vraie valeur métier.
