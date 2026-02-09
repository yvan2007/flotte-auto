# API JSON FLOTTE

Tous les endpoints renvoient du **JSON** et nécessitent une **session authentifiée** (cookie). Les URLs sont relatives à la racine de l’application (ex. `/dashboard/` → base `/`).

---

## API REST Framework (api/v1/)

- **Marques :** `GET /api/v1/marques/`, `GET /api/v1/marques/<id>/`
- **Modèles :** `GET /api/v1/modeles/`, `GET /api/v1/modeles/<id>/`
- **Véhicules :** `GET /api/v1/vehicules/?q=...&statut=parc`, `GET /api/v1/vehicules/<id>/`
- **Ventes :** `GET /api/v1/ventes/` (manager/admin), `GET /api/v1/ventes/<id>/`
- **Locations :** `GET /api/v1/locations/`, `GET /api/v1/locations/<id>/`
- **Conducteurs :** `GET /api/v1/conducteurs/`, `GET /api/v1/conducteurs/<id>/`
- **CA :** `GET /api/v1/ca/`, `GET /api/v1/ca/evolution/?granularite=mois&annee=2025` (manager/admin)
- **Dashboard :** `GET /api/v1/dashboard/`

Pagination : 20 par page (`?page=2`). **Browsable API :** ouvrir une URL dans le navigateur (connecté).

---

## API JSON légère (api/...) — Paramétrage / formulaires

| Méthode | URL | Rôle | Description |
|--------|-----|------|-------------|
| GET | `/api/marques/` | Tous | Liste des marques (id, nom) — marques non archivées |
| GET | `/api/modeles-par-marque/?marque_id=<id>` | Tous | Liste des modèles pour une marque (id, nom) |

---

## Parc / véhicules

| Méthode | URL | Rôle | Description |
|--------|-----|------|-------------|
| GET | `/api/vehicules/` | Tous | Liste des véhicules (résumé). Query : `statut` (parc \| import \| vendu), `q` (recherche), `limit` (défaut 50, max 200) |
| GET | `/api/vehicules/<id>/` | Tous | Détail d’un véhicule (châssis, marque, modèle, statut, km, prix, nb documents, etc.) |

---

## Ventes et chiffre d’affaires

| Méthode | URL | Rôle | Description |
|--------|-----|------|-------------|
| GET | `/api/ventes/` | Manager/Admin | Liste des ventes. Query : `limit` (défaut 50, max 200) |
| GET | `/api/ca/synthese/` | Manager/Admin | Synthèse CA : `total_ca`, `nb_ventes`, `moyenne_vente` (FCFA) |
| GET | `/ca/api/evolution/?granularite=mois&annee=2025` | Manager/Admin | Évolution du CA pour graphiques. Query : `granularite` (jour \| mois \| annee), `annee`, `mois` (optionnel si granularite=jour). Réponse : `labels`, `data`, `nb_ventes` |

---

## Tableau de bord

| Méthode | URL | Rôle | Description |
|--------|-----|------|-------------|
| GET | `/api/dashboard/kpis/` | Tous | KPIs : `parc`, `import`, `vendus`, `total` (nombre de véhicules) |

---

## Conducteurs et locations

| Méthode | URL | Rôle | Description |
|--------|-----|------|-------------|
| GET | `/api/conducteurs/` | Tous | Liste des conducteurs (id, nom, prenom, email, telephone, actif) |
| GET | `/api/locations/` | Tous | Liste des locations (résumé). Query : `statut` (en_cours \| a_venir \| termine), `limit` |

---

## Exemples

- Liste des véhicules au parc :  
  `GET /api/vehicules/?statut=parc`
- Recherche véhicule :  
  `GET /api/vehicules/?q=ABC123`
- Synthèse CA :  
  `GET /api/ca/synthese/` (réponse : `{"total_ca": 15000000, "nb_ventes": 5, "moyenne_vente": 3000000}`)
- Évolution CA par mois :  
  `GET /ca/api/evolution/?granularite=mois&annee=2025`

Les montants sont en **FCFA**. Les dates sont au format **ISO 8601** (`YYYY-MM-DD`).

---

## Exportations et téléchargements

Exports CSV (réglementaire, charges d’import, locations, audit) et téléchargement des fichiers (rapports journaliers, factures, documents véhicule, démarches import) : voir **[EXPORTATIONS.md](EXPORTATIONS.md)**.
