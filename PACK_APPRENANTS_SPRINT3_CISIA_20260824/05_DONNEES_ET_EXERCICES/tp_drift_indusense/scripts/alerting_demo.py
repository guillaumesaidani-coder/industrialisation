"""Preuve M32 autonome : rapport PSI/KS, drift_events et cooldown 0 -> 1 -> 0.

Ce script reste dans le kit Sprint 3 et s'exécute sans Docker ni PostgreSQL. Il utilise
les CSV InduSense déjà versionnés, la convention PSI du module 31 et une base SQLite
en mémoire par défaut. Il ne remplace pas l'intégration Prefect/PostgreSQL : il prouve
la règle de décision et la traçabilité avant ce branchement.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))
from drift_lab import SEUIL_PSI_FORT, drift_table  # noqa: E402

DDL = """
CREATE TABLE IF NOT EXISTS drift_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detected_at TEXT NOT NULL,
    feature TEXT NOT NULL,
    psi REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'open'
)
"""


def make_report(reference: pd.DataFrame, current: pd.DataFrame) -> dict[str, Any]:
    """Retourne le contrat JSON du module 32 à partir du calcul testé du module 31."""
    table = drift_table(reference, current)
    report: dict[str, Any] = {}
    for row in table.itertuples(index=False):
        report[str(row.feature)] = {
            "psi": float(row.psi),
            "ks_p": float(row.ks_pvalue),
            "drift": bool(row.psi > SEUIL_PSI_FORT),
        }
    report["_global"] = {"drift": any(v["drift"] for v in report.values())}
    return report


def should_alert(
    connection: sqlite3.Connection,
    feature: str,
    now: datetime,
    cooldown_hours: int = 6,
) -> bool:
    """Autorise une alerte si aucune alerte récente n'existe pour la feature."""
    last = connection.execute(
        "SELECT max(detected_at) FROM drift_events WHERE feature = ?", (feature,)
    ).fetchone()[0]
    if last is None:
        return True
    last_at = datetime.fromisoformat(str(last))
    return now - last_at >= timedelta(hours=cooldown_hours)


def maybe_alert(
    connection: sqlite3.Connection,
    report: dict[str, Any],
    now: datetime,
    cooldown_hours: int = 6,
) -> int:
    """Insère au plus une alerte pour la feature la plus dérivée ; retourne 0 ou 1."""
    candidates = [
        (feature, values)
        for feature, values in report.items()
        if feature != "_global" and values["drift"]
    ]
    if not candidates:
        return 0
    feature, values = max(candidates, key=lambda item: item[1]["psi"])
    if not should_alert(connection, feature, now, cooldown_hours):
        return 0
    connection.execute(
        "INSERT INTO drift_events(detected_at, feature, psi) VALUES (?, ?, ?)",
        (now.isoformat(), feature, float(values["psi"])),
    )
    connection.commit()
    return 1


def run_demo(connection: sqlite3.Connection) -> tuple[list[int], dict[str, Any]]:
    """Joue fenêtre saine, dérive +8 °C puis relance à +1 h sous cooldown."""
    connection.execute(DDL)
    data = RACINE / "data"
    reference = pd.read_csv(data / "reference_normale.csv")
    healthy = make_report(reference, pd.read_csv(data / "fenetre_1.csv"))
    drifted = make_report(reference, pd.read_csv(data / "fenetre_2.csv"))
    t0 = datetime(2026, 2, 25, 9, 0, tzinfo=timezone.utc)
    sequence = [
        maybe_alert(connection, healthy, t0),
        maybe_alert(connection, drifted, t0),
        maybe_alert(connection, drifted, t0 + timedelta(hours=1)),
    ]
    return sequence, drifted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db",
        default=":memory:",
        help="SQLite : :memory: par défaut, ou chemin explicite pour conserver la preuve.",
    )
    parser.add_argument("--json", action="store_true", help="Affiche aussi le rapport JSON.")
    parser.add_argument(
        "--report-out",
        type=Path,
        help="Écrit le rapport JSON dans ce chemin (créé sous le dossier demandé).",
    )
    args = parser.parse_args()

    with sqlite3.connect(args.db) as connection:
        sequence, report = run_demo(connection)
        rows = connection.execute(
            "SELECT detected_at, feature, psi, status FROM drift_events ORDER BY id"
        ).fetchall()
        print("sequence=" + " -> ".join(map(str, sequence)))
        print(f"drift_events={len(rows)}")
        if rows:
            print(f"event_feature={rows[0][1]}")
            print(f"event_psi={rows[0][2]:.3f}")
        if args.report_out:
            args.report_out.parent.mkdir(parents=True, exist_ok=True)
            args.report_out.write_text(
                json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
            )
            print(f"report_out={args.report_out}")
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        if sequence != [0, 1, 0] or len(rows) != 1:
            raise SystemExit("Preuve M32 invalide : attendu 0 -> 1 -> 0 et une ligne.")


if __name__ == "__main__":
    main()
