# Preuve pipeline Prefect — ingest → gold → modèle → predict → store (module 29)

Périmètre : `flows/pipeline.py` (5 tasks Prefect assemblées dans le flow
`indusense-pipeline`), `scripts/demo_prefect_idempotence.py`. Stockage des
scores dans une base SQLite (`INDUSENSE_PREDICTIONS_DB`, défaut
`artifacts/predictions.db`).

## Registre des preuves

| Contrôle | Statut | Preuve actuelle | Risque résiduel / suite |
|---|---|---|---|
| Décomposition tasks/flow | Implémenté | 5 tasks Prefect (`build-gold-dataset`, `ensure-model`, `predict-latest`, `store-predictions`) assemblées dans `@flow indusense_pipeline`. `uv run --frozen python flows/pipeline.py` logue une entrée « Beginning flow run » puis « Task run '...' — Finished in state Completed() » pour chacune. | Aucun. |
| Run nommé | Implémenté | `flow_run_name` généré par un callable (`_flow_run_name`) à partir du dossier de données et de l'horodatage, ex. `indusense-pipeline-raw-20260902-101008`, visible dans chaque ligne de log Prefect de l'exécution. | Aucun. |
| Cache / reprise sur l'ingestion | Implémenté | `build-gold-dataset` a une `cache_key_fn` qui hashe mtime + taille des 3 fichiers source et `window_hours`. Deuxième exécution (même process ou process frais) : `Task run 'build-gold-dataset-...' — Finished in state Cached(type=COMPLETED)` au lieu de rejouer ingestion + jointure + features. | Cache invalidé si un fichier source change (attendu) ; pas de `cache_expiration` fixe — à borner si la volumétrie change en formation longue durée. |
| Reprise sur l'entraînement | Implémenté | `ensure-model` vérifie `model_path.exists()` avant d'entraîner : log `Reprise : modele existant reutilise -> artifacts\models\rf.joblib` au lieu de relancer un RandomForest. | `retrain=True` force un réentraînement explicite si nécessaire. |
| Idempotence du stockage | Implémenté | `uv run --frozen python scripts/demo_prefect_idempotence.py` rejoue le flow deux fois sur une base SQLite temporaire neuve (jamais réutilisée) : `1er passage : rows_scored=4 rows_in_db=4` puis `2e passage : rows_scored=4 rows_in_db=4` → `OK idempotence`. Mécanisme : `INSERT ... ON CONFLICT(machine, observed_at) DO UPDATE` (clé composite machine + observed_at), donc un second passage met à jour les lignes au lieu d'en ajouter. | Aucun. |
| Exécution hors réseau | Implémenté | `uv run --frozen python flows/pipeline.py` s'exécute sans accès réseau (profil Prefect éphémère, serveur temporaire local, orchestration sur SQLite local). | `uv run` sans `--frozen` tente une résolution réseau du lock et peut rester bloqué en environnement sans accès sortant — toujours utiliser `--frozen` pour ce pipeline. |
| Non-régression | Implémenté | `uv run --frozen pytest -q` → `26 passed, 5 skipped` (suite API/sécurité/loaders/temporel/compose inchangée après ajout du flow). | Aucun. |

## Note de méthode

- « Implémenté » signifie ici : commande exécutée réellement (flow lancé deux
  fois de suite, logs Prefect lus), pas une lecture du code seule.
- Le rattrapage se limite au périmètre du jalon 07 : pipeline local
  séquentiel avec traces claires. L'UI Prefect (serveur persistant,
  dashboard) et les politiques de retry avancées restent hors périmètre —
  réserve des modules 30 et suivants (Docker Compose, base Postgres via
  `indusense.flows.predict_flow`, cf. guide multiplateforme section 10).
