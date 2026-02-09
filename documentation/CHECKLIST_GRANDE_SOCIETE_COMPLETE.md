# Checklist complète — Niveau « grande société » (final)

Liste **exhaustive** de tout ce qu’il faut ajouter ou renforcer pour que FLOTTE soit **complet et final** au niveau entreprise. Chaque point est actionnable (quoi faire, où, pourquoi).

---

## 1. Sécurité HTTP et cookies

| # | Élément | À faire | Où | Priorité |
|---|--------|---------|-----|----------|
| 1.1 | **HTTPS forcé en production** | Activer `SECURE_SSL_REDIRECT=True` quand `DEBUG=False` (déjà conditionnel dans `settings.py`). S’assurer que le reverse proxy (Nginx/Apache) ou le load balancer termine le SSL et envoie `X-Forwarded-Proto: https`. | `settings.py` / `.env` | Haute |
| 1.2 | **En-têtes de sécurité** | Ajouter `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` (ex. 31536000, True, True) en production pour forcer le navigateur à n’utiliser que HTTPS. | `settings.py` | Haute |
| 1.3 | **Content-Type / X-Content-Type-Options** | S’assurer que les réponses ne sont pas interprétées en MIME sniffing. Django gère déjà une partie ; ajouter un middleware ou des headers dans le reverse proxy : `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`. | Middleware ou Nginx | Moyenne |
| 1.4 | **Référentiel de contenu (CSP)** | Optionnel mais recommandé : définir une politique Content-Security-Policy (limiter scripts, styles, sources) pour réduire les risques XSS. | Middleware ou Nginx | Basse |

---

## 2. Authentification et accès

| # | Élément | À faire | Où | Priorité |
|---|--------|---------|-----|----------|
| 2.1 | **Rate limiting sur le login** | Limiter le nombre de tentatives de connexion par IP (ex. 5 par 15 min) pour éviter le brute-force. Utiliser `django-ratelimit` ou un middleware custom qui compte les échecs et renvoie 429 ou bloque temporairement. | Vue login / middleware | Haute |
| 2.2 | **Verrouillage de compte après N échecs** | Après X tentatives échouées pour un même identifiant, désactiver le compte ou imposer un délai (ex. 30 min). Soit via `django-axes`, soit en stockant les échecs (modèle ou cache) et en vérifiant dans le formulaire de login. | Vue login / modèle ou cache | Haute |
| 2.3 | **Expiration de session / inactivité** | Déjà en place : `SESSION_COOKIE_AGE`. Optionnel : raccourcir en cas d’inactivité (ex. 2 h sans requête) avec `SESSION_SAVE_EVERY_REQUEST=True` (déjà fait) et une durée plus courte, ou implémenter une déconnexion automatique côté front. | `settings.py` | Moyenne |
| 2.4 | **Déconnexion unique (invalidation session)** | Permettre à l’admin de « déconnecter » un utilisateur (supprimer sa session). Soit en supprimant les entrées dans `Session` pour cet `user_id`, soit en ajoutant une vue admin « Révoquer les sessions de cet utilisateur ». | Admin / vue dédiée | Moyenne |

---

## 3. Logging et traçabilité

| # | Élément | À faire | Où | Priorité |
|---|--------|---------|-----|----------|
| 3.1 | **Logging vers fichier avec rotation** | Configurer un handler `RotatingFileHandler` ou `TimedRotatingFileHandler` pour les logs (erreurs, accès sensibles). Éviter que les fichiers grossissent indéfiniment. | `settings.py` → `LOGGING` | Haute |
| 3.2 | **Niveau et modules** | Séparer niveaux par logger : `flotte` en INFO, `django.request` en WARNING (ou ERROR pour 5xx), `django.security` en WARNING. | `settings.py` → `LOGGING` | Haute |
| 3.3 | **Log des requêtes sensibles** | Logger (sans mots de passe) : tentatives de login (succès/échec, user, IP), accès aux vues admin/paramétrage, modifications critiques (déjà partiel via AuditLog). | Middleware ou vues login / signals | Moyenne |
| 3.4 | **Format structuré (JSON)** | Pour intégration avec un outil (ELK, Datadog, etc.) : formatter les logs en JSON (message, level, timestamp, user, path, status_code). | `settings.py` → `LOGGING` formatter | Basse |

---

## 4. Gestion des erreurs (pages et handlers)

| # | Élément | À faire | Où | Priorité |
|---|--------|---------|-----|----------|
| 4.1 | **Page 404 personnalisée** | Créer une vue `page_not_found` et un template `404.html` (message clair, lien retour, sans détail technique). Déclarer `handler404` dans `urls.py` racine. | `flotte/views.py` + `templates/404.html` + `urls.py` | Haute |
| 4.2 | **Page 500 personnalisée** | Créer une vue `server_error` et un template `500.html` (message générique « Une erreur s’est produite », pas de traceback). Déclarer `handler500` dans `urls.py` racine. | `flotte/views.py` + `templates/500.html` + `urls.py` | Haute |
| 4.3 | **Page 403 (PermissionDenied)** | Créer une vue et un template `403.html` pour les accès refusés (rôle insuffisant). Déclarer `handler403`. | Idem | Moyenne |
| 4.4 | **Désactiver le DEBUG en production** | S’assurer que `DEBUG=False` en prod (via `DJANGO_DEBUG=0` ou variable d’environnement). Ne jamais exposer les tracebacks aux utilisateurs. | `.env` / déploiement | Haute |

---

## 5. Base de données et sauvegardes

| # | Élément | À faire | Où | Priorité |
|---|--------|---------|-----|----------|
| 5.1 | **Base de données production** | Remplacer SQLite par PostgreSQL (ou MySQL) en production : meilleure concurrence, sauvegardes, fiabilité. Configurer `DATABASES` via variables d’environnement (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`). | `settings.py` + `.env` | Haute |
| 5.2 | **Sauvegardes régulières** | Mettre en place des sauvegardes automatiques (dump quotidien, rétention 7–30 jours). Script cron ou tâche planifiée (Celery, systemd timer) qui exécute `pg_dump` ou équivalent. | Script + cron / orchestration | Haute |
| 5.3 | **Migrations en déploiement** | Documenter et automatiser : `python manage.py migrate` avant redémarrage de l’app après déploiement. Éviter les migrations manuelles hasardeuses en prod. | Procédure / CI-CD | Haute |

---

## 6. Déploiement et exécution

| # | Élément | À faire | Où | Priorité |
|---|--------|---------|-----|----------|
| 6.1 | **Fichiers statiques en production** | Exécuter `collectstatic` et servir les statiques via Nginx (ou CDN), pas via Django en prod. Configurer `STATIC_ROOT` et `STATIC_URL`. | Déploiement / Nginx | Haute |
| 6.2 | **Médias (uploads)** | Servir les fichiers uploadés (rapports, documents) via le serveur web ou un stockage dédié (S3, etc.), avec contrôle d’accès (authentification). | `MEDIA_ROOT` / Nginx / storage | Moyenne |
| 6.3 | **ALLOWED_HOSTS** | En production, définir explicitement les noms de domaine autorisés (pas de `*`). Ex. `ALLOWED_HOSTS=app.flotte.com,flotte.com`. | `.env` | Haute |
| 6.4 | **Secret key forte** | Générer une clé aléatoire longue (ex. `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) et la mettre dans `.env` ; ne jamais commiter la clé prod. | `.env` | Haute |
| 6.5 | **Serveur WSGI/ASGI** | Utiliser Gunicorn (ou uWSGI) + Nginx en production, pas `runserver`. Documenter la commande de démarrage et le nombre de workers. | Procédure / systemd / Docker | Haute |

---

## 7. API et exposition

| # | Élément | À faire | Où | Priorité |
|---|--------|---------|-----|----------|
| 7.1 | **Rate limiting sur l’API** | Limiter le nombre de requêtes par utilisateur ou par IP sur les endpoints REST (ex. 100 req/min). Éviter les abus. | DRF throttling / middleware | Moyenne |
| 7.2 | **Versioning d’API** | Si l’API évolue, documenter une version (ex. `/api/v1/`) et prévoir une stratégie de rétrocompatibilité. | `urls.py` / doc API | Basse |
| 7.3 | **CORS** | Si l’API est appelée depuis un autre domaine (front SPA, mobile), configurer `django-cors-headers` avec une liste blanche d’origines (pas `*` en prod). | `settings.py` | Moyenne (si besoin) |

---

## 8. Audit et conformité

| # | Élément | À faire | Où | Priorité |
|---|--------|---------|-----|----------|
| 8.1 | **Étendre l’audit log** | Enregistrer aussi les modifications sur Vente, Depense, Facture, Conducteur, Utilisateurs (création/suppression de compte), Paramétrage (marques, modèles). | `signals.py` (post_save, post_delete) | Moyenne |
| 8.2 | **Export / consultation de l’audit** | Permettre aux admins de consulter et exporter l’historique (liste filtrée par date, utilisateur, modèle) depuis l’admin ou une vue dédiée. | Admin ou vue `flotte` | Moyenne |
| 8.3 | **Rétention des logs d’audit** | Définir une durée de conservation (ex. 2 ans) et une procédure d’archivage ou de purge (RGPD si données personnelles). | Politique / script | Basse |

---

## 9. Santé et disponibilité

| # | Élément | À faire | Où | Priorité |
|---|--------|---------|-----|----------|
| 9.1 | **Health check** | Exposer une URL (ex. `/health/` ou `/ping/`) qui renvoie 200 si l’app et la DB répondent. Utile pour les load balancers et la surveillance. | Vue + `urls.py` | Moyenne |
| 9.2 | **Timeouts** | Configurer les timeouts DB et HTTP côté serveur (Gunicorn, Nginx) pour éviter les blocages prolongés. | Gunicorn / Nginx | Moyenne |
| 9.3 | **Monitoring (optionnel)** | Intégrer un outil (Sentry, New Relic, Prometheus) pour tracer les erreurs 500 et les performances. | Sentry SDK / middleware | Basse |

---

## 10. Documentation et procédures

| # | Élément | À faire | Où | Priorité |
|---|--------|---------|-----|----------|
| 10.1 | **README déploiement** | Documenter : prérequis, variables d’environnement obligatoires, commandes (migrate, collectstatic), démarrage du serveur, vérification post-déploiement. | `README.md` ou `documentation/DEPLOIEMENT.md` | Haute |
| 10.2 | **.env.example à jour** | Lister toutes les variables utilisées (SECRET_KEY, DEBUG, ALLOWED_HOSTS, DB_*, EMAIL_*, LOGGING_*, etc.) avec des exemples sans valeurs réelles. | `.env.example` | Haute |
| 10.3 | **Runbook incidents** | Court document : que faire en cas de 500 (logs, redémarrage), de base corrompue (restauration backup), de pic de charge. | `documentation/RUNBOOK.md` | Moyenne |

---

## Synthèse par priorité

- **Haute** (indispensable pour une prod « grande société ») : 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, 4.4, 5.1, 5.2, 5.3, 6.1, 6.3, 6.4, 6.5, 10.1, 10.2.
- **Moyenne** (recommandé) : 1.3, 2.3, 2.4, 3.3, 4.3, 6.2, 7.1, 7.3, 8.1, 8.2, 9.1, 9.2, 10.3.
- **Basse** (optionnel) : 1.4, 3.4, 8.3, 9.3, 7.2.

En mettant en place **tous les points haute priorité** et les **moyenne** pertinents pour votre contexte, l’application peut être considérée **complète et finale** au niveau « grande société ». Les points **basse** renforcent encore la maturité (CSP, logs JSON, monitoring, rétention audit).
