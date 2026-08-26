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
| Taille d'image | **Non conforme** | `scripts/check_image.py indusense-api:m27` → `ECHEC : taille 354 Mo > 200 Mo`. Le contrôle utilisateur du même script passe (`user=appuser`). | Seuil `MAX_MB=200` du script non atteint avec les dépendances actuelles (scikit-learn/statsmodels pèsent lourd même en image slim). Dépassement assumé et documenté pour ce jalon, aucune réduction de couche effectuée. Piste future : évaluer un stage `runtime` sans `statsmodels`/deps de dev transitives, ou relever le seuil si jugé irréaliste pour ce projet. |

## Note de méthode

- « Implémenté » signifie ici : commande exécutée réellement contre l'image
  construite, pas une lecture du Dockerfile seule.
- Le dépassement de taille est un constat, pas un correctif : le `Dockerfile`
  reçu au jalon n'a pas été modifié pour ce TP.
