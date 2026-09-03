# Diagrammes de flux GEDCOM Viewer

Les diagrammes décrivent le fonctionnement actuel du parser, des contrôleurs et de l’interface.

## PHASE 1 : Initialisation & Chargement (Le Cycle de Lecture)

**Objectif :** Transformer le texte en objets indexés.

```mermaid
flowchart TD
    start((Start));
    
    %% UI & Service
    start --> A1[UI: Call Service.load_file()];
    A1 --> A2[GedcomService: Init Parser];
    
    %% Parsing Core
    A2 --> A3[Parser: Lire ligne par ligne];
    A3 --> A4{Ligne valide?};
    A4 -- Yes --> A5[Create Entity];
    A5 --> A6[Store Entity];
    A4 -- No --> A7[Journaliser et ignorer];
    A6 --> A3;
    A7 --> A3;
    A3 --> A8{Toutes lignes traitées?};
    A8 -- Yes --> A9[Parser: Parsing Complete];
    
    A9 --> A10{Mode strict?};
    A10 -- Oui --> A11[Valider la structure];
    A11 --> A12{Anomalies détectées?};
    A12 -- Oui --> A13[Refuser le chargement];
    A13 --> A18((End Load));
    A10 -- Non --> A14[Controller: Boucle de construction];
    A12 -- Non --> A14;

    %% Construction
    A14 --> A15[Instancier Modele];
    A15 --> A16[Stocker Objet];
    A16 --> A17[Construction Terminee];
    A17 --> A18;
```

---

## PHASE 2 : Interaction Utilisateur (La Consultation)

**Objectif :** Récupérer et afficher les détails d'un objet spécifique.

```mermaid
flowchart TD
    start((Start));
    B1[UI: Select Pointer];
    B1 --> B2[UI appelle Controller.get_entity(pointer)];
    
    B2 --> B3[Controller -> Service: Requête entité];
    B3 --> B4[Service -> Parser: Récupérer entité brute];
    B4 --> B5[Controller -> Objet modèle];
    
    B5 --> B6[Controller: Traiter Objet];
    B6 --> B7[UI: Enregistrer Historique];
    B7 --> B8[UI: Determiner Type Entity];
    B8 --> B9[UI: Selectionner Vue];
    B9 --> B10[Vue: Afficher Données];
    B10 --> end((End Consultation));
```

---

## PHASE 3 : Recherche & Navigation (L'Exploration)

**Objectif :** Filtrer rapidement le catalogue d'objets en mémoire.

```mermaid
flowchart TD
    start((Start));
    C1[UI: Saisie de la Query];
    C1 --> C2[UI appelle Controller.search_individuals(query)];
    
    subgraph Controller
        C2 --> C3[Controller: Iterer sur objets chargés];
        C3 --> C4{Match trouve?};
        C4 -- Yes --> C5[Ajouter au filtre];
        C4 -- No --> C6[Passer objet suivant];
        C5 --> C6;
        C6 --> C7{Tous objets parcourus?};
        C7 -- Yes --> C8[Retour Liste Filtree];
    end
    
    C8 --> C9[UI: Mettre à jour Treeview];
    C9 --> end((End Search));
```
