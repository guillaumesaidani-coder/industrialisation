"""Tests du kit drift InduSense — definition of done du scénario complet."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))
import drift_lab  # noqa: E402

DATA = RACINE / "data"
MODELES = RACINE / "models"

def test_psi_quasi_nul_sur_distributions_identiques():
    rng = np.random.default_rng(0)
    assert drift_lab.psi(rng.normal(0, 1, 20000), rng.normal(0, 1, 5000)) < 0.05

def test_psi_detecte_un_decalage():
    rng = np.random.default_rng(2)
    assert drift_lab.psi(rng.normal(0, 1, 20000), rng.normal(1, 1, 5000)) > 0.25

def test_psi_ignore_les_nan():
    rng = np.random.default_rng(3)
    ref = rng.normal(0, 1, 10000); ref[::50] = np.nan
    assert drift_lab.psi(ref, rng.normal(0, 1, 3000)) < 0.05

_donnees = (DATA / "reference_normale.csv").exists() and (DATA / "fenetre_3.csv").exists()
_modele = (MODELES / "model.joblib").exists()
donnees = pytest.mark.skipif(not _donnees, reason="lancez d'abord scripts/build_dataset.py")
modele = pytest.mark.skipif(not (_donnees and _modele), reason="lancez d'abord scripts/train_model.py")

def _t(fen, ref):
    import pandas as pd
    return drift_lab.drift_table(pd.read_csv(DATA / f"reference_{ref}.csv"), pd.read_csv(DATA / f"fenetre_{fen}.csv"))

@donnees
def test_fenetre1_temoin_silencieuse():
    assert (_t("1", "normale")["psi"] < 0.10).all()

@donnees
def test_fenetre2_capteur_detecte():
    tab = _t("2", "normale").set_index("feature")
    assert tab.loc["temperature", "psi"] > 0.25
    assert tab.loc["temperature", "ks_pvalue"] < 1e-6

@donnees
def test_fenetre3_concept_muet_au_psi():
    assert (_t("3", "normale")["psi"] < 0.10).all()

@donnees
def test_janvier_reference_par_regime():
    assert _t("janvier", "normale").set_index("feature").loc["temperature", "psi"] > 0.25  # fausse alerte
    assert (_t("janvier", "haute")["psi"] < 0.10).all()                                    # même régime : silence

@modele
def test_concept_drift_effondre_le_rappel():
    import evaluate_fenetre
    m1 = evaluate_fenetre.evaluer_fenetre("1")
    m3 = evaluate_fenetre.evaluer_fenetre("3")
    assert m1["rappel"] > 0.60
    assert m3["rappel"] < 0.5 * m1["rappel"]
    assert m3["roc_auc"] < 0.5
    assert abs(m3["taux_alerte"] - m1["taux_alerte"]) < 0.05  # panne silencieuse côté ops
