"""Charge légère M33, sans dépendance ajoutée au verrou de l'application."""

from __future__ import annotations

import json
import os
from pathlib import Path

from locust import HttpUser, between, task


SPRINT_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATH = SPRINT_ROOT / "payload.json"


def _load_payload() -> dict[str, object]:
    """Charge le corps une seule fois au démarrage du processus Locust."""

    with PAYLOAD_PATH.open(encoding="utf-8") as stream:
        payload = json.load(stream)
    if len(payload.get("readings", [])) < 7:
        raise RuntimeError(f"{PAYLOAD_PATH} doit contenir au moins 7 relevés")
    return payload


def _load_api_key() -> str:
    """Lit la clé depuis l'environnement, jamais depuis une constante versionnée."""

    api_key = os.environ.get("INDUSENSE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "INDUSENSE_API_KEY est absent : chargez la valeur du .env dans le terminal "
            "PowerShell avant de lancer Locust."
        )
    return api_key


PAYLOAD = _load_payload()


class InduSenseUser(HttpUser):
    """Client tabulaire à cadence compatible avec la limite pédagogique de 60/min."""

    wait_time = between(18.0, 22.0)

    def on_start(self) -> None:
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": _load_api_key(),
        }

    @task
    def predict_tabular(self) -> None:
        self.client.post(
            "/predict-tabular",
            json=PAYLOAD,
            headers=self.headers,
            name="/predict-tabular",
        )
