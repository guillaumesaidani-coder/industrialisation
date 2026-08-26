# [PÉDAGOGIE] ============================================================================
# [PÉDAGOGIE] FICHIER — tests/test_smoke_compose.py
# [PÉDAGOGIE] MODULE  — M28 — preuve que la stack Compose attend la readiness au démarrage
# [PÉDAGOGIE] RÔLE    — Vérifier, contre une VRAIE stack lancée par `docker compose up`, que les
# [PÉDAGOGIE]           3 services répondent ET que Prometheus a bien scrapé l'API avec succès.
# [PÉDAGOGIE] THÉORIE — un smoke test frappe le réseau réel (pas de TestClient in-process) : il
# [PÉDAGOGIE]           prouve l'orchestration (depends_on/healthcheck), pas seulement le code
# [PÉDAGOGIE]           • la cible Prometheus "up" est la preuve la plus forte : si l'ordre de
# [PÉDAGOGIE]             démarrage était faux, le premier scrape aurait échoué et resterait DOWN
# [PÉDAGOGIE] À VOIR  — ce fichier ne s'exécute utilement qu'APRÈS `docker compose up -d --build`
# [PÉDAGOGIE]           (voir la preuve du jalon 06). Sans stack lancée, il se SKIP proprement
# [PÉDAGOGIE]           plutôt que d'échouer, pour ne pas casser `uv run pytest -q` en local.
# [PÉDAGOGIE] PIÈGE   — Un simple `requests.get` immédiatement après `up -d` peut taper une
# [PÉDAGOGIE]           fenêtre où les conteneurs tournent mais ne sont pas encore "healthy" :
# [PÉDAGOGIE]           on retente donc avec un budget de temps plutôt que d'échouer au 1er essai.
# [PÉDAGOGIE] GARDE   — Toutes les lignes marquées [PÉDAGOGIE] sont des commentaires : elles
# [PÉDAGOGIE]           guident la lecture sans changer l'exécution.
# [PÉDAGOGIE] ============================================================================

from __future__ import annotations

import time

import pytest
import requests

API_URL = "http://127.0.0.1:8000"
PROMETHEUS_URL = "http://127.0.0.1:9090"
GRAFANA_URL = "http://127.0.0.1:3000"

# Budget total pour attendre que les healthchecks passent au vert (services
# prometheus/grafana ont un intervalle de 10s, retries=5 -> jusqu'à ~50s).
_TIMEOUT_S = 60.0
_POLL_S = 2.0


def _wait_for(url: str, expected_status: int = 200) -> requests.Response:
    """Interroge `url` jusqu'à `expected_status` ou expiration du budget.

    Distingue deux cas d'échec : la stack n'est pas lancée du tout (SKIP
    immédiat, pas de raison d'attendre 60s) contre la stack tourne mais un
    service n'est pas encore "healthy" (on retente avec un budget de temps).
    """
    try:
        requests.get(url, timeout=3)
    except requests.exceptions.ConnectionError:
        pytest.skip(
            f"Stack Compose injoignable ({url}) : lancer `docker compose up -d --build` avant "
            "ce smoke test."
        )

    deadline = time.monotonic() + _TIMEOUT_S
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            response = requests.get(url, timeout=3)
        except requests.exceptions.ConnectionError as exc:
            last_error = exc
            time.sleep(_POLL_S)
            continue
        if response.status_code == expected_status:
            return response
        last_error = AssertionError(f"{url} -> {response.status_code}")
        time.sleep(_POLL_S)
    raise AssertionError(f"{url} n'a jamais renvoyé {expected_status} : {last_error}")


def test_api_health_is_ok():
    body = _wait_for(f"{API_URL}/health").json()
    assert body == {"status": "ok"}


def test_api_ready_has_loaded_model():
    body = _wait_for(f"{API_URL}/ready").json()
    assert body["status"] == "ready"
    assert body["model_version"]


def test_prometheus_is_ready():
    response = _wait_for(f"{PROMETHEUS_URL}/-/ready")
    assert "Ready" in response.text or response.status_code == 200


def test_grafana_is_healthy():
    body = _wait_for(f"{GRAFANA_URL}/api/health").json()
    assert body["database"] == "ok"


def test_prometheus_scraped_api_successfully():
    # [PÉDAGOGIE] PREUVE — cible "up" = Prometheus n'a démarré son scrape qu'une fois l'API
    # [PÉDAGOGIE] réellement prête (depends_on: api condition: service_healthy a fonctionné).
    # Juste après le démarrage, la cible peut encore afficher "unknown" : le premier
    # scrape (scrape_interval: 15s) n'a pas forcément eu lieu. On retente donc sur le
    # CONTENU (pas seulement le code HTTP 200) jusqu'à observer "up".
    deadline = time.monotonic() + _TIMEOUT_S
    health = "unknown"
    while time.monotonic() < deadline:
        payload = _wait_for(f"{PROMETHEUS_URL}/api/v1/targets").json()
        targets = payload["data"]["activeTargets"]
        api_targets = [t for t in targets if t["labels"].get("job") == "indusense-api"]
        assert api_targets, "cible 'indusense-api' absente de /api/v1/targets"
        health = api_targets[0]["health"]
        if health == "up":
            return
        time.sleep(_POLL_S)
    raise AssertionError(f"cible 'indusense-api' jamais 'up' (dernier état : {health!r})")
