"""InduSense — Laboratoire de dérive : PSI + KS sur les capteurs réels.

Surveillance des 2 features capteurs (m31) : temperature, pressure_bar.
Spécificité InduSense vs PayGuard : la RÉFÉRENCE se choisit PAR RÉGIME
(normale = sept+nov+déc · haute = campagne d'octobre · train = tout 2025 mélangé),
et la table peut être segmentée PAR MACHINE (m31 §2.5).

Usage :
  python scripts/drift_lab.py --fenetre 1 --reference normale
  python scripts/drift_lab.py --fenetre janvier --reference normale   # fausse alerte de régime !
  python scripts/drift_lab.py --fenetre janvier --reference haute     # silence : même régime
  python scripts/drift_lab.py --fenetre 2 --reference normale --machine MACH-03
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

RACINE = Path(__file__).resolve().parents[1]
DATA = RACINE / "data"
RAPPORTS = RACINE / "reports"
FEATURES_SURVEILLEES = ["temperature", "pressure_bar"]
SEUIL_PSI_SURVEILLER, SEUIL_PSI_FORT = 0.10, 0.25


def psi(ref, cur, bins: int = 10) -> float:
    """PSI, conventions m31 : bins figés sur la référence, +1e-6, bords ouverts ±inf.
    Les NaN (vraies données capteurs !) sont écartés feature par feature."""
    ref = np.asarray(pd.Series(ref).dropna(), dtype=float)
    cur = np.asarray(pd.Series(cur).dropna(), dtype=float)
    edges = np.histogram_bin_edges(ref, bins=bins)
    edges[0], edges[-1] = -np.inf, np.inf
    p_ref = np.histogram(ref, edges)[0] / len(ref) + 1e-6
    p_cur = np.histogram(cur, edges)[0] / len(cur) + 1e-6
    return float(np.sum((p_cur - p_ref) * np.log(p_cur / p_ref)))


def ks_pvalue(ref, cur) -> float:
    return float(stats.ks_2samp(pd.Series(ref).dropna(), pd.Series(cur).dropna()).pvalue)


def verdict_psi(v: float) -> str:
    if v < SEUIL_PSI_SURVEILLER: return "OK RAS"
    if v < SEUIL_PSI_FORT: return "! à surveiller"
    return "!! dérive forte"


def drift_table(df_ref, df_cur, features=FEATURES_SURVEILLEES, bins=10) -> pd.DataFrame:
    lignes = [{"feature": f,
               "psi": psi(df_ref[f], df_cur[f], bins=bins),
               "ks_pvalue": ks_pvalue(df_ref[f], df_cur[f]),
               "verdict": verdict_psi(psi(df_ref[f], df_cur[f], bins=bins))}
              for f in features]
    return pd.DataFrame(lignes).sort_values("psi", ascending=False).reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fenetre", required=True, choices=["1", "2", "3", "janvier"])
    ap.add_argument("--reference", default="normale", choices=["normale", "haute", "train"])
    ap.add_argument("--machine", default=None, help="segmentation par machine, ex. MACH-03")
    ap.add_argument("--bins", type=int, default=10)
    args = ap.parse_args()

    fic_ref = {"normale": "reference_normale.csv", "haute": "reference_haute.csv", "train": "reference.csv"}
    df_ref = pd.read_csv(DATA / fic_ref[args.reference])
    nom_f = f"fenetre_{args.fenetre}.csv"
    df_cur = pd.read_csv(DATA / nom_f)
    if args.machine:
        df_ref = df_ref[df_ref["machine"] == args.machine]
        df_cur = df_cur[df_cur["machine"] == args.machine]

    table = drift_table(df_ref, df_cur, bins=args.bins)
    RAPPORTS.mkdir(exist_ok=True)
    suffixe = f"_{args.machine}" if args.machine else ""
    table.to_csv(RAPPORTS / f"drift_f{args.fenetre}_ref-{args.reference}{suffixe}.csv", index=False)

    aff = table.copy()
    aff["psi"] = aff["psi"].map(lambda v: f"{v:.3f}")
    aff["ks_pvalue"] = aff["ks_pvalue"].map(lambda v: f"{v:.2e}")
    print(f"\n=== Fenêtre {args.fenetre} vs référence {args.reference}"
          f"{' · ' + args.machine if args.machine else ''} "
          f"({len(df_ref)} vs {len(df_cur)} relevés, {args.bins} bins) ===")
    print(aff.to_string(index=False))


if __name__ == "__main__":
    main()
