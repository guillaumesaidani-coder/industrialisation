"""Point d'entree jalon 07 (modules 29-30) : `uv run --frozen python flows/pipeline.py`.

Delegue entierement a `indusense.flows.predict_flow`, le module empaquete
executable aussi dans le conteneur API via `python -m indusense.flows.predict_flow`
(module 30, docker compose run). Garde ce script racine uniquement pour la
commande de preuve du jalon, sans dupliquer la logique du flow.
"""

from __future__ import annotations

from indusense.flows.predict_flow import indusense_pipeline, main

__all__ = ["indusense_pipeline", "main"]

if __name__ == "__main__":
    main()
