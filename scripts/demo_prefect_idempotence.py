"""Preuve d'idempotence du pipeline Prefect (M29/M30).

Rejoue deux fois le flow `indusense_pipeline` sur une base SQLite temporaire
fraiche et verifie que le second passage ne duplique aucune ligne stockee.
Reference : FORMATION/JALONS/07-j4-matin-m29-m30.md
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flows.pipeline import indusense_pipeline  # noqa: E402
from indusense.config import settings  # noqa: E402


def _count_predictions(db_path: Path) -> int:
    with closing(sqlite3.connect(db_path)) as conn:
        return conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="indusense-preuve-") as tmp:
        db_path = Path(tmp) / "predictions.db"
        assert not db_path.exists(), "la base de preuve doit etre neuve, jamais reutilisee"

        first = indusense_pipeline(data_dir=settings.data_dir, db_path=db_path)
        rows_after_first = _count_predictions(db_path)

        second = indusense_pipeline(data_dir=settings.data_dir, db_path=db_path)
        rows_after_second = _count_predictions(db_path)

        print(f"1er passage : rows_scored={first['rows_scored']} rows_in_db={rows_after_first}")
        print(f"2e  passage : rows_scored={second['rows_scored']} rows_in_db={rows_after_second}")

        if rows_after_first != rows_after_second:
            print(
                f"ECHEC idempotence : {rows_after_first} -> {rows_after_second} lignes "
                "(le second passage a duplique des sorties)",
                file=sys.stderr,
            )
            return 1

        print(f"OK idempotence : {rows_after_second} lignes stables apres 2 passages ({db_path})")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
