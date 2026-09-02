# Preuve pipeline Prefect — ingest → gold → modèle → predict → store (modules 29-30)

Périmètre : `src/indusense/flows/predict_flow.py` (5 tasks Prefect assemblées
dans le flow `indusense-pipeline`), exécutable en local via `flows/pipeline.py`
(délégation, jalon 07) ou dans le conteneur API via
`python -m indusense.flows.predict_flow` (module 30). Stockage via SQLAlchemy,
URL portée par `INDUSENSE_DB_URL` : `sqlite:///artifacts/predictions.db` en
local/QA, `postgresql+psycopg://...@db:5432/postgres` injectée par
`compose.yaml` sous Docker.

## Registre des preuves

| Contrôle | Statut | Preuve actuelle | Risque résiduel / suite |
|---|---|---|---|
| Décomposition tasks/flow | Implémenté | 5 tasks Prefect (`build-gold-dataset`, `ensure-model`, `predict-latest`, `store-predictions`) assemblées dans `@flow indusense_pipeline`. `uv run --frozen python flows/pipeline.py` logue une entrée « Beginning flow run » puis « Task run '...' — Finished in state Completed() » pour chacune. | Aucun. |
| Run nommé | Implémenté | `flow_run_name` généré par un callable (`_flow_run_name`) à partir du dossier de données et de l'horodatage, ex. `indusense-pipeline-raw-20260902-101008`. | Aucun. |
| Cache / reprise sur l'ingestion (local) | Implémenté | `build-gold-dataset` a une `cache_key_fn` qui hashe mtime + taille des 3 fichiers source et `window_hours`. Deuxième exécution dans le même environnement Prefect (même process ou process frais partageant le même `PREFECT_HOME`) : `Task run 'build-gold-dataset-...' — Finished in state Cached(type=COMPLETED)`. | Chaque `docker compose run` du module 30 démarre un profil Prefect éphémère isolé : le cache inter-tasks ne survit pas d'un conteneur jetable à l'autre (attendu — la reprise qui compte en conteneur est celle du modèle, ci-dessous). |
| Reprise sur l'entraînement | Implémenté | `ensure-model` vérifie `model_path.exists()` avant d'entraîner : log `Reprise : modele existant reutilise -> artifacts/models/rf.joblib` — vrai en local (modèle déjà entraîné) et dans le conteneur (modèle Variante A embarqué par le `Dockerfile`, module 27). | `retrain=True` force un réentraînement explicite si nécessaire. |
| Idempotence du stockage (SQLite local) | Implémenté | `uv run --frozen python scripts/demo_prefect_idempotence.py` rejoue le flow deux fois sur une base SQLite temporaire neuve (jamais réutilisée) : `rows_in_db=4` puis `4` → `OK idempotence`. | Aucun. |
| Idempotence du stockage (Postgres réel) | Implémenté | `docker compose run --rm --no-deps -e INDUSENSE_DATA_DIR=/app/data/run --volume "<data>:/app/data/run:ro" api python -m indusense.flows.predict_flow` exécuté deux fois de suite contre le service `db` (Postgres 16) : `SELECT COUNT(*) FROM predictions` → `4` après le 1er passage, toujours `4` après le 2e. | Aucun. |
| Portabilité SQLite/Postgres | Implémenté | Même code SQL (`INSERT ... ON CONFLICT (machine, observed_at) DO UPDATE SET ... = excluded....`) exécuté sans branche dialecte via SQLAlchemy `create_engine(db_url)` ; validé contre les deux backends (essais ci-dessus). | Aucun. |
| Exécution hors réseau | Implémenté | `uv run --frozen python flows/pipeline.py` s'exécute sans accès réseau (profil Prefect éphémère, serveur temporaire local). | `uv run` sans `--frozen` tente une résolution réseau du lock et reste bloqué en environnement sans accès sortant — toujours utiliser `--frozen`. |
| Non-régression | Implémenté | `uv run --frozen pytest -q` → `26 passed, 5 skipped` (suite API/sécurité/loaders/temporel/compose inchangée après le passage à SQLAlchemy). | Aucun. |

## Note de méthode

- « Implémenté » signifie ici : commande exécutée réellement (flow lancé
  plusieurs fois, en local et dans le conteneur `api` contre un vrai Postgres
  démarré par `docker compose up -d --wait db`), pas une lecture du code
  seule.
- Sous Git Bash sur Windows, les chemins absolus commençant par `/` passés à
  `docker compose run` (ex. `-e INDUSENSE_DATA_DIR=/app/data/run`) sont
  réécrits en chemins Windows par la conversion automatique de MSYS avant
  d'atteindre Docker. Fixé en exportant `MSYS_NO_PATHCONV=1` autour de la
  commande — sans lien avec le code du pipeline, propre à ce shell.
- Le stockage n'a plus de branche dialecte : la même requête SQL upsert tourne
  contre SQLite (démo locale) et PostgreSQL (Compose), seule l'URL change via
  `INDUSENSE_DB_URL`.
