# Diagrammes UML - Système FLOTTE

Ce dossier contient les 4 diagrammes UML complets du système de gestion de flotte automobile FLOTTE.
Les fichiers sont au format PlantUML (.puml).

## 📋 Contenu

### 1. Diagramme de Classes (`01-diagramme-classes.puml`)
**Description :** Représente la structure statique du système avec toutes les entités, leurs attributs, méthodes et relations.

**Éléments inclus :**
- **Entités principales :** Vehicule, Import, Document, Reparation, Vente, Acquereur, Prestataire
- **Entités secondaires :** ChiffreAffaires, Utilisateur, Dashboard, Alerte
- **Attributs complets** pour chaque classe avec types et contraintes
- **Méthodes** principales de chaque classe
- **Relations :** Association, Agrégation, Composition
- **Énumérations :** StatutVehicule, EtatImport, TypeDocument, TypeReparation, Role, etc.

**Relations principales :**
- Vehicule → Import (1 à plusieurs)
- Vehicule → Document (1 à plusieurs)
- Vehicule → Reparation (1 à plusieurs)
- Vehicule → Vente (1 à 0..1)
- Vente → Acquereur (1 à 1)
- Reparation → Prestataire (1 à 1)
- ChiffreAffaires → Vente (1 à plusieurs)

---

### 2. Diagramme de Cas d'Utilisation (`02-diagramme-cas-utilisation.puml`)
**Description :** Représente les fonctionnalités du système du point de vue des utilisateurs.

**Éléments inclus :**
- **Acteurs :** Administrateur, Utilisateur
- **36 cas d'utilisation** organisés en packages :
  - Gestion Véhicules (7 cas)
  - Gestion Imports (6 cas)
  - Gestion Documents (4 cas)
  - Gestion Réparations (3 cas)
  - Gestion Ventes (5 cas)
  - Gestion Financière (4 cas)
  - Tableau de Bord (5 cas)
  - Authentification (2 cas)

**Relations :**
- **Include (<<include>>)** : Relations d'inclusion obligatoire
  - Ex: Ajouter véhicule inclut Se connecter
  - Ex: Enregistrer vente inclut Calculer marge
- **Extend (<<extend>>)** : Relations d'extension conditionnelle
  - Ex: Consulter fiche véhicule étend Consulter parc
  - Ex: Générer facture étend Enregistrer vente
- **Généralisation** : Relations d'héritage entre cas d'usage
  - Ex: Les étapes d'import héritent de Suivre démarches import

---

### 3. Diagramme de Séquence (`03-diagramme-sequence.puml`)
**Description :** Représente les interactions temporelles entre les acteurs et les composants du système pour les scénarios principaux.

**Séquences incluses :**

#### Séquence 1 : Ajout d'un véhicule
- Interaction complète depuis le clic jusqu'à l'enregistrement
- Validation des données
- Création du véhicule et initialisation de l'import
- Gestion des erreurs

#### Séquence 2 : Suivi des démarches d'import
- Consultation des démarches en cours
- Mise à jour d'une étape (douane, homologation, immatriculation, carte grise)
- Création automatique de documents
- Mise à jour du statut véhicule

#### Séquence 3 : Enregistrement d'une vente
- Consultation de la fiche véhicule
- Calcul des coûts et de la marge
- Enregistrement de la vente
- Mise à jour du statut et du chiffre d'affaires

#### Séquence 4 : Consultation tableau de bord
- Chargement parallèle des KPIs
- Récupération activité récente
- Récupération démarches en attente
- Récupération alertes

**Participants :** Interface, Contrôleur, Services métier, Base de données

---

### 4. Diagramme d'Activité (`04-diagramme-activite.puml`)
**Description :** Représente les processus métier et les flux d'activités du système.

**Processus inclus :**

#### Processus 1 : Processus d'import complet
- Flux complet depuis l'ajout du véhicule jusqu'à l'obtention de la carte grise
- 5 partitions principales :
  1. Douane
  2. Homologation (avec branchement COC vs RTI)
  3. Immatriculation
  4. Carte grise
  5. Assurance
- Points de décision et conditions

#### Processus 2 : Processus de vente
- Vérification disponibilité et documents
- Saisie informations vente
- Calcul coûts et marge
- Génération documents (facture, PV livraison)
- Mise à jour CA

#### Processus 3 : Gestion des réparations
- Enregistrement réparation
- Association au véhicule et prestataire
- Mise à jour coûts
- Recalcul marge si véhicule vendu

#### Processus 4 : Gestion des alertes
- Vérification automatique des échéances
- Génération alertes (assurance, CT, démarches)
- Affichage et traitement des alertes

#### Processus 5 : Calcul chiffre d'affaires
- Calcul CA mensuel et annuel
- Calcul marges et pourcentages
- Génération rapports et graphiques

**Éléments utilisés :**
- Activités (actions)
- Décisions (if/else)
- Partitions (groupes d'activités)
- Notes explicatives

---

## 🛠️ Utilisation

### Visualisation des diagrammes

Ces fichiers sont au format **PlantUML** (`.puml`). Pour les visualiser :

1. **En ligne :**
   - Aller sur [PlantUML Online Server](http://www.plantuml.com/plantuml/uml/)
   - Copier-coller le contenu d'un fichier `.puml`
   - Le diagramme sera généré automatiquement

2. **Localement :**
   - Installer PlantUML : `npm install -g node-plantuml`
   - Générer les images : `plantuml *.puml`
   - Ou utiliser un plugin dans votre IDE (VS Code, IntelliJ, etc.)

3. **Avec VS Code :**
   - Installer l'extension "PlantUML"
   - Ouvrir un fichier `.puml`
   - Appuyer sur `Alt+D` pour prévisualiser

### Formats de sortie

PlantUML peut générer :
- PNG (par défaut)
- SVG
- PDF
- LaTeX

---

## 📊 Résumé des entités

| Entité | Attributs principaux | Relations |
|--------|---------------------|-----------|
| **Vehicule** | id, marque, modèle, VIN, année, prixAchat, statut | → Import, Document, Reparation, Vente |
| **Import** | id, dates étapes, état | → Vehicule |
| **Document** | id, type, dates, fichier | → Vehicule |
| **Reparation** | id, date, type, coût | → Vehicule, Prestataire |
| **Vente** | id, dateVente, prixVente, marge | → Vehicule, Acquereur |
| **Acquereur** | id, nom, type | ← Vente |
| **Prestataire** | id, nom, type | ← Reparation |
| **ChiffreAffaires** | id, période, CA, marge | ← Vente |
| **Utilisateur** | id, nom, role | → Vehicule, Dashboard |
| **Dashboard** | KPIs | → Vehicule, Import, Vente, Alerte |
| **Alerte** | id, type, message, dateEcheance | → Vehicule |

---

## 🔗 Relations principales

- **Vehicule** est au centre du système
- **Import** suit le cycle de vie d'un véhicule depuis l'entrée
- **Vente** marque la fin du cycle (statut "Vendu")
- **Document** et **Reparation** enrichissent l'historique du véhicule
- **ChiffreAffaires** agrège les données financières
- **Dashboard** consolide toutes les informations pour la vue d'ensemble

---

## 📝 Notes importantes

- Tous les montants sont en **FCFA** (Franc CFA)
- Les dates sont critiques pour le suivi des démarches et alertes
- Le **VIN** est unique et sert d'identifiant principal
- Les **statuts** permettent de suivre l'état du véhicule dans son cycle de vie
- Les **alertes** sont générées automatiquement selon les échéances

---

## 📅 Version

- **Date de création :** Janvier 2025
- **Version du système :** Maquette v1.0
- **Format :** PlantUML 2.0

---

## 📚 Références

- [Documentation PlantUML](https://plantuml.com/)
- [Guide UML](https://www.uml-diagrams.org/)
- README principal du projet FLOTTE
