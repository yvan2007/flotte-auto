# Exportations et téléchargement de fichiers — FLOTTE

Récapitulatif des **exports** (CSV) et **téléchargements de fichiers** dans l’application.

---

## 1. Exports CSV (données)

Tous les exports CSV sont en **UTF-8 avec BOM** (ouverture correcte dans Excel), séparateur **point-virgule** (`;`). Accès réservé **Manager ou Admin** sauf mention contraire.

| Export | URL / accès | Contenu du fichier |
|--------|-------------|--------------------|
| **Export réglementaire** | TCO → « Export réglementaire (CSV) » ou `/export-reglementaire/` | Véhicules (parc + import) : châssis, immat, marque, modèle, km, CT véhicule, assurance véhicule, location en cours (oui/non), locataire, CT location, assurance location. Pour contrôle réglementaire. |
| **Charges d’import** | TCO → « Export charges d'import (CSV) » ou `/export-charges-import/` | Toutes les charges d’importation : châssis, fret, dédouanement, transitaire, coût total (FCFA), remarque. |
| **Locations** | TCO ou Location → « Export locations (CSV) » / « Exporter en CSV » ou `/export-locations/` | Liste des locations : véhicule, châssis, locataire, type, dates début/fin, loyer, frais annexes, **coût total** (loyer + frais + contraventions), statut. |
| **Audit** | Paramétrage → Audit → « Exporter CSV » (avec filtres date, utilisateur, modèle) | Journal d’audit : date, utilisateur, action (création/modification/suppression), modèle, ID objet, représentation. Réservé **Admin**. |

---

## 2. Téléchargement de fichiers (PDF, documents)

| Fichier | Où | Comment |
|---------|-----|--------|
| **Rapport journalier / document CA** | Chiffre d’affaires → liste des rapports | Clic sur le lien du rapport → téléchargement du **PDF** uploadé (`rapport_download`). |
| **Facture (PDF)** | Fiche véhicule → section Factures | Lien « PDF » à côté de chaque facture ayant un fichier attaché → ouvre ou télécharge le fichier. |
| **Document véhicule** (carte grise, assurance, CT, etc.) | Fiche véhicule → section Documents | Lien « Fichier » à côté de chaque document ayant un fichier attaché. |
| **Démarche import** (PV, attestation, etc.) | Fiche véhicule → section Démarches import | Lien « Document » à côté de chaque démarche ayant une pièce jointe. |

Les liens des factures, documents véhicule et démarches import pointent vers l’URL média (ex. `/media/...`) ; le navigateur ouvre ou propose le téléchargement selon le type de fichier.

---

## 3. Récap technique

- **Exports CSV** : vues `export_reglementaire`, `export_charges_import`, `export_locations`, `audit_list` (avec `?export=csv`). Noms de fichiers : `flotte_export_reglementaire.csv`, `flotte_charges_import.csv`, `flotte_locations.csv`, `audit_flotte_YYYYMMDD_HHMM.csv`.
- **Téléchargement rapport** : vue `rapport_download(pk)` → `FileResponse` du fichier `RapportJournalier.fichier`.
- **Fichiers sur fiche véhicule** : servis par Django (MEDIA_URL) ; pas de vue dédiée, lien direct `{{ obj.fichier.url }}`.

Pour ajouter un export (ex. ventes, dépenses) : créer une vue CSV avec `HttpResponse(content_type='text/csv; charset=utf-8')`, en-tête `Content-Disposition: attachment; filename="..."`, et ajouter le lien dans le menu ou la page concernée.
