# Drift spec InduSense (m31/m33)

## References gelees

- **Regime normale** : donnees de septembre + novembre + decembre (`data/drift/reference_normale.csv`, 31 821 lignes).
- **Regime haute charge** : donnees d'octobre (`data/drift/reference_haute.csv`, 11 006 lignes).
- Chaque fenetre de surveillance se compare aux DEUX references ; le choix de la
  bonne reference (normale ou haute) est une decision metier (planning de charge connu),
  jamais une decision automatique.

## Fenetre de mesure

- 7 jours glissants, par machine.
- Segmentation par `machine_id` : priorite aux machines `criticality = HIGH`
  (`data/drift_source/machine.sql`) ; `criticality` n'est JAMAIS reinjectee comme feature
  du modele (fuite d'information metier vers la prediction).

## PSI — protocole fige

- 10 bins, calcules sur la REFERENCE uniquement (grille stable dans le temps, jamais
  recalculee sur la fenetre courante).
- Bords extremes ouverts (`-inf`/`+inf`) : une valeur courante hors de la plage de reference
  tombe dans le bin extreme au lieu d'etre perdue.
- Valeurs `NaN` ecartees du calcul.
- KS (Kolmogorov-Smirnov) en confirmation du PSI, jamais en decision seule (KS est
  structurellement aveugle a un concept drift a X inchange, cf. fenetre 3 ci-dessous).

## Regle d'alerte

- Alerte si PSI > 0,25 persistant sur 2 fenetres consecutives (une seule fenetre haute peut
  etre du bruit ; la persistance distingue un signal d'un artefact ponctuel).
- Lecture usuelle : PSI < 0,10 RAS · 0,10-0,25 a surveiller · > 0,25 fort.

## KPI de second rideau (performance retardee)

- Taux de confirmation des inspections (delai ~3 j) : plancher 0,05.
- Rappel du modele (delai ~15 j, une fois les vraies pannes connues) : plancher 0,60.
- Bande d'alerte (taux d'alerte du modele) : 35-50 % — en dehors de cette bande, le seuil
  gele lui-meme est a reevaluer, independamment du PSI.

## Preuves mesurees (uv run python scripts/evaluate_drift.py, 2026-09-03)

| Fenetre | Reference | PSI temperature | PSI pressure_bar | Rappel | ROC | Lecture |
|---|---|---|---|---|---|---|
| 1 (temoin, fev 2026) | normale | 0,002 | 0,025 | 0,753 | 0,791 | RAS des deux cotes : bruit de fond etalonne. |
| 2 (capteur +8C) | normale | **6,834** | 0,025 | 0,738 | 0,793 | PSI hurle sur `temperature` seule ; le modele (assis sur les deltas) tient — mais capteur menteur = donnees corrompues pour tout le reste. Controle physique d'abord (`docs/runbook.md`). |
| 3 (concept drift) | normale | 0,002 | 0,025 | **0,051** | **0,209** | PSI structurellement muet (X quasi identiques), rappel effondre — seul un KPI avec labels (rappel/ROC) voit ce type de derive. |
| janvier (campagne haute charge) | normale | 6,203 | 0,002 | 0,802 | 0,816 | PSI hurle vs reference normale... |
| janvier (meme fenetre) | haute | **0,001** | 0,001 | 0,802 | 0,816 | ...mais RAS vs reference haute charge : fausse alerte de regime. C'est la raison d'etre des references par regime figees ci-dessus. |

## Reactions (resume)

- PSI capteur franchi (fenetre 2) -> etalonnage physique AVANT toute action modele.
- Campagne planifiee reconnue (fenetre janvier vs haute = RAS) -> basculer de reference, ne
  pas alerter.
- Rappel sous le plancher 0,60 (fenetre 3) -> reentrainement (protocole m21 complet), puis
  nouvelle reference et spec mise a jour — jamais un simple ajustement de seuil.
