# Analyse avant améliorations — Fiche véhicule, facture, documents

Réponses aux questions avant de modifier le code.

---

## 1. Le côté facture, ça doit gérer automatique ?

**Aujourd’hui :** non. Les factures sont **saisies entièrement à la main** (numéro, fournisseur, date, montant, type). Il n’y a aucun lien avec les charges d’import, les dépenses ou les réparations, et aucun calcul automatique.

**Ce qu’on peut faire pour « gérer automatique » :**

| Élément | Proposition |
|--------|-------------|
| **Montant de référence** | Sur la fiche véhicule, la section **« Coûts & marge »** affiche déjà : prix d’achat + total dépenses + total réparations = coût total. On peut y ajouter le **total des charges d’import** pour avoir un **coût total complet** (référence pour facturation). Lors de la création d’une facture depuis un véhicule, on peut **suggérer ce montant** (champ pré-rempli ou indication). |
| **Pièce jointe facture** | Aujourd’hui la facture est uniquement « métadonnées ». Ajouter un champ **fichier (PDF)** sur le modèle `Facture` pour attacher la facture scannée → la partie « facture » gère alors aussi le **document réel**. |
| **Pas de génération auto de PDF** | Générer automatiquement un PDF de facture (design, mentions légales) serait un gros développement ; ce n’est pas prévu dans cette phase. L’automatique = **suggestion de montant** + **stockage du fichier** de la facture. |

**Conclusion :** oui, le côté facture peut être « géré de façon plus automatique » en : (1) affichant un coût total véhicule (achat + import + dépenses + réparations) comme référence, (2) suggérant ce montant à la création d’une facture, (3) permettant d’attacher un vrai document (PDF) à chaque facture.

---

## 2. Parties « document » : pouvoir ajouter de vrais documents

**Aujourd’hui :**

| Entité | Fichier ? | Constat |
|--------|-----------|--------|
| **DocumentVehicule** | Non | Uniquement type, numéro, dates, « disponible » / « à faire ». Aucun `FileField` → on ne peut pas joindre de fichier (carte grise, assurance, CT, etc.). |
| **ImportDemarche** | Non | Uniquement étape, date, statut, remarque. Aucune pièce jointe (PV, attestation, document douane, etc.). |
| **Facture** | Non | Uniquement numéro, fournisseur, date, montant, type. Aucun fichier pour la facture scannée. |

**Ce qu’il faut faire :**

- **DocumentVehicule** : ajouter un champ **`fichier`** (FileField, optionnel) pour attacher le document (PDF/image).
- **ImportDemarche** : ajouter un champ **`piece_jointe`** ou **`fichier`** (FileField, optionnel) pour attacher un document par démarche.
- **Facture** : ajouter un champ **`fichier`** (FileField, optionnel) pour la facture PDF.

Les formulaires et vues devront gérer l’upload (enctype, MEDIA_URL, sécurisation des accès). C’est cohérent avec « ajouter de vrais documents » partout où c’est pertinent.

---

## 3. Disposition : garder la même idée, plus pro et jolie

**Idée actuelle (à garder) :** grille de cartes (Identification, Démarches import, Charges d’importation, etc.), boutons « Ajouter / Modifier », listes d’activités.

**Améliorations prévues (même idée, plus pro) :**

- **Cartes** : ombres légères, bords arrondis homogènes, espacement interne (padding) plus confortable.
- **Typo** : hiérarchie claire (titres de bloc, libellés, valeurs).
- **Boutons** : états hover/active cohérents, taille et contraste suffisants.
- **Charges d’importation** : afficher un **sous-total** (somme des « Coût total » de toutes les charges du véhicule) dans la carte, pour que l’addition soit visible sans calcul manuel.
- **Identification** : corriger l’affichage si un champ « Pays d’origine » contient une valeur numérique erronée (données existantes) ; garder le même layout.
- **Couleurs / thème** : rester sur les variables CSS existantes (thèmes beige, bleu, etc.) pour garder la même identité, en l’affinant (contraste, états).

Aucun changement de structure (pas de suppression de colonnes ni de blocs), uniquement un rendu plus soigné et lisible.

---

## 4. Tout ce qui manque dans cette vision

Synthèse de ce qui sera traité en même temps :

| Domaine | Manque | Action |
|--------|--------|--------|
| **API** | Rate limiting, CORS | Throttling DRF sur les endpoints REST ; CORS configuré (liste d’origines si besoin). |
| **Audit** | Seulement Véhicule, Location, DocumentVehicule | Étendre les signals à Vente, Depense, Facture, Conducteur, Utilisateurs (création/suppression), paramétrage (Marque, Modele, etc.). |
| **Audit** | Consultation / export par les admins | Vue (ou page admin) pour filtrer et exporter l’historique d’audit (date, utilisateur, modèle). |
| **Audit** | Rétention | Documenter la durée de conservation et, si besoin, une commande ou un script de purge/archivage. |
| **Facture** | Pas de document attaché | Champ `fichier` sur Facture + formulaire + affichage lien téléchargement. |
| **Documents véhicule** | Pas de fichier | Champ `fichier` sur DocumentVehicule + formulaire + affichage. |
| **Démarches import** | Pas de pièce jointe | Champ `fichier` sur ImportDemarche + formulaire + affichage. |
| **Fiche véhicule** | Total des charges d’import non affiché | Calculer et afficher la somme des coûts totaux d’import dans la carte « Charges d’importation ». |
| **Fiche véhicule** | Rendu un peu basique | Amélioration CSS (cartes, espacements, boutons) pour un rendu plus pro, même disposition. |

En faisant tout cela, la fiche véhicule reste dans la même logique (blocs Identification, Démarches, Charges, etc.) tout en étant plus complète (vrais documents, totaux, facture avec fichier et référence de coût) et plus propre visuellement.

---

## 5. Récap des autres champs (est-ce normal ?)

| Champ / entité | Statut | Remarque |
|----------------|--------|----------|
| **Pays d'origine** (véhicule) | Corrigé | C’est un texte libre (nom de pays). Une valeur comme « 200000000 » (prix collé par erreur) est désormais refusée : placeholder « ex. Allemagne, Japon », aide à la saisie, et validation qui rejette une valeur entièrement numérique avec un message clair. |
| **Prix d'achat** | Normal | Saisie manuelle, en FCFA. Pas de calcul automatique (achat unique par véhicule). |
| **Charges d'import** | Normal | Fret + dédouanement + transitaire → **coût total calculé automatiquement** à l’enregistrement. |
| **Relevés carburant** | Normal | Litres × prix = montant (ou champ manquant complété) à l’enregistrement. |
| **Dépenses / Réparations** | Normal | Pas de champ fichier : les justificatifs (factures) se gèrent via l’entité **Facture** (avec fichier PDF) ou en pièce jointe sur une démarche si besoin. |
| **Location** | Normal | Pas de champ fichier pour l’instant ; un champ « Contrat (PDF) » peut être ajouté plus tard si besoin. |
| **Documents véhicule** | Complété | Champ **fichier** ajouté pour attacher le document (carte grise, assurance, etc.). |
| **Démarches import** | Complété | Champ **fichier** (pièce jointe) ajouté. |
| **Facture** | Complété | Champ **fichier** (PDF) ajouté + référence coût total à l’ajout. |

En résumé : les autres champs sont **normaux** (pas de fichier là où la facture ou le document est géré ailleurs). Seul **Pays d'origine** a été renforcé pour éviter la confusion avec un montant.
