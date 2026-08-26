# Preuve Compose — stack API / Prometheus / Grafana (module 28)

Périmètre : `compose.yaml` (3 services : `api` construit depuis le `Dockerfile`
du jalon 05, `prometheus:v3.1.0`, `grafana:11.4.0`), scrape config
`monitoring/prometheus.yml`, provisioning datasource
`monitoring/grafana/provisioning/datasources/prometheus.yml`, smoke test
`tests/test_smoke_compose.py`.

## Registre des preuves

| Contrôle | Statut | Preuve actuelle | Risque résiduel / suite |
|---|---|---|---|
| Config valide | Implémenté | `docker compose config -q` termine sans erreur ni avertissement. | Aucun. |
| Build + démarrage | Implémenté | `docker compose up -d --build` construit l'image API puis crée les 3 conteneurs sans erreur. | Aucun. |
| Readiness gating (api → prometheus) | Implémenté | `docker compose ps` / logs de `up` montrent l'ordre réel : `api-1 Healthy` **avant** `prometheus-1 Starting` (depends_on: api, condition: service_healthy). | Aucun. |
| Readiness gating (prometheus → grafana) | Implémenté | Mêmes logs : `prometheus-1 Healthy` **avant** `grafana-1 Started` (depends_on: prometheus, condition: service_healthy). | Aucun. |
| Healthchecks des 3 services | Implémenté | `docker compose ps` → `api-1`, `prometheus-1`, `grafana-1` tous `Up ... (healthy)` après démarrage complet. | Aucun. |
| Scrape Prometheus réussi | Implémenté | `tests/test_smoke_compose.py::test_prometheus_scraped_api_successfully` interroge `GET /api/v1/targets` et vérifie `health == "up"` pour le job `indusense-api`. Juste après le démarrage la cible peut afficher `unknown` (premier scrape pas encore joué) : le test retente jusqu'à `up`, ce qui est la preuve la plus directe que Prometheus n'a pas tapé une API pas encore chargée. | Aucun. |
| Smoke test complet | Implémenté | `uv run pytest tests/test_smoke_compose.py -q` → `5 passed` contre la stack réellement lancée (`/health`, `/ready`, `/-/ready` Prometheus, `/api/health` Grafana, cible scrapée). | Aucun. |
| Volumes persistants | Implémenté | `prometheus_data` et `grafana_data` déclarés en volumes nommés (survivent à `docker compose down` sans `-v`) ; `docker compose ps -a` après `down` ne montre plus aucun conteneur, `docker volume ls` conserve les deux volumes. | Aucun. |
| Robustesse hors stack | Implémenté | `uv run pytest -q` (sans `docker compose up`) ne casse pas la suite générale : chaque test du smoke se `SKIP` proprement dès le premier `ConnectionError`, au lieu d'échouer ou d'attendre le budget complet de 60s. | Aucun. |
| `docker compose down` | Implémenté | Conteneurs et réseau supprimés proprement, sans erreur ; réseau `..._default` et les 3 conteneurs disparaissent de `docker compose ps -a`. | Aucun. |

## Note de méthode

- « Implémenté » signifie ici : commande exécutée réellement contre la stack
  lancée (build + up + ps + pytest + down), pas une lecture du `compose.yaml`
  seule.
- La preuve d'ordonnancement (readiness gating) s'appuie sur les logs
  d'événements de `docker compose up` (séquence `Healthy` avant le `Starting`
  suivant), pas seulement sur la présence de `depends_on` dans le fichier.
