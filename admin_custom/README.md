# Admin Django Personnalisé

Cette application ajoute des fonctionnalités avancées à l'admin Django :

## 🎨 Fonctionnalités

### 1. Graphiques Dynamiques
- Sélection du modèle (Order, Invoice, Payment, Product)
- Choix du champ à analyser
- Types de graphiques : Courbe, Histogramme, Camembert, Donut, Aire
- Fréquences : Jour, Semaine, Mois, Trimestre, Année
- Opérations : Somme, Moyenne, Nombre

### 2. Grilles de Données Configurables
- Sélection du modèle
- Choix des colonnes à afficher
- Description personnalisable
- Tables interactives avec DataTables (tri, recherche, pagination)

### 3. Switch de Thèmes
- 5 thèmes disponibles :
  - Par défaut (bleu Django)
  - Sombre
  - Bleu
  - Vert
  - Violet
- Persistance via localStorage
- Application immédiate

## 🚀 Utilisation

1. **Générer un graphique** :
   - Sélectionner le modèle, le champ, le type, la fréquence et l'opération
   - Cliquer sur "Générer le graphique"

2. **Créer une grille** :
   - Sélectionner le modèle
   - Entrer les colonnes séparées par des virgules (ex: `order_number,status,total_amount`)
   - Ajouter une description optionnelle
   - Cliquer sur "Créer la grille"

3. **Changer de thème** :
   - Cliquer sur le bouton "🎨 Thèmes" en bas à droite
   - Sélectionner un thème
   - Le thème est sauvegardé automatiquement

## 📁 Structure

- `models.py` : Modèles DashboardGrid et DashboardChart (pour sauvegarder les configurations)
- `views.py` : APIs pour récupérer les données des graphiques et grilles
- `admin.py` : Enregistrement des modèles dans l'admin
- `templates/admin/` : Templates personnalisés
- `static/css/` : Styles CSS et thèmes
- `static/js/` : JavaScript pour les fonctionnalités dynamiques

## 🔧 Configuration

Les modèles disponibles pour les graphiques et grilles :
- `Order` : Commandes
- `Invoice` : Factures
- `Payment` : Paiements
- `Product` : Produits
- `Category` : Catégories
- `UserProfile` : Profils utilisateurs

## 📝 Notes

- Les graphiques utilisent Chart.js (CDN)
- Les grilles utilisent DataTables (CDN)
- Le thème est sauvegardé dans le localStorage du navigateur
- Les données sont récupérées dynamiquement via des APIs AJAX
