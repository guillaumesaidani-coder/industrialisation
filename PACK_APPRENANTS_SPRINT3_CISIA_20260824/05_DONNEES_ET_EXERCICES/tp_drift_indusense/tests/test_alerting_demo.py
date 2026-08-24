"""Tests de la preuve autonome M32, sans réseau, Docker ni base externe."""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))
from alerting_demo import DDL, maybe_alert, run_demo  # noqa: E402


def test_sequence_canonique_trace_une_seule_alerte() -> None:
    with sqlite3.connect(":memory:") as connection:
        sequence, _ = run_demo(connection)
        rows = connection.execute(
            "SELECT feature, psi FROM drift_events ORDER BY id"
        ).fetchall()
    assert sequence == [0, 1, 0]
    assert len(rows) == 1
    assert rows[0][0] == "temperature"
    assert rows[0][1] > 0.25


def test_cooldown_expire_apres_six_heures() -> None:
    report = {
        "temperature": {"psi": 0.30, "ks_p": 0.0, "drift": True},
        "_global": {"drift": True},
    }
    t0 = datetime(2026, 2, 25, 9, 0, tzinfo=timezone.utc)
    with sqlite3.connect(":memory:") as connection:
        connection.execute(DDL)
        assert maybe_alert(connection, report, t0) == 1
        assert maybe_alert(connection, report, t0 + timedelta(hours=1)) == 0
        assert maybe_alert(connection, report, t0 + timedelta(hours=6)) == 1
        count = connection.execute("SELECT count(*) FROM drift_events").fetchone()[0]
    assert count == 2


def test_fenetre_saine_ne_cree_aucun_evenement() -> None:
    report = {
        "temperature": {"psi": 0.02, "ks_p": 0.3, "drift": False},
        "_global": {"drift": False},
    }
    with sqlite3.connect(":memory:") as connection:
        connection.execute(DDL)
        assert maybe_alert(connection, report, datetime.now(timezone.utc)) == 0
        count = connection.execute("SELECT count(*) FROM drift_events").fetchone()[0]
    assert count == 0
