"""Preuve d'idempotence du pipeline Prefect (M29/M30).

Rejoue deux fois le flow `indusense_pipeline` sur une base SQLite temporaire
fraiche et verifie que le second passage ne duplique aucune ligne stockee.
Reference : FORMATION/JALONS/07-j4-matin-m29-m30.md
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from indusense.config import settings
from indusense.flows.predict_flow import count_predictions, indusense_pipeline


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="indusense-preuve-") as tmp:
        db_path = Path(tmp) / "predictions.db"
        assert not db_path.exists(), "la base de preuve doit etre neuve, jamais reutilisee"
        db_url = f"sqlite:///{db_path.as_posix()}"

        first = indusense_pipeline(data_dir=settings.data_dir, db_url=db_url)
        rows_after_first = count_predictions(db_url)

        second = indusense_pipeline(data_dir=settings.data_dir, db_url=db_url)
        rows_after_second = count_predictions(db_url)

        print(f"1er passage : rows_scored={first['rows_scored']} rows_in_db={rows_after_first}")
        print(f"2e  passage : rows_scored={second['rows_scored']} rows_in_db={rows_after_second}")

        if rows_after_first != rows_after_second:
            print(
                f"ECHEC idempotence : {rows_after_first} -> {rows_after_second} lignes "
                "(le second passage a duplique des sorties)",
                file=sys.stderr,
            )
            return 1

        print(f"OK idempotence : {rows_after_second} lignes stables apres 2 passages ({db_url})")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
