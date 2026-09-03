# Preuve Compose — stack DB / API / Prometheus / Grafana (module 28)

Périmètre : `compose.yaml` (4 services : `db` en `postgres:16`, `api`
construit depuis le `Dockerfile` du jalon 05, `prometheus:v3.1.0`,
`grafana:11.4.0`), scrape config `monitoring/prometheus.yml`, provisioning
datasource `monitoring/grafana/provisioning/datasources/prometheus.yml`,
smoke test `tests/test_smoke_compose.py`.

## Registre des preuves

| Contrôle | Statut | Preuve actuelle | Risque résiduel / suite |
|---|---|---|---|
| Config valide | Implémenté | `docker compose config -q` termine sans erreur ni avertissement. | Aucun. |
| Build + démarrage | Implémenté | `docker compose up -d --build` construit l'image API puis crée les 4 conteneurs sans erreur. | Aucun. |
| Readiness gating (db → api) | Implémenté | `docker compose ps` / logs de `up` montrent l'ordre réel : `db-1 Healthy` **avant** `api-1 Starting` (depends_on: db, condition: service_healthy ; healthcheck `pg_isready -U postgres`). | Aucun. |
| Readiness gating (api → prometheus) | Implémenté | `docker compose ps` / logs de `up` montrent l'ordre réel : `api-1 Healthy` **avant** `prometheus-1 Starting` (depends_on: api, condition: service_healthy). | Aucun. |
| Readiness gating (prometheus → grafana) | Implémenté | Mêmes logs : `prometheus-1 Healthy` **avant** `grafana-1 Started` (depends_on: prometheus, condition: service_healthy). | Aucun. |
| Healthchecks des 4 services | Implémenté | `docker compose ps` → `db-1`, `api-1`, `prometheus-1`, `grafana-1` tous `Up ... (healthy)` après démarrage complet. | Aucun. |
| Scrape Prometheus réussi | Implémenté | `tests/test_smoke_compose.py::test_prometheus_scraped_api_successfully` interroge `GET /api/v1/targets` et vérifie `health == "up"` pour le job `indusense-api`. Juste après le démarrage la cible peut afficher `unknown` (premier scrape pas encore joué) : le test retente jusqu'à `up`, ce qui est la preuve la plus directe que Prometheus n'a pas tapé une API pas encore chargée. | Aucun. |
| Smoke test complet | Implémenté | `uv run pytest tests/test_smoke_compose.py -q` → `5 passed` contre la stack réellement lancée (`/health`, `/ready`, `/-/ready` Prometheus, `/api/health` Grafana, cible scrapée). | Aucune assertion dédiée à `db` dans le smoke test actuel — la lecture réelle en base reste un chantier du module 30 (accès SQLAlchemy). |
| Volumes persistants | Implémenté | `pgdata`, `prometheus_data` et `grafana_data` déclarés en volumes nommés (survivent à `docker compose down` sans `-v`) ; `docker compose ps -a` après `down` ne montre plus aucun conteneur, `docker volume ls` conserve les trois volumes. | Aucun. |
| Robustesse hors stack | Implémenté | `uv run pytest -q` (sans `docker compose up`) ne casse pas la suite générale : chaque test du smoke se `SKIP` proprement dès le premier `ConnectionError`, au lieu d'échouer ou d'attendre le budget complet de 60s. | Aucun. |
| `docker compose down` | Implémenté | Conteneurs et réseau supprimés proprement, sans erreur ; réseau `..._default` et les 4 conteneurs disparaissent de `docker compose ps -a`. | Aucun. |

## Note de méthode

- « Implémenté » signifie ici : commande exécutée réellement contre la stack
  lancée (build + up + ps + pytest + down), pas une lecture du `compose.yaml`
  seule.
- La preuve d'ordonnancement (readiness gating) s'appuie sur les logs
  d'événements de `docker compose up` (séquence `Healthy` avant le `Starting`
  suivant), pas seulement sur la présence de `depends_on` dans le fichier.

## Retour formateur

Le `compose.yaml` publié ne déclarait que `api`/`prometheus`/`grafana` : le
guide attend aussi un service `db` (`postgres:16`), un healthcheck
`pg_isready`, une dépendance `api: depends_on: db: condition:
service_healthy`, la variable `INDUSENSE_DB_URL` côté `api`, et le volume
`pgdata`. Ajouté et vérifié en conditions réelles : `docker compose up -d
--build` démarre `db` en premier, l'attend `healthy`, puis démarre `api`
(healthy) avant `prometheus` puis `grafana` — même ordre de gating que
précédemment, avec un maillon de plus en amont.
