# Runbook M34 — derive capteur (PSI temperature)

Rejoue reellement le 2026-09-03 sur la stack Compose du repo (`docker compose up -d --build`
+ `uv run python scripts/export_drift_metrics.py`) : cible Prometheus `indusense-drift` `up`,
dashboard Grafana « InduSense — derive & metriques » ouvert, alerte declenchee par
`uv run python scripts/evaluate_drift.py --fenetre 2`.

## Alerte

- Nom : `IndusenseDriftPSIEleve`.
- Signal/condition : `indusense_drift_psi{feature="temperature",reference="normale"} > 0,25`
  persistant sur 2 fenetres consecutives (regle m31/TP_drift §4). Observe reellement :
  fenetre 2 -> PSI temperature = 6,83 (seuil fort 0,25 largement franchi), pressure_bar reste
  a 0,025 (OK RAS) — donc un seul capteur derive, pas les deux.
- Gravite et impact metier : majeure mais non bloquante. Le PSI mesure une derive du CAPTEUR
  (donnee d'entree), pas une degradation du service ; le modele continue de repondre
  (`/predict-tabular` reste up, cf. `docs/slo.md`) mais ses predictions reposent sur une
  temperature qui ne represente plus la realite physique — risque de faux negatifs/positifs
  en aval si non traite.

## Diagnostic borne

1. Confirmer que c'est bien le capteur, pas le modele ou le pipeline : lire le panneau
   « PSI par capteur » (Grafana) ou `indusense_drift_psi` (Prometheus) — seul `temperature`
   deborde, `pressure_bar` reste stable. Comparer aussi au KPI de second rideau (rappel,
   panneau « Rappel panne (seuil gele) ») : ici rappel 0,738, dans la plage attendue — la
   detection de panne elle-meme n'est pas effondree (contraste avec la fenetre 3 / concept
   drift, ou le rappel chute a 0,05 : cas different, cf. `docs/TP_drift.md` tableau §2).
2. Verifier que ce n'est pas un simple changement de regime planifie (campagne haute charge)
   avant de traiter comme une panne capteur : rejouer `evaluate_drift --fenetre 2 --reference
   haute` — si le PSI redevient RAS avec la reference haute charge, c'est un changement de
   regime a re-referencer, pas une derive physique (cf. §4 de `docs/TP_drift.md`, cas
   « janvier vs haute » = 0,001).
3. Si le PSI reste fort quelle que soit la reference testee (c'est le cas ici : fenetre 2 vs
   normale = 6,83, aucune reference de regime connu ne l'explique), la cause est physique :
   capteur de temperature hors service ou mal etalonne sur la periode.

## Action reversible

- Action : etalonnage physique du capteur AVANT toute action sur le modele (ne pas
  reentrainer, ne pas changer le seuil gele `artifacts/drift_threshold.json`) — le probleme
  est en amont des donnees, pas dans la logique de decision.
- Retour arriere : si l'etalonnage ne resout pas la derive, isoler la machine concernee
  (segmentation `--machine`, cf. `docs/TP_drift.md` §2) et basculer ses lectures en mode
  degrade (alerte manuelle) le temps du diagnostic materiel, sans toucher au modele en
  production pour les autres machines.
- Preuve de resolution : relancer `uv run python scripts/evaluate_drift.py --fenetre 2` (ou la
  fenetre live equivalente) apres intervention — le panneau « PSI par capteur » doit repasser
  sous 0,10 (RAS) pour `temperature`, meme lecture confirmee dans Prometheus
  (`indusense_drift_psi{feature="temperature"}`).

Ne jamais copier de secret, de payload sensible ou de journal complet dans le
runbook.
