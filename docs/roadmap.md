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

Terminée.

### Réalisations

- isolation de la coordination du chargement dans `ui/load_coordinator.py` ;
- extraction du panneau de recherche et de liste dans `ui/entity_list_panel.py` ;
- extraction de la barre de navigation dans `ui/navigation_bar.py` ;
- extraction du sélecteur de type d’entité dans `ui/entity_type_panel.py` ;
- extraction du panneau de contenu et vues détaillées dans `ui/detail_panel.py` ;
- extraction de l’en-tête dans `ui/app_header.py` ;
- extraction de la gestion des fichiers récents dans `ui/file_manager.py` ;
- extraction du menu applicatif dans `ui/application_menu.py` ;
- extraction du navigateur d’entités dans `ui/entity_browser.py` ;
- extraction de la navigation d’entités dans `ui/entity_navigator.py` ;
- extraction de la gestion des vues détaillées dans `ui/entity_view_manager.py` ;
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

Les extractions prévues sont réalisées. La fenêtre principale conserve
l’orchestration de l’application et les transitions entre contrôleurs et vues.

### Bénéfice interface

- code plus lisible ;
- moins de couplage ;
- ajout de fonctionnalités plus simple.

## Priorité 2 bis — corriger les résolveurs figés et enrichir le formulaire Individu

### Statut

Terminée.

### Réalisations

- correction d’un bug où les résolveurs de pointeurs des vues restaient liés à
  l’ancien `AppController` après un chargement asynchrone (remplacement de
  `self.controller`), ce qui rendait silencieusement toutes les résolutions de
  noms inopérantes sans erreur visible ; les résolveurs sont désormais des
  fonctions qui accèdent à `self.controller` au moment de l’appel ;
- ajout de deux onglets en bas du formulaire Individu : **Familles (parent)**
  (liste à deux colonnes nom/identifiant, alimentée par
  `format_entity_display_name`) et **Enfants** (déduits des `FAMS` de
  l’individu) ;
- réutilisation de l’API `format_entity_label` / `format_entity_display_name`
  du `SearchController` plutôt qu’une logique de résolution dupliquée dans les
  vues ;
- `DetailPanel` sépare désormais le bloc GEDCOM brut et le formulaire d’entité
  avec un `PanedWindow` redimensionnable au lieu d’un partage figé à 50/50.

### Bénéfice

- fiabilité des noms affichés après le premier chargement de fichier ;
- ergonomie améliorée pour explorer les familles et enfants d’un individu ;
- panneau de détail redimensionnable selon les besoins de lecture.

## Priorité 3 — gérer les gros GEDCOM plus proprement

### Statut

En cours — première optimisation et mesure réalisées.

### Objectif performance

Réduire le coût mémoire et améliorer la scalabilité.

### Actions performance

- identifier les points de chargement en mémoire complète ;
- lecture normalisée ligne par ligne pour supprimer la copie temporaire des
  lignes brutes ;
- première mesure sur 100 000 lignes : environ 6,5 Mo de pic mémoire ;
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
