# Registre des contrôles de sécurité — InduSense API (module 26)

Statut au 25/08/2026 : **4 contrôles implémentés et prouvés par test**, **1 contrôle
planifié**. « Implémenté » signifie ici : code présent en production ET couvert par
un test qui observe le code HTTP réel, pas seulement une exception Python interne.

| Contrôle | Statut | Preuve actuelle | Risque résiduel | Action suivante |
|---|---|---|---|---|
| Auth | Implémenté | `require_api_key` → 401 sans clé/clé invalide, testé dans `tests/test_api.py`. | Clé unique partagée (tout-ou-rien), pas de rotation automatisée. | Documenter la procédure de rotation de `INDUSENSE_API_KEY`. |
| Validation | Implémenté | Pydantic (`TabularPredictionRequest`, `min_length=7`) + `normalize_machine_id` → 422, testé dans `tests/test_api.py`. | Un historique valide en forme mais métier-incohérent (ex. doublons d'horodatage) passe la validation de forme ; `feats.empty` rattrape une partie des cas limites. | Ajouter un test de payload métier-incohérent supplémentaire si le besoin apparaît. |
| Rate limit | Implémenté | `rate_limit_dependency` → 429 au-delà de 60 req/min/IP, testé directement (60 passent, 61e bloqué) dans `tests/test_security.py::test_rate_limit_blocks_after_limit`. | État en mémoire, par processus : non partagé entre plusieurs instances de l'API. | Documenter la limite ; migrer vers un stockage partagé (ex. Redis) si passage en multi-instances. |
| Taille payload | Implémenté | `limit_body_size` → 413 au-delà de 64 Ko, testé dans `tests/test_security.py::test_payload_too_large_returns_413` ; `Content-Length` illisible → 400, testé dans `test_invalid_content_length_returns_400`. | Contrôle déclaratif sur l'en-tête `Content-Length`, pas un comptage effectif des octets reçus (contournable en chunked ou en mentant sur l'en-tête). | Ajouter un comptage effectif au niveau ASGI ou une limite au reverse-proxy si le service est exposé publiquement. |
| Audit logging | Planifié v0 | Aucun événement structuré aujourd'hui : seul `X-Request-ID` corrèle les logs d'une requête, ce n'est pas une preuve d'audit. | Aucune traçabilité de qui a appelé quoi et quand en cas d'incident. | Émettre un événement structuré (horodatage, request_id, route, code retour) **sans clé, sans payload, sans PII**, puis écrire un test dédié qui le prouve. |

## Note de méthode

- Un contrôle **priorisé n'est pas un contrôle implémenté** : seuls Auth, Validation,
  Rate limit et Taille payload ont aujourd'hui une preuve automatisée (code HTTP
  observé par un test). L'audit logging reste Planifié v0 tant qu'aucun événement ni
  test dédié n'existe.
- Règle transverse : ne jamais logguer une clé API, un payload brut ou une donnée à
  caractère personnel — un log bavard est une fuite (menace *Information disclosure*
  du threat model).
