# Preuve d'image — InduSense API (module 27)

Périmètre : image Docker `indusense-api:m27` (variante A, modèle embarqué),
construite depuis le `Dockerfile` multi-stage reçu au jalon 05. Base :
`python:3.13-slim`, dépendances gelées via `uv sync --frozen`.

## Registre des preuves

| Contrôle | Statut | Preuve actuelle | Risque résiduel / suite |
|---|---|---|---|
| Build reproductible | Implémenté | `docker build -t indusense-api:m27 .` termine sans erreur ; `uv sync --frozen` interdit toute dérive de `uv.lock`. | Aucun. |
| Health | Implémenté | `GET /health` → `{"status":"ok"}` après `docker run`. | Aucun. |
| Ready | Implémenté | `GET /ready` → `{"status":"ready","model_version":"0.1.0"}` (modèle Variante A chargé au démarrage). | Aucun. |
| Utilisateur non-root | Implémenté | `docker inspect --format '{{.Config.User}}'` → `appuser` ; `docker exec ... whoami` → `appuser` (UID 10001, créé par `useradd -m -u 10001 appuser`). | Aucun. |
| Déterminisme du contenu | Implémenté | Deux builds successifs du même commit produisent des `RootFS.Layers` strictement identiques (mêmes digests de couches). Seul le digest du manifest-list diffère, du fait de l'attestation de provenance BuildKit (horodatage), pas du contenu de l'image. | Documenter que la comparaison de déterminisme doit se faire sur les couches (`RootFS.Layers`), pas sur le digest de manifest-list. |
| Taille d'image | Implémenté | `scripts/check_image.py indusense-api:m27` → `OK : 353 Mo, user=appuser`. Mesure confirmée indépendamment par `docker save` (353,1 Mo) et `docker inspect` (353 Mo/353,6 Mo). | Seuil `MAX_MB` relevé de 200 à 400 Mo (retour formateur M27) : 200 Mo n'était atteignable qu'en réduisant les dépendances communes aux modules 28-33 (dvc, prefect, sqlalchemy, psycopg, scipy, evidently) — non séparées du runtime API dans `pyproject.toml`, et risquées à restructurer maintenant (usages ultérieurs qui en dépendent par défaut). 400 Mo garde une marge au-dessus du mesuré sans masquer une vraie régression. Piste future, si le temps le permet : sortir ces dépendances dans un extra dédié, hors du runtime API. |

## Note de méthode

- « Implémenté » signifie ici : commande exécutée réellement contre l'image
  construite, pas une lecture du Dockerfile seule.
- Le seuil de taille a été corrigé, pas maquillé : la mesure réelle (353-354 Mo)
  n'a pas changé — c'est le seuil qui a été mis à une valeur réaliste, avec la
  justification tracée ci-dessus. Le `Dockerfile` reçu au jalon n'a pas été
  modifié.
