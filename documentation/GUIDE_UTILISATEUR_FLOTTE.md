# Guide utilisateur FLOTTE — de A à Z

Guide simple pour utiliser l’application **FLOTTE** (gestion de flotte automobile : import, parc, locations, ventes).  
Tous les montants sont en **FCFA**.

---

## 1. À quoi sert FLOTTE ?

En gros, FLOTTE permet de :

- **Enregistrer** les véhicules (achat, import, parc).
- **Suivre** les étapes d’import (douane, immatriculation, etc.) et les **coûts** (fret, dédouanement).
- **Rattacher** à chaque véhicule : documents (carte grise, assurance, CT), dépenses, réparations, factures.
- **Gérer** les locations (LLD, LOA) avec conducteur, CT, assurance, contraventions.
- **Enregistrer** les ventes et voir le **chiffre d’affaires** et les **coûts** (TCO).

Chaque chose est **associée** à un véhicule (ou à une location) pour tout retrouver au même endroit.

---

## 2. Se connecter et rôles

- **Connexion** : identifiant + mot de passe (ou « Se connecter avec Google » si configuré).
- **Mot de passe oublié** : lien sur la page de connexion → email de réinitialisation.

**Trois rôles** (Paramétrage → Utilisateurs) :

| Rôle | En gros, il peut |
|------|-------------------|
| **Admin** | Tout faire + paramétrage (marques, modèles, types, utilisateurs) et consulter/exporter l’**audit**. |
| **Gestionnaire** | Tout sauf paramétrage et audit : parc, import, locations, ventes, CA, TCO, exports CSV. |
| **Utilisateur** | Voir le parc, les échéances, **ses** ventes (où il est acquéreur), pas les autres. |

---

## 3. Le tableau de bord

**Où** : menu **Tableau de bord**.

**En gros** : vue d’ensemble du parc et des **alertes** (CT, assurance, permis, documents).

- **Les 4 chiffres en haut** : véhicules au parc, en cours d’import, vendus, total.
- **Répartition par marque** : nombre de véhicules par marque.
- **Véhicules en cours d’import** : derniers véhicules en statut « En cours d’importation » ; clic sur le nom → fiche véhicule ; **Fiche** → idem ; **Voir tout l’import** → liste complète.
- **Alertes** : CT, assurance (locations et véhicules au parc), permis conducteurs, documents avec échéance dans les 30 jours. Chaque ligne pointe vers la fiche concernée.

**Lien utile** : « Voir toutes les échéances » → page **Échéances** (90 jours).

---

## 4. Le parc (véhicules)

**Où** : menu **Parc / Flotte**.

**En gros** : liste de **tous** les véhicules. On peut filtrer (Au parc / En import / Vendus) et **rechercher** (châssis, immat, marque…).

### Créer un véhicule

- **Nouveau véhicule** (menu ou bouton) → formulaire.

**Champs principaux (à quoi ça sert)** :

| Champ | À quoi ça sert |
|-------|-----------------|
| **Numéro de châssis** | Identifiant **unique** du véhicule (obligatoire). Ex. : WDD2050461A123456. |
| **Marque** | Liste déroulante : choisir une **marque** déjà créée au paramétrage (ex. Toyota). |
| **Modèle** | Liste déroulante : les **modèles** dépendent de la marque choisie (ex. Corolla). Si la marque n’a pas de modèle, en créer un dans Paramétrage → Modèles. |
| **Année** | Année du véhicule. |
| **Statut** | **Au parc** (dispo), **En cours d’importation**, ou **Vendu**. Détermine où le véhicule apparaît (parc, import, liste ventes). |
| **Type véhicule / carburant / transmission** | Listes du paramétrage (voiture, SUV ; essence, diesel ; manuelle, auto). |
| **Couleurs** | Extérieure et intérieure : liste (Blanc, Noir, etc.) ou saisie. |
| **Date entrée parc** | Date à laquelle le véhicule est entré au parc. |
| **Km à l’entrée** / **Kilométrage actuel** | Kilométrage ; à mettre à jour si besoin. |
| **Prix d’achat (FCFA)** | Prix d’achat du véhicule (pour calcul des coûts et marges). |
| **Pays d’origine** | Saisie avec **suggestions** : taper pour afficher la liste des pays, puis choisir (ex. Allemagne, Japon). |
| **État à l’entrée** | Très bon, Bon, Correct, À réparer. |
| **N° immatriculation** | Numéro de plaque (souvent renseigné après import). |
| **Date première immat.** | Date de première immatriculation. |
| **CT / Assurance (véhicule au parc)** | Pour un véhicule **non loué** : dates d’expiration du contrôle technique et de l’assurance. |

Enregistrer → le véhicule apparaît dans le parc (ou dans « Import » si statut = En cours d’importation).

### Voir ou modifier un véhicule

- Clic sur le **nom du véhicule** ou sur **Fiche** → **fiche véhicule** (détail complet).
- **Modifier** (sur la fiche ou depuis la liste) → même formulaire pour corriger les infos.

---

## 5. La fiche véhicule (détail d’un véhicule)

**Où** : Parc → clic sur un véhicule (ou Recherche → clic sur un résultat).

**En gros** : tout ce qui est **rattaché** à ce véhicule est regroupé sur une seule page.

### Blocs de la fiche

- **Identification** : résumé (marque, modèle, châssis, km, prix achat, origine, statut, immat, CT, assurance). Bouton **Modifier** pour changer ces infos.

- **Démarches import** : les **étapes** d’import (douane, transport, CT, immatriculation…). Chaque ligne = une étape (nom, date, statut). **Ajouter une démarche** : étape, date, statut, pièce jointe (PDF/image) optionnelle, remarque. **À quoi ça sert** : suivre où en est le véhicule dans l’import et garder les justificatifs.

- **Charges d’importation** : **fret**, **dédouanement**, **frais transitaire**. Le **coût total** est calculé automatiquement (fret + dédouanement + transitaire). **Ajouter une charge** : remplir les montants (FCFA) ; la remarque est optionnelle. **À quoi ça sert** : connaître le coût total d’import du véhicule.

- **Parties importées** : pièces ou parties importées **liées** (ou non) à ce véhicule. Désignation, quantité, coût unitaire. Optionnel.

- **Documents** : carte grise, assurance, CT, vignette, etc. Pour chaque document : **type** (liste ou « Autre »), numéro, dates d’émission/échéance, **disponible** (oui/non), **fichier** (PDF/image) optionnel. **À quoi ça sert** : savoir quels documents existent, leurs échéances, et attacher le scan.

- **Dépenses** : dépenses **liées** à ce véhicule (entretien, réparation, carburant, assurance, autre). Libellé, type, phase (suggestion : Import, Réparation…), montant (FCFA), date. **À quoi ça sert** : suivre tout ce qu’on a dépensé pour ce véhicule.

- **Réparations** : réparations **effectuées ou à faire**. Date, km, type (suggestions : Carrosserie, Mécanique…), description, coût (FCFA), prestataire. **À quoi ça sert** : historique des réparations et coûts.

- **Factures** : factures **rattachées** au véhicule (achat, réparation, assurance…). Numéro, fournisseur, date, montant, type, **fichier** (PDF) optionnel. **À quoi ça sert** : garder la trace des factures et du coût de référence (la fiche affiche un total des coûts).

- **Coûts & marge** : **Prix d’achat** + **Total dépenses** + **Total réparations** + **Total charges d’import** = coût total. Si le véhicule est vendu, comparaison avec le prix de vente (marge). **À quoi ça sert** : voir combien le véhicule a coûté au total et la marge si vendu.

- **Vente / Cession** : si le véhicule est **vendu**, infos de la vente (acquéreur, date, prix, km, garantie, état livraison). Sinon, bouton **Ajouter une vente** pour enregistrer la vente (voir section Ventes).

- **Locations** : liste des **locations** de ce véhicule (LLD, LOA…). Lien vers la fiche de chaque location.

**Règle simple** : tout ce que vous ajoutez (démarche, charge, document, dépense, réparation, facture, vente) est **associé** à ce véhicule et apparaît ici.

---

## 6. Import & démarches

**Où** : menu **Import & démarches** (Gestionnaire/Admin).

**En gros** : liste des véhicules **en cours d’import** avec leurs démarches. Pour chaque véhicule on voit les étapes enregistrées (depuis la fiche véhicule).

- **Fiche** → ouvre la fiche du véhicule (où on peut **ajouter** des démarches et des charges d’import).
- Les **démarches** se renseignent sur la **fiche véhicule** (bloc « Démarches import » → Ajouter une démarche).

---

## 7. Parties importées

**Où** : menu **Parties importées**.

**En gros** : pièces ou parties importées (pas forcément liées à un véhicule). Désignation, quantité, coût unitaire, **véhicule** (optionnel : on peut associer à un véhicule ou laisser vide pour un stock général).

- **Ajout** : depuis la liste ou depuis la fiche véhicule (alors le véhicule est pré-rempli).

---

## 8. Locations

**Où** : menu **Location** (Gestionnaire/Admin).

**En gros** : contrats de location (LLD, LOA, courte durée). Chaque location est **associée** à **un véhicule** et optionnellement à **un conducteur**.

### Créer une location

- **Nouvelle location** → formulaire.

**Champs principaux** :

| Champ | À quoi ça sert |
|-------|-----------------|
| **Véhicule** | Liste des véhicules **au parc** : choisir celui qui est loué. |
| **Conducteur** | Liste des conducteurs actifs : choisir le chauffeur assigné (optionnel). |
| **Locataire** | Nom du locataire (société ou particulier). Suggestions si déjà saisis. |
| **Type** | LLD, LOA, Location courte. |
| **Date début / Date fin** | Période du contrat. |
| **Loyer mensuel (FCFA)** | Loyer. |
| **Coût de location** / **Frais annexes** | Coût global ou complément ; frais annexes (assurance, entretien…). |
| **Km inclus / mois** ; **Prix km supplémentaire** | Si prévu au contrat. |
| **Date expiration CT** / **Assurance** | Échéances pour ce contrat (alertes tableau de bord). |
| **Km prochaine vidange** | Pour le suivi. |
| **Statut** | En cours, À venir, Terminé. |

Enregistrer → la location apparaît dans la liste et sur la **fiche véhicule**.

### Contraventions (amendes)

Sur la **fiche location** (clic sur une location) : on peut **ajouter des contraventions** (date, référence, montant). Elles sont prises en compte dans le **coût total** de la location (loyer + frais + contraventions).

---

## 9. Ventes

**Où** : menu **Ventes** (ou fiche véhicule → Ajouter une vente).

**En gros** : enregistrer la **cession** d’un véhicule (acquéreur, date, prix, km, garantie, état livraison). Dès qu’une vente est enregistrée pour un véhicule, son **statut** passe à **Vendu** (il sort du parc et de l’export réglementaire).

**Champs** :

| Champ | À quoi ça sert |
|-------|-----------------|
| **Date vente** | Date de la cession. |
| **Acquéreur** | Nom de l’acheteur (particulier ou société). |
| **Compte client (acquéreur)** | Si l’acquéreur a un **compte Utilisateur** dans FLOTTE, on peut l’associer pour qu’il voie cette vente dans « Mes ventes ». |
| **Prix vente (FCFA)** | Prix de vente. |
| **Km à la vente** | Kilométrage au moment de la vente. |
| **Garantie** | Suggestions : Aucune, 6 mois, 1 an… ou saisie libre. |
| **État livraison** | Suggestions : Bon état, Très bon état… ou saisie libre. |

Enregistrer → le véhicule passe en « Vendu », la vente apparaît dans Chiffre d’affaires et TCO.

---

## 10. Réparations, Documents, Maintenance, Carburant, Conducteurs

- **Réparations** (menu) : liste de **toutes** les réparations ; chaque ligne est liée à un véhicule. On peut ajouter depuis la liste ou depuis la **fiche véhicule** (bloc Réparations).

- **Documents** (menu) : liste des **documents** (carte grise, assurance, CT…) par véhicule. L’ajout se fait sur la **fiche véhicule** (bloc Documents).

- **Maintenance préventive** : rappels (vidange, révision…) par véhicule. Formulaire : véhicule, type de maintenance, dates prévues/effectuées, km, coût, prestataire, statut.

- **Carburant** : relevés de carburant (date, km, litres, montant, lieu). Associés à un véhicule.

- **Conducteurs** : liste des **chauffeurs**. Nom, prénom, email, téléphone, date expiration permis. On les **associe** à une **location** (champ Conducteur assigné). **Ajouter** : formulaire ; **Modifier** : même formulaire.

**Règle** : tout est **associé** soit à un **véhicule**, soit à une **location** (elle-même liée à un véhicule), pour tout retrouver au bon endroit.

---

## 11. Chiffre d’affaires et TCO

- **Chiffre d’affaires** (menu) : synthèse du CA (total, nombre de ventes), **évolution** (graphique), **détail** par période. Upload de **rapports journaliers** ou documents CA (PDF). Réservé Gestionnaire/Admin.

- **TCO** (Coût total de possession) : tableau des véhicules avec **acquisition** (achat + import), **dépenses**, **maintenance**, **carburant**, **vente**, et **TCO** (coût total moins prix de vente si vendu).  
  **Exports CSV** (boutons en haut) : **Export réglementaire** (véhicules, immat, CT, assurance, locataire), **Export charges d’import**, **Export locations**.

---

## 12. Paramétrage (Admin)

**Où** : menu **Paramétrage**.

**En gros** : définir les **listes** utilisées partout (marques, modèles, types, types de documents, utilisateurs) et consulter l’**audit**.

- **Marques** : ajouter/modifier/archiver les **marques** (ex. Toyota, BMW). Les véhicules choisissent une marque dans la liste.
- **Modèles** : ajouter des **modèles** **par marque** (ex. Corolla pour Toyota). Chaque modèle a une marque, une version, des années min/max.
- **Types** : **Carburant** (essence, diesel…), **Transmission** (manuelle, auto…), **Type de véhicule** (voiture, SUV…). Utilisés dans le formulaire véhicule.
- **Types de document** : liste des types de documents (carte grise, assurance, CT…) pour le bloc Documents de la fiche véhicule.
- **Utilisateurs** : créer/modifier les **comptes** et leur **rôle** (Admin, Gestionnaire, Utilisateur).
- **Audit** : journal des **créations, modifications, suppressions** (qui, quand, sur quel objet). Filtres par date, utilisateur, modèle. **Exporter CSV** pour garder une trace.

**Règle** : avant d’avoir des véhicules « Toyota Corolla », il faut une **marque** Toyota et un **modèle** Corolla (lié à Toyota). Idem pour les types : les créer ici pour qu’ils apparaissent dans les listes.

---

## 13. Recherche et exports

- **Recherche** (champ en haut ou menu **Recherche**) : en tapant (châssis, marque, locataire, acquéreur, conducteur, fournisseur…), les **résultats s’affichent au fur et à mesure** (véhicules, locations, ventes, conducteurs, factures). Clic sur une ligne → fiche correspondante.

- **Exports** (voir aussi **documentation/EXPORTATIONS.md**) :
  - **Export réglementaire** : véhicules (parc + import) avec immat, CT, assurance, locataire (page TCO).
  - **Export charges d’import** : toutes les charges (fret, dédouanement, transitaire, coût total) en CSV (page TCO).
  - **Export locations** : toutes les locations avec coût total (page TCO ou page Location).
  - **Export audit** : journal d’audit en CSV (Paramétrage → Audit), avec filtres.

- **Téléchargement de fichiers** : sur la fiche véhicule, les factures, documents et démarches avec **fichier** attaché ont un lien (PDF / Fichier / Document) pour ouvrir ou télécharger le fichier.

---

## 14. Récapitulatif des associations

| Élément | Associé à | Où le renseigner |
|--------|-----------|-------------------|
| Véhicule | Marque, Modèle (paramétrage) | Parc → Nouveau véhicule / Modifier |
| Démarche import | Véhicule | Fiche véhicule → Démarches import → Ajouter |
| Charge d’import | Véhicule | Fiche véhicule → Charges d’importation → Ajouter |
| Partie importée | Véhicule (optionnel) | Fiche véhicule ou menu Parties importées |
| Document | Véhicule + type (liste) | Fiche véhicule → Documents → Ajouter |
| Dépense | Véhicule | Fiche véhicule → Dépenses → Ajouter |
| Réparation | Véhicule | Fiche véhicule → Réparations → Ajouter |
| Facture | Véhicule | Fiche véhicule → Factures → Ajouter |
| Location | Véhicule + Conducteur (optionnel) | Menu Location → Nouvelle location |
| Contravention | Location | Fiche location → Ajouter contravention |
| Vente | Véhicule (+ compte acquéreur optionnel) | Fiche véhicule → Vente ou menu Ventes |
| Maintenance / Relevé carburant | Véhicule | Menus Maintenance, Carburant |

---

## 15. Ordre conseillé pour bien démarrer

1. **Paramétrage** : créer au moins une **marque** et un **modèle**, et quelques **types** (carburant, transmission, type de véhicule) si besoin.
2. **Parc** : **créer un véhicule** (châssis, marque, modèle, statut, prix, etc.).
3. **Fiche véhicule** : ajouter des **démarches** (import), des **charges d’import**, un **document** (ex. carte grise), une **dépense** ou **réparation** pour voir comment tout se rattache.
4. **Conducteurs** : créer un conducteur si vous faites des **locations**.
5. **Location** : créer une location (véhicule + locataire + type + dates).
6. **Vente** : sur un véhicule, ajouter une vente pour le passer en « Vendu » et voir le CA / TCO.

À partir de là, vous avez fait le tour des principaux enchaînements : **paramétrage → véhicule → fiche (démarches, charges, documents, dépenses, réparations, factures) → location → vente**. Le guide ci‑dessus détaille chaque champ et chaque partie pour vous guider de la manière la plus simple.
