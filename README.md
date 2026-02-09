# FLOTTE — Gestion d'import & parc véhicules

Application Django de gestion de flotte automobile (import, parc, ventes, CA).

## Contexte du projet

**FLOTTE** est une application **Django** de **gestion de flotte automobile** centrée sur l’**import de véhicules**. Elle vise les professionnels qui :

- **Importent** des véhicules (douane, homologation, immatriculation, carte grise),
- **Suivent** l’état du parc (date d’entrée, kilométrage, prix d’achat, origine, réparations),
- **Conservent** les documents (carte grise, assurance, contrôle technique, etc.) avec la date de chaque pièce,
- **Vendent** les véhicules (acquéreur, garantie, état à la livraison) et **suivent** le chiffre d’affaires et les marges.

Tous les montants sont en **FCFA** (conversion indicative 1 € ≈ 656 FCFA).

---

## Lancer l'application

**Important :** le projet utilise un environnement virtuel (`.venv`). Il faut **toujours l’activer** avant toute commande (`runserver`, `migrate`, `createsuperuser`, etc.).

### 1. Créer le venv (une seule fois)

```powershell
cd chemin\vers\FLOTTE
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-django.txt
```

### 2. Migrations et données (une seule fois)

```powershell
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py load_parametrage_initial
python manage.py createsuperuser
```

### 3. Démarrer le serveur (à chaque fois)

**Option A — Script (recommandé)** : le script active le venv puis lance le serveur.

- **PowerShell** : `.\runserver.ps1`
- **Invite de commandes** : `runserver.bat`

**Option B — À la main** : activer le venv, puis lancer le serveur.

- **PowerShell** :
  ```powershell
  .\.venv\Scripts\Activate.ps1
  python manage.py runserver
  ```
- **Invite de commandes (cmd)** :
  ```cmd
  .venv\Scripts\activate.bat
  python manage.py runserver
  ```

Puis ouvrir **http://127.0.0.1:8000/** et se connecter avec le superuser (ou avec **Se connecter avec Google** si configuré).

Fonctionnalités : châssis = identifiant véhicule, Paramétrage (marques, modèles, types carburant/transmission/véhicule, utilisateurs), Location (CT, assurance, km vidange), Parc, Import, Réparations, Documents, Ventes, CA. Thème beige conservé.

### Connexion Google (optionnel)

Pour activer le bouton **« Se connecter avec Google »** sur la page de connexion :

1. **Google Cloud Console** : [APIs & Services → Identifiants](https://console.cloud.google.com/apis/credentials) → Créer des identifiants → **ID client OAuth 2.0** (type **Application Web**).
2. **URI de redirection autorisés** : ajouter  
   - En local : `http://127.0.0.1:8000/accounts/google/login/callback/`  
   - En production : `https://votre-domaine.com/accounts/google/login/callback/`
3. **Variables d’environnement** (ne jamais les mettre dans le code) :
   - `GOOGLE_OAUTH_CLIENT_ID` = ID client
   - `GOOGLE_OAUTH_CLIENT_SECRET` = Secret client

Sans ces variables, le bouton Google reste affiché mais la connexion Google échouera tant qu’elles ne sont pas définies.

### Emails (bienvenue, mot de passe oublié)

À chaque **création de compte** (Paramétrage → Utilisateurs → Ajouter, ou connexion Google), un **email de bienvenue** est envoyé automatiquement (si l’utilisateur a une adresse email) : message structuré avec lien « Accéder à l’application ». Les templates HTML se trouvent dans `templates/flotte/emails/` (bienvenue, réinitialisation mot de passe). Pour ajouter d’autres emails (rappels CT, expiration documents, etc.), réutiliser le module `flotte.emails` et la fonction `send_mail_html()`. En dev sans SMTP, les emails s’affichent dans la console. Pour un envoi réel, ajouter dans `.env` : `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (Gmail : mot de passe d'application). Tester avec : `python manage.py send_test_email votre@email.com`. Le domaine des liens : `EMAIL_DOMAIN` ou site Django (Admin → Sites).

---

## Définitions / Lexique

Termes techniques utilisés dans la maquette et ce README :

| Terme | Définition |
|-------|------------|
| **ANTS** | Agence nationale des titres sécurisés. Organisme public français qui délivre notamment les cartes grises et gère les demandes d’immatriculation (en ligne ou via Simplimmat). |
| **Backdrop** | Fond semi-transparent (grisé) affiché derrière une fenêtre modale. Cliquer dessus ferme la modal. |
| **Backend** | Partie « serveur » d’une application (bases de données, logique métier). La maquette FLOTTE n’a pas de backend : aucune donnée n’est sauvegardée. |
| **Badge** | Petite pastille ou étiquette affichant une information (ex. rôle « Admin », statut « En import », « Au parc »). |
| **CA** | **Chiffre d’affaires** : montant total des ventes sur une période (mois, année). |
| **Carte grise** | Certificat d’immatriculation du véhicule (titre officiel). Obligatoire pour circuler. Contient le numéro d’immatriculation, les caractéristiques du véhicule, etc. |
| **CG** | Abréviation de **carte grise**. |
| **COC** | **Certificat de conformité** (européen). Document du constructeur attestant que le véhicule respecte les normes européennes. Permet souvent d’éviter une réception à titre isolé (RTI). |
| **CT** | **Contrôle technique** : examen périodique obligatoire du véhicule (sécurité, pollution). La date du « prochain CT » est à suivre pour chaque véhicule. |
| **Démarches** | Étapes administratives à accomplir (douane, homologation, immatriculation, carte grise, etc.). |
| **Devis** | Document ou maquette présentant une offre (prix, fonctionnalités). Ici, la maquette sert de support pour montrer ce que fera le système. |
| **Douane** | Formalités et droits à régler lors de l’**import** d’un véhicule acheté à l’étranger (déclaration, éventuels droits et taxes). |
| **DREAL** | Direction régionale de l’environnement, de l’aménagement et du logement. En France, instructeur des demandes d’**homologation** / **réception à titre isolé** (RTI) pour les véhicules importés. |
| **FCFA** | **Franc CFA** (XOF en Afrique de l’Ouest, XAF en Afrique centrale). Unité monétaire utilisée dans la maquette pour les montants (devis, CA, marges, etc.). Conversion indicative : 1 € ≈ 656 FCFA. |
| **Hash** | Partie de l’URL après le `#` (ex. `#parc`, `#dashboard`). Utilisée ici pour la navigation entre sections sans recharger la page. |
| **Homologation** | Procédure qui certifie qu’un véhicule est conforme aux normes (sécurité, émissions). Préalable à l’immatriculation. Peut passer par un **COC** ou une **RTI**. |
| **Immat. / Immatriculation** | Enregistrement du véhicule et attribution d’un **numéro d’immatriculation** (plaques). En France, demande via l’**ANTS** (ou professionnel habilité). |
| **KPI** | **Key Performance Indicator** (indicateur clé de performance). Indicateur synthétique pour suivre l’activité (ex. nombre de véhicules au parc, CA du mois, ventes du mois). |
| **Marge** | Différence entre le **prix de vente** et les **coûts** (achat + réparations, etc.). Peut être exprimée en montant (FCFA) ou en pourcentage. |
| **Modal** | Fenêtre qui s’affiche au-dessus du contenu principal et qui impose une action (consulter, remplir, fermer) avant de revenir à la page. Ex. : Fiche véhicule, Nouveau véhicule. |
| **N° immat.** | **Numéro d’immatriculation** (plaques). Attribué une fois la **carte grise** obtenue. |
| **Parc / Flotte** | Ensemble des véhicules détenus ou gérés par l’entreprise (en stock, en import, ou vendus). |
| **PV** | **Procès-verbal**. Ex. **PV de livraison** : document signé à la remise du véhicule à l’acquéreur (à conserver avec la facture de vente). |
| **RTI** | **Réception à titre isolé**. Procédure d’**homologation** pour un véhicule spécifique (souvent import hors UE ou sans **COC**), instruite par la **DREAL**. |
| **Sidebar** | Menu latéral fixe (à gauche) contenant la navigation entre les sections (Tableau de bord, Parc, Import, etc.) et le bouton « Nouveau véhicule ». |
| **VIN** | **Vehicle Identification Number** (numéro d’identification du véhicule). Code unique de 17 caractères (chiffres et lettres) qui identifie chaque véhicule. Présent sur la carte grise et souvent sur la carrosserie. |

---

## Actions possibles, par section

### 1. Navigation (menu latéral)

| Action | Comment | Exemple / précision |
|--------|---------|---------------------|
| **Changer de section** | Cliquer sur un lien du menu (Tableau de bord, Parc, Import, etc.) | L’URL passe à `#dashboard`, `#parc`, `#import`, etc. L’onglet actif se met en surbrillance (fond beige). |
| **Ouvrir « Nouveau véhicule »** | Cliquer sur **Nouveau véhicule** en bas du menu | Une modal s’ouvre avec le formulaire d’ajout. La date du jour est pré-remplie. |

---

### 2. En-tête (barre du haut)

| Action | Comment | Exemple / précision |
|--------|---------|---------------------|
| **Rechercher un véhicule** | Saisir du texte dans **Rechercher véhicule, VIN, marque…** | La recherche filtre les lignes du **tableau Parc / Flotte** (marque, modèle, VIN, année). Ex. : taper `toyota` ou `2019` n’affiche que les véhicules correspondants. |
| **Voir l’utilisateur connecté** | Regarder le badge **Admin** à droite | En maquette, le badge est fixe (pas de connexion réelle). |

---

### 3. Tableau de bord

| Action | Comment | Exemple / précision |
|--------|---------|---------------------|
| **Consulter les KPIs** | Regarder les 4 cartes en haut | **Véhicules dans le parc** (ex. 24), **En cours d’import** (5), **Vendus ce mois** (3), **CA du mois (FCFA)** (ex. 28 076 800). |
| **Voir l’activité récente** | Lire la liste **Activité récente** | Dernières actions : entrée au parc, carte grise obtenue, vente, réparation, homologation en cours, etc. |
| **Identifier les démarches en attente** | Lire **Démarches en attente** | Badges (Immatriculation, Carte grise, Douane) + véhicule concerné. Ex. : *Immatriculation — Toyota Corolla*. |
| **Consulter les alertes** | Lire **Alertes** | Prochains **contrôles techniques** et **échéances d’assurance** par véhicule. Ex. : *CT — BMW 320d — Prochain CT 15/04/2025*. |

---

### 4. Parc / Flotte

| Action | Comment | Exemple / précision |
|--------|---------|---------------------|
| **Voir la liste des véhicules** | Ouvrir la section **Parc / Flotte** | Tableau : Marque/Modèle, Année, VIN, Date entrée, Km entrée, Prix achat (FCFA), Origine, État, Immat., Statut. |
| **Filtrer** | Utiliser le menu **Filtrer par état** | Options : Tous, Au parc, En import, Vendus. *En maquette, les filtres sont affichés mais non branchés (pas de filtrage effectif).* |
| **Trier** | Utiliser le menu **Tri** | Options : Date entrée ↓, Marque, Modèle. *En maquette, le tri est affiché mais non branché.* |
| **Rechercher** | Saisir dans la barre de recherche (en-tête) | Filtre les lignes du tableau en temps réel (voir § 2). |
| **Ouvrir la fiche d’un véhicule** | Cliquer sur **Fiche** dans la ligne du véhicule | Ouvre la **modal Fiche véhicule** avec identification, démarches, réparations, coûts & marge, vente. |

---

### 5. Import & démarches

| Action | Comment | Exemple / précision |
|--------|---------|---------------------|
| **Suivre les démarches par véhicule** | Consulter le tableau **Suivi des démarches** | Colonnes : Véhicule, Date entrée, **Douane** (date ou « En cours »), **Homologation / RTI**, **Immatriculation**, **Carte grise**, **N° immat.**, État. |
| **Repérer l’étape en cours** | Regarder la colonne **État** et les dates | Ex. : *Immat.* = en attente d’immatriculation ; *CG* = en attente de carte grise ; *Complet* = toutes les étapes faites. |

Ordre type des étapes : **Douane** → **Homologation / Réception (DREAL ou COC)** → **Immatriculation ANTS** → **Carte grise** → Assurance.

---

### 6. Réparations

| Action | Comment | Exemple / précision |
|--------|---------|---------------------|
| **Consulter l’historique des réparations** | Ouvrir **Réparations** | Tableau : Véhicule, Date, **Km** au moment de l’intervention, Type (Mécanique, Carrosserie, Freinage…), Description, **Coût (FCFA)**, Prestataire. |
| **Exemple** | — | *VW Golf — 18/01/2025 — 94 200 km — Distribution + kit courroie — 472 320 FCFA — Garage Duval.* |

---

### 7. Documents

| Action | Comment | Exemple / précision |
|--------|---------|---------------------|
| **Voir les documents par véhicule** | Ouvrir **Documents** et parcourir les cartes | Chaque carte = un véhicule. Liste des pièces avec **date** : Carte grise, Douane, COC, **Assurance** (souscription + **échéance**), **Contrôle technique** (dernier + **prochain**). |
| **Repérer les manquants** | Regarder les libellés « — … (en attente) » | Ex. : *— Carte grise (en attente)*, *— Contrôle technique (à faire)*. |

---

### 8. Ventes

| Action | Comment | Exemple / précision |
|--------|---------|---------------------|
| **Consulter les ventes** | Ouvrir **Ventes** | Tableau : Véhicule, Date vente, **Acquéreur** (particulier ou pro), **Prix vente (FCFA)**, **Km vente**, **Garantie** (durée + km), État livraison, **Marge (FCFA)**. |
| **Exemple** | — | *Audi A4 — 20/01/2025 — M. Kouassi — 12 136 000 FCFA — 112 300 km — 6 mois / 10 000 km — Très bon — +1 587 520 FCFA.* |

À conserver en réel : **facture de vente** et **PV de livraison**.

---

### 9. Chiffre d’affaires

| Action | Comment | Exemple / précision |
|--------|---------|---------------------|
| **Voir les KPIs CA** | Regarder les cartes en haut | **CA ce mois**, **Marge ce mois**, **CA mois précédent**, **CA année en cours** (tous en FCFA). |
| **Voir l’évolution du CA** | Regarder le **graphique Oct — Jan** | Barres relatives au CA (axe en millions FCFA). |
| **Voir le détail par mois** | Consulter le tableau **Détail des ventes par mois** | Colonnes : Mois, Nb ventes, **CA (FCFA)**, **Coûts (FCFA)**, **Marge (FCFA)**, **Marge (%)**. |

---

### 10. Fiche véhicule (modal)

| Action | Comment | Exemple / précision |
|--------|---------|---------------------|
| **Ouvrir la fiche** | Cliquer sur **Fiche** dans une ligne du tableau **Parc / Flotte** | La modal s’ouvre (même contenu pour chaque ligne en maquette). |
| **Consulter le détail** | Lire les blocs | **Identification** : Marque, Année, VIN, Date entrée, Km, Prix achat, Origine, État, N° immat. **Démarches & documents** : douane, homologation, immat., carte grise, assurance, CT. **Réparations** : historique ou « Aucune ». **Coûts & marge** : Prix achat + Réparations = Total ; indique si vendu ou au parc. **Vente / Cession** : acquéreur et garantie si vendu, sinon « Non vendu ». |
| **Fermer la modal** | Cliquer sur **×**, sur le fond (backdrop) ou appuyer sur **Échap** | La modal se ferme. |

---

### 11. Nouveau véhicule (modal + formulaire)

| Action | Comment | Exemple / précision |
|--------|---------|---------------------|
| **Ouvrir le formulaire** | Cliquer sur **Nouveau véhicule** dans le menu | La modal **Nouveau véhicule — Import** s’ouvre. La **date du jour** est pré-remplie. |
| **Remplir les champs** | Saisir les informations | **Marque / Modèle** (ex. *Mercedes Classe C 220d*), **Année** (ex. *2019*), **VIN** (17 caractères), **Date entrée parc**, **Km à l’entrée** (ex. *68000*), **Prix d’achat (FCFA)** (ex. *14760000*), **Origine** (ex. *Allemagne*), **État à l’entrée** (Très bon, Bon, Correct, À réparer). |
| **Enregistrer** | Cliquer sur **Enregistrer** | En maquette : une **alerte** récapitule les données saisies ; la modal se ferme et le formulaire est réinitialisé. Aucune donnée n’est enregistrée côté application. |
| **Annuler** | Cliquer sur **Annuler** ou fermer la modal (×, backdrop, Échap) | La modal se ferme sans enregistrement. |

---

## Structure du projet

| Élément | Rôle |
|--------|------|
| `flotte_project/` | Paramètres Django, URLs racine. |
| `flotte/` | Application : modèles, vues, formulaires, admin, signaux, commandes de gestion. |
| `templates/` | Templates HTML (base, dashboard, parc, locations, paramétrage, etc.). |
| `static/` | CSS (thème beige), fichiers statiques. |
| `manage.py` | Point d’entrée Django. |

---

## Palette & style

- **Couleur principale** : beige (`#e8dfd4`, `#c4b39e`, `#a8957a`, etc.) et accents bruns.
- **Typographies** : DM Sans (texte), Instrument Serif (titres).
- **Icônes** : SVG inline, style contour, `currentColor` pour s’adapter au thème.
