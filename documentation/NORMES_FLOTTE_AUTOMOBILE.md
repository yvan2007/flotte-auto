# Recommandations — Normes flotte automobile

Ce document liste les bonnes pratiques et normes courantes en **gestion de flotte automobile**, et ce que l’application FLOTTE couvre déjà ou peut ajouter pour un usage professionnel.

---

## Est-ce complet et professionnel ?

**Oui, pour un usage courant.** L’application est déjà **complète et correcte** pour une gestion de flotte professionnelle « classique » :

- **Parc & véhicules** : châssis, km, statut, documents, maintenance, carburant, réparations, ventes.
- **Locations** : CT, assurance, km vidange, contraventions.
- **Conformité** : page Échéances (90 j), alertes dashboard (CT, assurance, permis, documents).
- **Rôles** : Admin, Gestionnaire, Utilisateur.
- **CA, import, API, thèmes.**

Les points listés ci‑dessous sont des **améliorations optionnelles** selon le niveau d’exigence (audit, assurance, très gros parcs) : assignation conducteur, types de documents paramétrables, TCO, export, audit log. Tu peux les ajouter plus tard si besoin.

---

## Déjà en place dans FLOTTE

| Domaine | Élément | Statut |
|--------|--------|--------|
| **Véhicule** | Numéro de châssis (identifiant unique) | ✅ |
| **Véhicule** | Kilométrage, date entrée parc, statut (parc / import / vendu) | ✅ |
| **Véhicule** | Données techniques (carburant, transmission, type, CO2, puissance fiscale) | ✅ |
| **Documents** | Documents par véhicule avec type, n°, dates émission/échéance | ✅ |
| **Location** | CT (contrôle technique) et assurance avec dates d’expiration | ✅ |
| **Location** | Km prochaine vidange, loyer, km inclus, pénalités (contraventions) | ✅ |
| **Conducteurs** | Permis (n°, date expiration), contact, actif | ✅ |
| **Maintenance** | Types (vidange, courroie, pneus, filtres, plaquettes, batterie), date prévue/effectuée, km, coût | ✅ |
| **Carburant** | Relevés (date, km, litres, montant, prix/litre) | ✅ |
| **Alertes** | CT et assurance (locations) dans les 30 jours sur le tableau de bord | ✅ |
| **Rôles** | Admin, Gestionnaire, Utilisateur (droits différenciés) | ✅ |
| **CA / Rapports** | Chiffre d’affaires, évolution, rapports PDF | ✅ |
| **Import** | Démarches, charges (fret, dédouanement, transitaire), parties importées | ✅ |

---

## À ajouter pour se rapprocher des normes flotte

### Priorité haute (conformité et sécurité)

1. **Page « Échéances » consolidée** ✅ *En place*  
   Une seule page (`/echeances/`) listant toutes les échéances sur 90 jours :
   - CT (locations en cours)
   - Assurance (locations en cours)
   - **Documents véhicule** (date d’échéance)
   - **Permis conducteurs** (expiration)
   - **Maintenance préventive** (à faire, date prévue)  
   → Limite les oublis et répond aux exigences de traçabilité.

2. **Alertes permis et documents sur le tableau de bord** ✅ *En place*  
   En plus des alertes CT/assurance :
   - Conducteurs dont le **permis expire** dans les 30 jours.
   - **Documents** dont la date d’échéance est dans les 30 jours.  
   → Bonnes pratiques flotte et risque routier.

3. **Assignation conducteur ↔ location** ✅ *En place*  
   Lien explicite : quel conducteur est assigné à quelle location (ou à quel véhicule sur une période).  
   - Responsabilité en cas d’accident ou de contravention.  
   - Conformité « qui conduit quoi ».  
   → Modèle : `Location.conducteur` (ForeignKey vers `Conducteur`, optionnel) ou table d’assignation véhicule/conducteur/période.

4. **Types de documents normalisés** ✅ *En place*  
   Liste de types prédéfinis (ex. : Carte grise, Assurance, Contrôle technique, Vignette, …) avec possibilité d’en ajouter.  
   → Paramétrage (table `TypeDocument` ou liste fixe) + champs document avec échéance pour rappels.

### Priorité moyenne (pilotage et coûts)

5. **Coût total de possession (TCO) par véhicule** ✅ *En place*  
   Indicateur : coût d’acquisition (achat + import) + entretien + carburant + autres dépenses − produit de vente.  
   → Vue ou rapport « Coût par véhicule » / « TCO ».

6. **Rappels maintenance basés sur km** ✅ *En place*  
   Sur la page Échéances : section « Vidange — Km atteint ou dépassé » (véhicules au parc et locations en cours).

7. **CT / Assurance au niveau véhicule** ✅ *En place*  
   Champs `date_expiration_ct` et `date_expiration_assurance` sur le véhicule. Alertes sur le tableau de bord et page Échéances (véhicules au parc).

### Priorité basse (optionnel)

8. **Historique kilométrage**  
   Courbe ou tableau « km dans le temps » par véhicule (à partir des relevés carburant, maintenance, locations).  
   → Utile pour litiges ou analyse d’usage.

9. **Export réglementaire** ✅ *En place*  
   **Export réglementaire** (lien sur la page TCO, ou `/export-reglementaire/`) : CSV avec châssis, immat, CT, assurance, locataire (manager/admin).

10. **Traçabilité des modifications (audit log)** ✅ *En place*  
    Modèle `AuditLog` + signals sur Véhicule, Location, DocumentVehicule (création, modification, suppression). Consultation dans l’admin Django.

11. **Politique de maintenance**  
    Règles par type (ex. vidange tous les 15 000 km ou 12 mois) pour générer automatiquement les prochaines échéances.

---

## Synthèse des actions recommandées

| Action | Impact | Complexité |
|--------|--------|------------|
| Page **Échéances** (CT, assurance, documents, permis, maintenance) | Élevé | Faible |
| Alertes **permis** et **documents** sur le dashboard | Élevé | Faible |
| **Conducteur** assigné à la location | Élevé | Moyenne (migration + formulaires) |
| Types de documents **paramétrables** | Moyen | Faible |
| **TCO** par véhicule (vue/rapport) | Moyen | Moyenne |
| CT/Assurance au niveau **véhicule** | Moyen | Moyenne (migration) |
| **Audit log** | Conformité | Élevée |

En mettant en place la **page Échéances**, les **alertes permis + documents** et l’**alerte vidange (km)**, l’application respecte les principales attentes des normes flotte automobile (contrôles, échéances, conducteurs, documents, maintenance).
