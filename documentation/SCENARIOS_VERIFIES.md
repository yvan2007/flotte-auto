# Scénarios métier vérifiés

Vérification des cas limites et cohérence de la logique métier.

---

## 1. Véhicule vendu deux fois (ou plusieurs ventes)

- **Modèle** : un véhicule peut avoir plusieurs enregistrements `Vente` (ex. reprise puis revente, ou erreur de saisie).
- **TCO** : on utilise **la dernière vente** (`Vente.Meta.ordering = ['-date_vente']` puis `v.ventes.all()[:1]`). Le prix de vente soustrait est donc celui de la cession la plus récente → cohérent pour le coût total de possession.
- **Workflow** : à la création d’une vente (`VenteCreateView.form_valid`), le véhicule est passé en `statut='vendu'`. Une deuxième vente pour le même véhicule ne serait créée que manuellement (reprise non modélisée) ; le TCO reste correct en prenant la dernière vente.

**Conclusion** : Comportement correct.

---

## 2. Location sans conducteur assigné

- **Modèle** : `Location.conducteur` est `null=True, blank=True`.
- **Formulaire** : champ optionnel, liste des conducteurs actifs avec libellé "—" si vide.
- **Fiche location** : affichage "Conducteur assigné : —" si aucun conducteur.

**Conclusion** : Géré correctement.

---

## 3. Véhicule au parc avec une location en cours

- **Risque** : un véhicule peut être en `statut='parc'` tout en ayant une location `statut='en_cours'` (création de location ne modifiant pas le statut du véhicule). Sans règle, il apparaîtrait à la fois dans les alertes "CT/assurance (locations)" et "CT/assurance (véhicules au parc)".
- **Règle métier** : les alertes "CT/assurance **véhicule** (au parc)" concernent les véhicules réellement disponibles (au parc **sans** location en cours). Les alertes "CT/assurance **location**" concernent les contrats en cours.
- **Correction** : les listes `alertes_ct_vehicule`, `alertes_assurance_vehicule`, `echeances_ct_vehicule` et `echeances_assurance_vehicule` excluent les véhicules qui ont au moins une location avec `statut='en_cours'` (`.exclude(locations__statut='en_cours').distinct()`).

**Conclusion** : Comportement corrigé, plus de doublon.

---

## 4. Document : type liste + type libre (Autre)

- Si l’utilisateur choisit un type dans la liste **et** remplit "Type (si Autre)", les deux sont enregistrés. L’affichage utilise `libelle_type` → priorité au type liste. Pas de conflit.
- Validation : au moins un des deux (type liste ou type libre) doit être renseigné ; le type libre est trimé (espaces seuls = vide).

**Conclusion** : Comportement correct.

---

## 5. Export réglementaire : véhicule avec ou sans location

- Véhicules filtrés : `statut__in=['parc', 'import']`.
- Pour chaque véhicule : `loc_en_cours = v.locations.filter(statut='en_cours').first()`. Colonnes "Location en cours", "Locataire", "CT (location)", "Assurance (location)" renseignées si une location en cours existe, sinon "Non" et champs vides.

**Conclusion** : Comportement correct.

---

## 6. Vente : mise à jour du statut véhicule

- À la création d’une vente (`VenteCreateView.form_valid`), `vehicule.statut` est mis à `'vendu'`. Le véhicule n’apparaît plus dans le parc ni dans l’export réglementaire (filtré sur parc/import).

**Conclusion** : Cohérent.
