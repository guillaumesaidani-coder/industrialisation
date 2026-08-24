"""InduSense — Évaluation métier d'une fenêtre de production au seuil GELÉ."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score

RACINE = Path(__file__).resolve().parents[1]

def evaluer_fenetre(fenetre: str) -> dict:
    modele = joblib.load(RACINE / "models" / "model.joblib")
    carte = json.loads((RACINE / "models" / "threshold.json").read_text(encoding="utf-8"))
    df = pd.read_csv(RACINE / "data" / f"fenetre_{fenetre}.csv")
    proba = modele.predict_proba(df[carte["features"]])[:, 1]
    y = df["panne_24h"].to_numpy()
    yp = (proba >= carte["seuil"]).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, yp).ravel()
    return {"fenetre": fenetre, "n": len(y), "seuil": carte["seuil"],
            "taux_panne": float(y.mean()), "taux_alerte": float(yp.mean()),
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
            "accuracy": (tp + tn) / len(y),
            "precision": tp / (tp + fp) if tp + fp else 0.0,
            "rappel": tp / (tp + fn) if tp + fn else 0.0,
            "pr_auc": float(average_precision_score(y, proba)),
            "roc_auc": float(roc_auc_score(y, proba))}

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fenetre", required=True, choices=["1", "2", "3", "janvier"])
    args = ap.parse_args()
    m = evaluer_fenetre(args.fenetre)
    print(f"\n=== Fenêtre {m['fenetre']} — {m['n']} relevés · seuil gelé {m['seuil']} ===")
    print(f"  Taux de panne réel   : {m['taux_panne']:.2%}")
    print(f"  Taux d'alerte modèle : {m['taux_alerte']:.2%}")
    print(f"  Confusion [TN FP / FN TP] : [{m['tn']} {m['fp']} / {m['fn']} {m['tp']}]")
    print(f"  Rappel {m['rappel']:.3f} · Précision {m['precision']:.3f} · Accuracy {m['accuracy']:.3f}")
    print(f"  PR-AUC {m['pr_auc']:.3f} · ROC-AUC {m['roc_auc']:.3f}")
    rp = RACINE / "reports"; rp.mkdir(exist_ok=True)
    ligne = pd.DataFrame([m]); chemin = rp / "suivi_fenetres.csv"
    if chemin.exists():
        old = pd.read_csv(chemin, dtype={"fenetre": str})
        old = old[old["fenetre"] != m["fenetre"]]
        ligne = pd.concat([old, ligne], ignore_index=True)
    ligne.to_csv(chemin, index=False)

if __name__ == "__main__":
    main()
