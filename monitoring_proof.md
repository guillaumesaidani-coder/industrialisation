# Preuve monitoring — drift, Prometheus, Grafana, runbook (modules 31-34)

Perimetre : `src/indusense/monitoring/drift.py` (PSI + KS), `scripts/{drift_windows,
train_drift_model,evaluate_drift,export_drift_metrics}.py`, job Prometheus `indusense-drift`
(`monitoring/prometheus.yml`), dashboard `monitoring/grafana/provisioning/dashboards/
indusense_drift.json`, `docs/{TP_drift,slo,runbook}.md`, `reports/drift/drift_spec.md`.

## Registre des preuves

| Controle | Statut | Preuve actuelle | Risque residuel / suite |
|---|---|---|---|
| Fenetres + jointure capteurs | Implemente | `uv run python scripts/drift_windows.py` -> 64 535 lignes, panne_v1 5,18 % (reference TP : 64 535 / 5,2 %). | Aucun. |
| Modele drift entraine (split temporel) | Implemente | `uv run python scripts/train_drift_model.py` -> validation decembre PR-AUC 0,257 / ROC 0,815, seuil gele 0,04 (reference TP : 0,258 / 0,817 / seuil 0,03 ; ecart attribuable a la re-execution locale, `random_state=42` fixe dans le code). | Aucun. |
| Tests unitaires drift | Implemente | `uv run pytest tests/test_drift_monitoring.py -q` -> `8 passed`. | Aucun. |
| 4 fenetres de surveillance | Implemente | `evaluate_drift.py` rejoue reellement : fenetre 1 (PSI 0,002, RAS), fenetre 2 (PSI temperature 6,83, capteur), fenetre 3 (ROC 0,209, concept drift, PSI muet), janvier vs normale (PSI 6,20) puis vs haute (PSI 0,001, meme fenetre) — les 4 lecons du TP reproduites, cf. `reports/drift/drift_spec.md`. | Aucun. |
| Exporteur Prometheus (m33) | Implemente | `uv run python scripts/export_drift_metrics.py` sert `indusense_drift_psi`/`indusense_drift_rappel`/... sur `:9109/metrics`, verifie par `curl`. | Tourne sur l'hote (pas conteneurise) : a arreter/relancer manuellement, documente dans `docs/TP_drift.md`. |
| 2 cibles Prometheus UP | Implemente | `docker compose up -d --build` puis `GET /api/v1/targets` -> `indusense-api` (`api:8000`) et `indusense-drift` (`host.docker.internal:9109`) toutes deux `up`. `extra_hosts: host.docker.internal:host-gateway` ajoute au service `prometheus` pour la portabilite Linux. | Aucun. |
| Dashboard Grafana provisionne | Implemente | `GET /api/search` -> dashboard `indusense-drift` charge automatiquement (6 panneaux : PSI par capteur, rappel, taux d'alerte, PSI dans le temps, precision, ROC-AUC) ; datasource Prometheus deja provisionnee. | Aucun. |
| Alerte controlee declenchee et visible | Implemente | Rejeu de `evaluate_drift --fenetre 2` pendant l'exporteur actif -> `indusense_drift_psi{feature="temperature",fenetre="2",reference="normale"}` lu a `6,83` via `GET /api/v1/query` (bien au-dessus du seuil 0,25 de la spec). | Aucun. |
| SLO grondes sur les metriques reelles | Implemente | `docs/slo.md` : 3 PromQL (disponibilite, latence p95, erreurs) testes reellement contre `http_requests_total`/`http_request_duration_seconds_bucket` exposes par `prometheus-fastapi-instrumentator`. La requete de disponibilite renvoie `NaN` a faible volumetrie (`increase` sur un compteur trop jeune) : documente comme cas de SLI absent, pas une fausse disponibilite parfaite. | Le seuil p95 (0,5 s) et l'objectif de disponibilite (99 %) sont des choix pedagogiques assumes, non mesures sur un historique de production reel. |
| Runbook joue | Implemente | `docs/runbook.md` reecrit sur l'alerte reellement declenchee ci-dessus (PSI temperature, fenetre 2) : diagnostic en 3 etapes (capteur isole vs modele, changement de regime exclu par contre-epreuve `--reference haute`, cause physique confirmee), action reversible (etalonnage physique avant toute action modele). | Aucun. |
| Suite de tests globale non cassee | Implemente | `uv run pytest -q` -> `34 passed, 5 skipped` (skips = smoke tests hors stack, comportement deja documente dans `compose_proof.md`). `uv run ruff check .` -> `All checks passed`. | Aucun. |

## Note de methode

- « Implemente » signifie ici : commande executee reellement (stack Compose relancee,
  exporteur lance, requetes Prometheus/Grafana jouees), pas une lecture des fichiers de
  configuration seule.
- Les fichiers `data/drift*`, `artifacts/drift_*`, scripts et dashboard proviennent du jalon
  revele `jalon/10` (deja integres/stabilises a ce stade du parcours) ; le travail propre a
  ce jalon porte sur leur mise en service reelle (stack + exporteur + 2 cibles UP + alerte
  jouee) et la redaction de `docs/slo.md`, `docs/runbook.md` et `reports/drift/drift_spec.md`,
  ecrits a partir des metriques et resultats effectivement observes sur cette machine.
