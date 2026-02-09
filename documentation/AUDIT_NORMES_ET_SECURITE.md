# Audit normes et sécurité — FLOTTE

Ce document indique ce qui est **en ordre** et ce qui **manque ou est à renforcer** pour un niveau « grandes sociétés » (sessions, sécurité, traçabilité). **Soyez honnête avec vous-même** : tout n’est pas parfait partout ; ce qui manque est listé clairement.

---

## 1. Ce qui est en ordre (déjà en place)

| Point | Détail |
|--------|--------|
| **Sessions** | `django.contrib.sessions` + `SessionMiddleware` : sessions activées, cookie de session. |
| **CSRF** | `CsrfViewMiddleware` : protection CSRF sur les formulaires. |
| **Authentification** | `AuthenticationMiddleware`, `LOGIN_URL`, redirections login/logout. |
| **Mots de passe** | Validateurs Django (longueur, similarité, mots courants, numérique). |
| **Permissions** | Rôles (admin, gestionnaire, utilisateur), mixins, décorateurs, filtrage par rôle. |
| **Secrets** | Clé et config sensibles via variables d’environnement / `.env` (pas en dur). |
| **Traçabilité** | `AuditLog` + middleware + signals sur Véhicule, Location, DocumentVehicule. |
| **Gestion d’erreurs** | Try/except + messages utilisateur + logging sur ventes, formulaire vente, `user_role`. |
| **Données sensibles** | Pas de log de mots de passe ; emails avec backend configurable (SMTP/console). |
| **XFrame** | `XFrameOptionsMiddleware` : protection clickjacking. |

Donc sur **sessions, CSRF, auth, rôles, audit, erreurs et secrets**, l’essentiel est en place pour un usage professionnel courant.

---

## 2. Ce qui manque ou n’est pas « norme grandes sociétés »

Ces points sont **optionnels** selon l’environnement (dev vs production, niveau d’exigence).

| Point | Manque / risque | Recommandation |
|--------|------------------|-----------------|
| **Sessions en production** | Pas de `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_SAVE_EVERY_REQUEST` explicites. En HTTP, le cookie de session peut être lu. | En **production (HTTPS)** : définir dans `settings.py` ou `.env` : `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`, et éventuellement `SESSION_SAVE_EVERY_REQUEST=True`. |
| **Cookies / HTTPS** | Pas de `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_PROXY_SSL_HEADER` en config. | En production derrière HTTPS : activer ces réglages pour forcer HTTPS et cookies sécurisés. |
| **LOGGING** | Aucune config `LOGGING` dans `settings.py`. Les `logger` du code utilisent la config par défaut (souvent console uniquement). | Pour un niveau « entreprise » : configurer `LOGGING` (fichiers, rotation, niveaux par module) pour tracer les erreurs et les accès sensibles. |
| **Gestion 500/404** | Pas de handlers personnalisés `handler500` / `handler404`. | Optionnel : vues + templates dédiés pour une page d’erreur propre (sans fuite d’info technique). |
| **Rate limiting** | Pas de limitation du nombre de requêtes (login, API). | Optionnel : middleware ou décorateur (ex. `django-ratelimit`) sur login et endpoints sensibles. |

En résumé : **tout n’est pas au niveau « grande société »** (sessions sécurisées en prod, logging structuré, HTTPS forcé). Pour un usage interne ou une petite structure, l’existant est **suffisant**. Pour un déploiement critique ou un audit strict, il faut ajouter les réglages ci‑dessus.

---

## 3. Synthèse honnête

- **Oui**, l’application est **dans les normes** pour : sessions, CSRF, auth, rôles, traçabilité (audit), gestion d’erreurs sur les parties sensibles, pas de secrets en dur.
- **Non**, ce n’est **pas encore 100 % « grandes sociétés »** : cookies de session/CSRF sécurisés en prod, logging centralisé, HTTPS forcé et rate limiting ne sont pas en place. Ce sont des **compléments à prévoir** si vous visez ce niveau.

**Mis en place à la suite de l’audit** (dans `settings.py`) :
- **Sessions** : `SESSION_COOKIE_HTTPONLY=True`, `SESSION_SAVE_EVERY_REQUEST=True`, `SESSION_COOKIE_AGE` (12 h). En production (`DEBUG=False`) : `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, et optionnellement `SECURE_SSL_REDIRECT` / `SECURE_PROXY_SSL_HEADER`.
- **LOGGING** : config de base (console, niveau INFO pour `flotte`, WARNING pour la racine).

**Liste complète pour tout finaliser** : voir **`CHECKLIST_GRANDE_SOCIETE_COMPLETE.md`** — tout ce qu’il faut ajouter (sécurité, logging, erreurs 404/500, DB prod, sauvegardes, déploiement, rate limiting, audit, health check, doc) avec priorité haute / moyenne / basse.
