# 📊 Analyse Complète du Projet GEDCOM Viewer

## Vue d'ensemble

**GEDCOM Viewer 5.5.1** est une application desktop Python + Tkinter pour visualiser et explorer des fichiers GEDCOM (format standardisé pour les données généalogiques). L'application compte environ **3 900 lignes de code** réparties en trois couches architecturales.

---

## 🏗️ Architecture et Structure

### **Couches Applicatives**

```
┌─────────────────────────────────────┐
│        UI (ui/)                     │ ← Tkinter GUI
├─────────────────────────────────────┤
│   Controllers (controllers/)         │ ← Orchestration & logique métier
├─────────────────────────────────────┤
│   GEDCOM Models (gedcom/)           │ ← Parser & modèles de données
└─────────────────────────────────────┘
```

### **Composants Principaux**

| Module | Responsabilité |
|--------|-----------------|
| **gedcom/parser.py** | Analyse les fichiers .ged ligne par ligne, crée les entités brutes |
| **gedcom/models/** | 8 fichiers définissant les modèles métier (Individual, Family, Source, Repository, etc.) |
| **controllers/gedcom_service.py** | Charge les fichiers, gère l'index des entités |
| **controllers/entity_controller.py** | Récupère les objets par pointeur GEDCOM (@I1@, @F1@, etc.) |
| **controllers/search_controller.py** | Filtre par type d'entité, recherche par texte |
| **controllers/presentation_controller.py** | Formate les informations pour l'affichage |
| **ui/main_window.py** | Fenêtre principale Tkinter |
| **ui/views/** | 7 vues détaillées (Individual, Family, Source, Repository, Note, Multimedia, Submitter) |
| **ui/menus.py** | Barre de menu (Fichier, Récents, Affichage) |
| **ui/syntax_highlighter.py** | Coloration syntaxique du code GEDCOM brut |
| **ui/themes.py** | Thème moderne Tkinter |

---

## 🎯 Fonctionnalités

### ✅ Implémentées

- ✓ Chargement de fichiers GEDCOM (.ged)
- ✓ Sélection par onglets verticaux (INDI, FAM, SOUR, REPO, NOTE, OBJE, SUBM)
- ✓ Liste en deux colonnes avec tri par nom ou identifiant
- ✓ Tri des individus par `SURN` et tri numérique des identifiants
- ✓ Recherche instantanée dans la liste des entités
- ✓ Navigation par pointeurs GEDCOM
- ✓ Affichage du bloc GEDCOM brut avec coloration syntaxique
- ✓ Navigation historique (précédent/suivant)
- ✓ Menu des fichiers récents
- ✓ Vues détaillées pour 7 types d'entités
- ✓ Prévisualisation d'images multimédia
- ✓ Journalisation locale (`~/.gedcom_viewer.log`)
- ✓ Panneau de statut avec dernière erreur
- ✓ Défilement vertical des formulaires longs
- ✓ Formulaires enrichis pour Famille, Note, Source et Dépôt

---

## 📂 Distribution des Fichiers

| Répertoire | Fichiers | Lignes | Purpose |
|-----------|----------|--------|---------|
| **gedcom/** | 2 + 8 modèles | ~900 | Parser + modèles métier |
| **controllers/** | 6 fichiers | ~1000 | Orchestration et logique |
| **ui/** | 3 + 7 vues | ~1200 | Interface utilisateur |
| **tests/** | 4 fichiers | ~300 | Tests unitaires |
| **Root** | main.py, Makefile, run.sh | ~100 | Points d'entrée et build |

---

## 🔄 Flux de Données

```
Utilisateur (UI)
       ↓
 GedcomViewer (main_window.py)
       ↓
 AppController (orchestration)
       ↓
GedcomService (charge les fichiers)
       ├→ Parser (parse le fichier)
       ├→ EntityController (indexe les entités)
       └→ SearchController (filtre/recherche)
       ↓
Views (affiche les détails)
```

---

## 🛠️ Outils et Dépendances

| Élément | Détail |
|---------|--------|
| **Langage** | Python 3 |
| **GUI** | Tkinter (stdlib) |
| **Build** | PyInstaller (pour exécutable) |
| **Linting** | Black (formatage) |
| **Testing** | unittest (stdlib) |

### **Commandes Makefile**

- `make install` — installer pip, Tkinter, PyInstaller, Black
- `make run` — lancer l'application
- `make test` — exécuter les tests
- `make format` — formater avec Black
- `make lint` — vérifier la syntaxe
- `make dist` — créer un exécutable standalone

---

## 🧪 Tests

Le projet contient 4 fichiers de test :

- `test_gedcom_parser.py` — Parser et structure GEDCOM
- `test_gedcom_service.py` — Service de chargement
- `test_app_controller.py` — Contrôleur principal
- `test_main_window.py` — Tests UI

**Fichier de test GEDCOM** : `gedcom-test.ged` (exemple de données)

---

## 📊 Types d'Entités Supportés

| Type | Classe | Exemple |
|------|--------|---------|
| **INDI** | `Individual` | John Doe (1900-1980) |
| **FAM** | `Family` | Mariage, enfants |
| **SOUR** | `Source` | Documents sources |
| **REPO** | `Repository` | Archives/dépôts |
| **NOTE** | `Note` | Notes détaillées |
| **OBJE** | `Object` | Photos/documents multimédia |
| **SUBM** | `Submitter` | Personne ayant soumis les données |
| **EVEN** | `Event` | Événements (naissances, décès, etc.) |

---

## 🎨 Interface Utilisateur

### **Organisation**

- **Barre latérale gauche** : onglets verticaux de sélection du type d'entité
- **Panneau gauche** : liste filtrable avec colonnes Nom et Identifiant
- **Panneau central** : bloc GEDCOM brut en lecture seule et colorisé
- **Panneau droit** : vue détaillée avec formulaires scrollables
- **Barre de statut** : Affiche la dernière erreur loggée

### **Thème**

Moderne, couleurs adaptées au type d'entité

---

## ✨ Points Forts

1. **Architecture bien structurée** — Séparation claire UI/Controllers/Models
2. **Extensible** — Facile d'ajouter de nouvelles vues ou entités
3. **Parser robuste** — Gère les variations GEDCOM
4. **Recherche performante** — Filtrage en temps réel
5. **Documentation** — README, SCHEMA.md, commentaires de code
6. **Logging** — Traçabilité des erreurs

---

## ⚠️ Observations et Améliorations Possibles

| Domaine | Observation |
|---------|------------|
| **Dépendances** | Tkinter, Pillow recommandé pour les images, PyInstaller et Black pour le développement |
| **Tests** | Couverture modérée (4 fichiers test) |
| **Documentation** | `doc.md` et `SCHEMA.md` semblent incomplets/en chantier |
| **Erreurs** | Utiliser `make lint` pour identifier les problèmes Python |
| **Performance** | Pas de cache/index pour très gros fichiers GEDCOM |
| **Validation** | Pas de validation stricte du GEDCOM 5.5.1 spec |

---

## 📋 Résumé Exécutif

**GEDCOM Viewer** est un outil bien architécturé et modulaire pour explorer des fichiers généalogiques GEDCOM. Le projet suit une stratégie en trois couches claire, facilite l'extension future et propose déjà une interface utilisateur complète avec 7 types de vues spécialisées.

Les domaines d'amélioration concernent principalement la couverture de tests, la validation stricte du format GEDCOM, et l'optimisation pour les très gros fichiers.

**Tests** : 61 tests unitaires, tous validés au dernier contrôle
**Langages** : Python 3, Tkinter
**Licence/État** : Application fonctionnelle (v5.5.1)

