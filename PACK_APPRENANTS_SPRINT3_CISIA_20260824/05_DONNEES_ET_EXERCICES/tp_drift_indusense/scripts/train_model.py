"""InduSense — Entraînement m8-propre : split TEMPOREL + seuil gelé par le coût.

Protocole (leçons Sprint 2/3) :
  - train = 26/08 → 30/11/2025 · validation = DÉCEMBRE 2025 (split temporel, m8 :
    avec des rolling features, un split aléatoire fuit — mesuré : ROC 0,93 aléatoire
    contre 0,82 temporel sur ce même jeu !) ;
  - coût maintenance : FN (panne non anticipée) = 5 000 € ≫ FP (inspection) = 200 €
    → seuil théorique calibré 200/5200 ≈ 0,038 ;
  - le seuil est GELÉ dans models/threshold.json (carte d'identité m22).
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score

RACINE = Path(__file__).resolve().parents[1]
FEATURES = ["temperature", "pressure_bar"] + [
    f"{c}_{k}" for c in ["temperature", "pressure_bar"] for k in ["moy6h", "moy24h", "std24h", "delta6h"]
]
COUT_FN, COUT_FP = 5000.0, 200.0

def main() -> None:
    ref = pd.read_csv(RACINE / "data" / "reference.csv", parse_dates=["timestamp"])
    tr = ref[ref["timestamp"] < "2025-12-01"]
    val = ref[ref["timestamp"] >= "2025-12-01"]
    print(f"Train {len(tr)} l (aoû-nov) · Validation TEMPORELLE {len(val)} l (déc) · panne {ref['panne_24h'].mean():.2%}")

    modele = HistGradientBoostingClassifier(random_state=42).fit(tr[FEATURES], tr["panne_24h"])
    proba = modele.predict_proba(val[FEATURES])[:, 1]
    pr_auc = float(average_precision_score(val["panne_24h"], proba))
    roc = float(roc_auc_score(val["panne_24h"], proba))

    meilleur, cout_min = 0.5, float("inf")
    for t in np.arange(0.02, 0.981, 0.01):
        yp = (proba >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(val["panne_24h"], yp).ravel()
        c = COUT_FN * fn + COUT_FP * fp
        if c < cout_min: meilleur, cout_min = round(float(t), 2), c
    yp = (proba >= meilleur).astype(int)
    tn, fp, fn, tp = confusion_matrix(val["panne_24h"], yp).ravel()

    md = RACINE / "models"; md.mkdir(exist_ok=True)
    joblib.dump(modele, md / "model.joblib")
    (md / "threshold.json").write_text(json.dumps({
        "modele": "HistGradientBoostingClassifier(random_state=42)",
        "features": FEATURES, "seuil": meilleur,
        "cout_fn_eur": COUT_FN, "cout_fp_eur": COUT_FP,
        "validation": {"periode": "décembre 2025 (temporel)", "pr_auc": round(pr_auc, 4),
                       "roc_auc": round(roc, 4), "rappel": round(tp / (tp + fn), 4),
                       "precision": round(tp / (tp + fp), 4), "taux_alerte": round(float(yp.mean()), 4)},
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Validation déc : PR-AUC {pr_auc:.3f} (prévalence {val['panne_24h'].mean():.3f}) · ROC-AUC {roc:.3f}")
    print(f"Seuil gelé {meilleur} (théorique {COUT_FP/(COUT_FP+COUT_FN):.3f}) : "
          f"rappel {tp/(tp+fn):.3f} · précision {tp/(tp+fp):.3f} · taux d'alerte {yp.mean():.2%}")
    print("Modèle + seuil gelés dans models/")

if __name__ == "__main__":
    main()
