"""Pipeline InduSense orchestre par Prefect (modules 29-30).

Decoupe ingestion -> dataset gold -> entrainement/reprise -> prediction ->
stockage idempotent en 5 tasks, assemblees dans un flow nomme par run.
Reference : FORMATION/JALONS/07-j4-matin-m29-m30.md
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from loguru import logger
from prefect import flow, get_run_logger, task
from prefect.runtime import flow_run

from indusense import __version__
from indusense.config import settings
from indusense.data.loaders import build_dataset, load_incidents, load_pressure, load_temperature
from indusense.features.temporal import add_temporal_features
from indusense.models.tabular import (
    load_model,
    predict_proba,
    save_model,
    select_features,
    train_model,
)

RAW_FILES = ("capteurs_temperature.csv", "capteurs_pression.tsv", "releves_incidents.csv")


def _sources_cache_key(context, parameters: dict) -> str:
    """Cle de cache = empreinte des fichiers source + parametres de jointure.

    Une meme empreinte => Prefect rejoue le resultat en cache (reprise) sans
    relire ni rejoindre les sources. Un fichier modifie (mtime/taille) ou un
    parametre different change la cle et force un recalcul.
    """
    data_dir = Path(parameters["data_dir"])
    fingerprint = [f"window_hours={parameters.get('window_hours')}"]
    for name in RAW_FILES:
        stat = (data_dir / name).stat()
        fingerprint.append(f"{name}:{stat.st_mtime_ns}:{stat.st_size}")
    return hashlib.sha256("|".join(fingerprint).encode("utf-8")).hexdigest()


@task(
    name="build-gold-dataset",
    cache_key_fn=_sources_cache_key,
    cache_expiration=None,
    persist_result=True,
    retries=1,
)
def build_gold_dataset(data_dir: Path, window_hours: int) -> pd.DataFrame:
    """Ingestion + jointure + features temporelles (cachee par empreinte source)."""
    run_logger = get_run_logger()
    temp = load_temperature(data_dir / "capteurs_temperature.csv")
    pres = load_pressure(data_dir / "capteurs_pression.tsv")
    inc = load_incidents(data_dir / "releves_incidents.csv")
    dataset = build_dataset(temp, pres, inc, window_hours=window_hours)
    dataset = add_temporal_features(dataset).dropna().reset_index(drop=True)
    run_logger.info(
        "Dataset gold construit : %s lignes, %s machines",
        len(dataset),
        dataset["machine"].nunique(),
    )
    return dataset


@task(name="ensure-model", retries=1)
def ensure_model(
    dataset: pd.DataFrame,
    model_dir: Path,
    target_col: str,
    random_seed: int,
    retrain: bool,
) -> Path:
    """Entraine et sauvegarde le modele, sauf reprise sur un modele deja present."""
    run_logger = get_run_logger()
    model_path = model_dir / "rf.joblib"
    if model_path.exists() and not retrain:
        run_logger.info("Reprise : modele existant reutilise -> %s", model_path)
        return model_path

    x = select_features(dataset, target_col)
    y = dataset[target_col]
    model = train_model(x, y, random_state=random_seed)
    save_model(model, model_path)

    metadata = {
        "created_at": datetime.now(UTC).isoformat(),
        "package_version": __version__,
        "random_seed": random_seed,
        "target_col": target_col,
        "features": list(x.columns),
        "n_train_rows": int(len(dataset)),
        "panne_rate": round(float(y.mean()), 4),
    }
    (model_dir / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    run_logger.info("Modele (re)entraine sur %s lignes -> %s", len(dataset), model_path)
    return model_path


@task(name="predict-latest")
def predict_latest(dataset: pd.DataFrame, model_path: Path, target_col: str) -> pd.DataFrame:
    """Score la derniere observation connue de chaque machine."""
    latest = dataset.groupby("machine").tail(1).reset_index(drop=True)
    model = load_model(model_path)
    scores = predict_proba(model, select_features(latest, target_col))
    return pd.DataFrame(
        {
            "machine": latest["machine"],
            "observed_at": latest["timestamp"],
            "score": scores,
        }
    )


@task(name="store-predictions")
def store_predictions(
    predictions: pd.DataFrame, db_path: Path, threshold: float, model_version: str
) -> int:
    """Upsert idempotent : re-executer le flow met a jour les lignes, n'en ajoute pas."""
    run_logger = get_run_logger()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    scored_at = datetime.now(UTC).isoformat()

    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                machine TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                score REAL NOT NULL,
                decision TEXT NOT NULL,
                model_version TEXT NOT NULL,
                scored_at TEXT NOT NULL,
                PRIMARY KEY (machine, observed_at)
            )
            """
        )
        rows = [
            (
                str(row.machine),
                pd.Timestamp(row.observed_at).isoformat(),
                float(row.score),
                "alerte" if row.score >= threshold else "ok",
                model_version,
                scored_at,
            )
            for row in predictions.itertuples()
        ]
        conn.executemany(
            """
            INSERT INTO predictions
                (machine, observed_at, score, decision, model_version, scored_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(machine, observed_at) DO UPDATE SET
                score = excluded.score,
                decision = excluded.decision,
                model_version = excluded.model_version,
                scored_at = excluded.scored_at
            """,
            rows,
        )
        conn.commit()
        row_count = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]

    run_logger.info(
        "Predictions upsertees : %s lignes ecrites, %s lignes totales en base", len(rows), row_count
    )
    return row_count


def _flow_run_name() -> str:
    params = flow_run.parameters
    data_dir = Path(params.get("data_dir") or settings.data_dir).name
    return f"indusense-pipeline-{data_dir}-{datetime.now():%Y%m%d-%H%M%S}"


@flow(name="indusense-pipeline", flow_run_name=_flow_run_name)
def indusense_pipeline(
    data_dir: Path | None = None,
    model_dir: Path | None = None,
    db_path: Path | None = None,
    window_hours: int | None = None,
    threshold: float | None = None,
    random_seed: int | None = None,
    retrain: bool = False,
) -> dict:
    """Flow ingest -> gold -> modele -> predict -> store, rejouable sans duplication."""
    data_dir = Path(data_dir or settings.data_dir)
    model_dir = Path(model_dir or settings.model_dir)
    db_path = Path(db_path or settings.predictions_db)
    window_hours = window_hours if window_hours is not None else settings.incident_window_hours
    threshold = threshold if threshold is not None else settings.decision_threshold
    random_seed = random_seed if random_seed is not None else settings.random_seed

    dataset = build_gold_dataset(data_dir, window_hours)
    model_path = ensure_model(dataset, model_dir, settings.target_col, random_seed, retrain)
    predictions = predict_latest(dataset, model_path, settings.target_col)
    row_count = store_predictions(predictions, db_path, threshold, __version__)

    return {
        "rows_scored": len(predictions),
        "rows_in_db": row_count,
        "db_path": str(db_path),
    }


def main() -> None:
    result = indusense_pipeline()
    logger.info("Pipeline termine : {}", result)


if __name__ == "__main__":
    main()
