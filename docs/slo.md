# SLO InduSense — M33

Métriques réellement exposées sur `GET /metrics` (via `prometheus-fastapi-instrumentator`,
branché dans `src/indusense/api/main.py`) : `http_requests_total{handler,method,status}` et
`http_request_duration_seconds_bucket{handler,method,le}`. Les PromQL ci-dessous n'utilisent
que ces séries, vérifiées en interrogeant `http://127.0.0.1:9090` sur la stack Compose.

| Indicateur | Population | Fenetre | Objectif | Source PromQL | Budget d'erreur |
|---|---|---|---|---|---|
| Disponibilite | Requetes `/predict-tabular` et `/predict-image` (le coeur metier ; `/health`/`/ready` sont des sondes techniques, exclues) | 30 jours glissants | >= 99 % de reponses non-5xx | `1 - (sum(increase(http_requests_total{handler=~"/predict.*",status=~"5.."}[30d])) or vector(0)) / sum(increase(http_requests_total{handler=~"/predict.*"}[30d]))` | 1 % de requetes en erreur serveur tolerees sur 30 j (~7h de panne cumulee equivalente) |
| Latence | Requetes `/predict-tabular` (chemin le plus sollicite, appele en synchrone par l'operateur) | 5 minutes glissantes | p95 <= 0,5 s | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{handler="/predict-tabular"}[5m])) by (le))` | 5 % des requetes de la fenetre autorisees au-dela de 0,5 s |
| Erreurs | Toutes les requetes API (`http_requests_total`, tous handlers) | 5 minutes glissantes | Taux de 5xx < 1 % | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` | 1 % de requetes en erreur serveur tolerees par fenetre de 5 min avant alerte |

## Pourquoi ces objectifs

- **Disponibilite** : `/predict-tabular` est l'endpoint que l'atelier facturera a l'usage
  metier (decision de panne). Une indisponibilite prolongee bloque l'operateur ; le seuil
  99 % sur 30 j est deliberement modeste (stack mono-instance, sans redondance ici) plutot
  qu'un objectif affiche sans moyen de le tenir.
- **Latence** : le predict est appele en direct par un humain qui attend la reponse (pas de
  file asynchrone) ; au-dela de quelques centaines de ms l'attente devient percue. 0,5 s
  laisse de la marge a un modele scikit-learn charge en memoire, sans etre un objectif
  arbitraire type "100 ms" hors de portee d'un service non optimise.
- **Erreurs** : un taux de 5xx eleve indique une degradation cote service (bug, dependance
  cassee) distincte d'une derive data (couverte par `docs/TP_drift.md` / dashboard
  `indusense_drift_*`). Separer ces deux causes evite d'envoyer la mauvaise equipe sur la
  mauvaise alerte.

## SLI absent vs SLI mauvais

Un **SLI absent** signifie qu'aucune serie exploitable ne remonte pour la fenetre interrogee :
query Prometheus vide, `NaN`, ou cible `indusense-api` a `DOWN` dans `/api/v1/targets`. C'est
un probleme d'instrumentation, de scrape ou (verifie en conditions reelles sur cette stack) de
volumetrie trop faible — `increase(...[30d])` sur un compteur qui vient d'apparaitre renvoie
`0/0 = NaN` tant qu'il n'a pas assez d'echantillons dans la fenetre, meme si le service tourne
parfaitement. C'est un cas distinct d'une panne, mais on ne peut RIEN affirmer sur le SLO tant
que ce n'est pas leve (le budget d'erreur ne doit pas etre consomme sur une absence de
mesure). Un **SLI mauvais** signifie que la serie existe et repond, mais que sa valeur est
hors objectif (ex. `http_requests_total{status=~"5.."}` non nul et p95 latence > 0,5 s) : c'est
un incident reel a traiter via le runbook (`docs/runbook.md`). Verification pratique : d'abord
`curl http://127.0.0.1:9090/api/v1/targets` (cible `up` ?), puis relire les compteurs bruts
(`sum(increase(http_requests_total{handler=~"/predict.*"}[30d]))`) avant de faire confiance au
ratio — sinon un SLI absent se lit a tort comme un SLI parfait (NaN, ou serie manquante
interpretee comme "0 erreur").
