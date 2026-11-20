# Préférences et données utilisateur

L'application conserve dans `~/.gedcom_viewer.json` :

- la taille de la fenêtre ;
- l'état des cases « Indenter » et « Montrer la vue » ;
- le dernier répertoire utilisé ;
- la liste des fichiers récents ;
- le thème et la langue retenus ;
- l'âge maximal pour les personnes décédées (`max_age_for_deceased`, 110 ans par défaut) ;
- la dernière entité sélectionnée par type d'entité.

Les journaux sont écrits dans `~/.gedcom_viewer.log`.

Les états des cases sont restaurés au lancement suivant. Si aucune préférence
n'a encore été enregistrée, « Indenter » et « Montrer la vue » sont cochés et
« Montrer GEDCOM » est décoché par défaut.
