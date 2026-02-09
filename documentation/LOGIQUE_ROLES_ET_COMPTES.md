# Logique des rôles et des comptes FLOTTE

Ce document décrit la logique recommandée pour **Admin**, **Gestionnaire** et **Utilisateur (client)**, et ce qui est déjà en place dans l’application.

---

## 1. Résumé en une phrase par rôle

| Rôle | En bref |
|------|--------|
| **Admin** | Crée tous les comptes (gestionnaires et clients), gère le paramétrage et a accès à tout. |
| **Gestionnaire** | Gère toute l’activité opérationnelle (parc, ventes, CA, import, locations, etc.) mais ne crée pas les comptes et n’accède pas au paramétrage. |
| **Utilisateur (client)** | Compte créé par l’admin après une transaction (vente, location, etc.) ; une fois connecté, il consulte uniquement ce qui le concerne (ses véhicules achetés, sa location, etc.). |

Cette logique est **saine et courante** pour une flotte / activité B2B : l’admin maîtrise les comptes et la config, le gestionnaire fait tourner l’activité, le client ne voit que ses propres affaires.

---

## 2. Ce qui est déjà en place dans FLOTTE

### 2.1 Admin

- **Création de comptes** : seul l’**admin** peut créer des utilisateurs (Paramétrage → Utilisateurs → Ajouter). ✅  
- **Paramétrage** : marques, modèles, types (carburant, transmission, véhicule, document), **utilisateurs** → réservé à l’admin. ✅  
- **Accès complet** : admin voit tout (dashboard, parc, échéances, import, ventes, CA, locations, etc.). ✅  

Donc : *« L’admin gère les créations de compte et gère tout de manière complète »* → **déjà le cas**.

### 2.2 Gestionnaire

- **Pas de création de comptes** : le gestionnaire n’a pas accès à Paramétrage → Utilisateurs. ✅  
- **Pas de paramétrage** : pas d’accès aux écrans marques, modèles, types, etc. ✅  
- **Toute la gestion opérationnelle** : parc, véhicules, import, démarches, ventes, CA, locations, réparations, documents, maintenance, carburant, conducteurs, échéances. ✅  

Donc : *« Le gestionnaire gère tout ce qui est gestion (sans paramétrage ni comptes) »* → **déjà le cas**.

### 2.3 Utilisateur (client)

- **Compte créé par l’admin** : oui, en créant un utilisateur avec le rôle « Utilisateur ». ✅  
- **Droits actuels** : le rôle « Utilisateur » voit aujourd’hui : tableau de bord, échéances, parc (liste véhicules), réparations, documents, maintenance, carburant, conducteurs. Il ne voit **pas** : ventes, CA, import, liste des locations, paramétrage. ✅  
- **Limite actuelle** : il n’y a **pas encore** de lien entre le compte « Utilisateur » et *ses* ventes / *sa* location. Donc aujourd’hui un utilisateur voit le **parc global** (ou des listes globales), pas uniquement « ce qui le concerne ».  

Pour que *« quand il se connecte il consulte tout ce qui lui concerne »* soit vrai, il faut **lier le compte client aux données** (ventes, locations, etc.). C’est la seule partie à faire évoluer (voir § 4).

---

## 3. Synthèse : qui fait quoi

```
┌─────────────────────────────────────────────────────────────────┐
│  ADMIN                                                           │
│  • Crée les comptes (Gestionnaire + Utilisateur / client)        │
│  • Paramétrage (marques, modèles, types, utilisateurs)          │
│  • Accès à tout le reste comme le gestionnaire                   │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  GESTIONNAIRE                                                    │
│  • Parc, véhicules, import, ventes, CA, locations                │
│  • Réparations, documents, maintenance, carburant, conducteurs   │
│  • Pas de paramétrage, pas de création de comptes                │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  UTILISATEUR (CLIENT)                                             │
│  • Compte créé par l’admin (souvent après une vente / location)  │
│  • Idéal : ne voir que « ses » ventes, « sa » location, etc.    │
│  • Actuellement : voit parc / listes globales (à filtrer côté    │
│    code pour n’afficher que ce qui le concerne)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Pour que le client ne voie que « ce qui le concerne »

Aujourd’hui, le modèle **Vente** a un champ `acquereur` (nom de l’acquéreur en texte), mais **aucun lien** avec un compte utilisateur. Idem pour les locations (pas de « client » lié à un User).

Pour appliquer la logique *« client = consultation de tout ce qui le concerne »*, il faut **relier le compte (User) aux données** :

1. **Option A – Lien direct sur la vente**  
   Ajouter sur le modèle `Vente` un champ optionnel du type :  
   `acquereur_compte = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='ventes_comme_acquereur')`.  
   Lors de la création du compte client, l’admin choisit (ou renseigne plus tard) à quelles ventes ce compte est associé. Ensuite, pour un utilisateur avec le rôle « Utilisateur », on filtre les ventes (et écrans dérivés) avec `ventes où acquereur_compte = request.user`.

2. **Option B – Lien par email**  
   Garder `acquereur` (nom) et ajouter par exemple `acquereur_email` sur `Vente`. À la connexion, on filtre les ventes où `acquereur_email = request.user.email`. Moins robuste (changement d’email, doublons) mais sans changer le modèle User.

3. **Espace « Mon compte » ou « Mes véhicules »**  
   Une fois le lien en place (A ou B), ajouter une vue dédiée (ex. « Mes achats » / « Ma location ») qui ne liste que les ventes (et éventuellement locations) liées à `request.user`, et limiter pour ce rôle l’accès au parc global (ou le filtrer par « mes véhicules »).

Recommandation : **Option A** (ForeignKey `acquereur_compte` sur `Vente`, et éventuellement un champ similaire sur **Location** si le client doit voir « sa » location). L’admin crée le compte client puis associe ce compte aux ventes (ou locations) concernées.

### 4.1 En place : à quel moment associer un client ?

- **À la création ou à la modification d'une vente** : l'admin ou le gestionnaire ouvre le formulaire de vente (création ou édition) et peut choisir optionnellement **« Compte client (acquéreur) »**. Seuls les utilisateurs avec le rôle « Utilisateur » sont proposés. Une fois la vente enregistrée avec ce champ renseigné, le client concerné voit cette vente dans **« Mes ventes »** (menu côté client).
- Le client (rôle Utilisateur) a le lien **« Mes ventes »** dans la sidebar ; la liste est filtrée sur `acquereur_compte = request.user`. Il ne peut pas créer ni modifier de ventes.

---

## 5. Réponses directes à tes questions

- **« L’admin gère les créations de compte »** → Oui, et c’est déjà comme ça dans FLOTTE (seul l’admin crée les comptes).  
- **« L’admin gère tout de manière complète »** → Oui (paramétrage + tout le reste).  
- **« Le gestionnaire gère tout ce qui est gestion »** → Oui (opérationnel uniquement, sans paramétrage ni création de comptes).  
- **« Le client est créé parce qu’il a eu une transaction »** → C’est la logique cible : l’admin crée le compte « Utilisateur » après une vente/location et peut ensuite lier ce compte aux données (dès qu’on ajoute le lien en base).  
- **« Quand il se connecte il consulte tout ce qui le concerne »** → C’est l’objectif ; il manque seulement le **lien** entre le compte (User) et les ventes/locations, puis le **filtrage** dans les vues pour le rôle Utilisateur.

En résumé : la **logique des rôles** que tu décris est la bonne et correspond déjà en grande partie à FLOTTE. La seule évolution à prévoir est de **lier le client (User) aux ventes (et éventuellement locations)** pour que « consulter ce qui le concerne » soit appliqué à l’écran.
