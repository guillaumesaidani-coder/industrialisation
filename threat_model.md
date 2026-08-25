# Threat model — InduSense API (module 26)

Périmètre : `POST /predict-tabular` et le pipeline qu'il déclenche (normalisation
`machine_id` → features temporelles → sélection de colonnes → `predict_proba`).
Actifs à protéger : la clé API, le modèle chargé en mémoire, les relevés capteurs
transmis par le client, la disponibilité du service.

## STRIDE

| Menace | Exemple concret sur `/predict-tabular` | Contrôle actuel |
|---|---|---|
| **S**poofing (usurpation) | Un client sans clé API se présente comme un système autorisé. | `require_api_key` → 401 si `X-API-Key` absente ou fausse. |
| **T**ampering (altération) | Un payload JSON malformé, un `machine_id` sans numéro exploitable, ou un historique trop court pour calculer les features. | Validation Pydantic (`TabularPredictionRequest`, `min_length=7`) → 422 ; `normalize_machine_id` lève `ValueError` → 422 ; `feats.empty` → 422. |
| **R**epudiation (déni d'action) | Impossible aujourd'hui de prouver après coup qui a appelé l'API et quand, en dehors du `X-Request-ID` de corrélation technique. | Aucun événement d'audit structuré. Le `request_id` (middleware `add_request_id`) corrèle les logs d'une requête mais ne constitue pas une preuve d'audit. **Risque résiduel assumé, action : Audit logging (Planifié v0).** |
| **I**nformation disclosure (fuite) | Le rate limit accepte des paramètres `?limit=`/`?window=` en clair dans l'OpenAPI, ou les logs affichent la clé API / le payload / des données machine identifiantes. | `rate_limit_dependency` n'expose que `request` (pas `limit`/`window`) dans le schéma OpenAPI ; aucune trace ne doit contenir clé, payload ou PII (règle de conception, à vérifier par test dédié — cf. TP3). |
| **D**enial of service (déni de service) | Un client envoie un corps de requête énorme, ou bombarde l'API de requêtes. | `limit_body_size` → 413 au-delà de 64 Ko (contrôle déclaratif sur `Content-Length`, pas un comptage effectif des octets reçus) ; `rate_limit_dependency` → 429 au-delà de 60 requêtes/min/IP (état en mémoire, par processus, non partagé entre plusieurs instances). |
| **E**levation of privilege (élévation de privilège) | Un client authentifié tente d'agir hors de son périmètre (ex. accéder aux métriques internes ou à une route non prévue). | Pas de rôles multiples dans le contrat actuel : la clé API est un secret unique, tout-ou-rien. `/metrics` est exposé sans authentification dédiée (usage interne de supervision) — risque à documenter, pas de preuve de contrôle spécifique aujourd'hui. |

## Limites connues (assumées, pas des angles morts)

- **Rate limit non distribué** : `_hits` vit en mémoire et par processus. Plusieurs
  instances de l'API ne partagent pas le compteur → contournable en répartissant
  les requêtes derrière un load balancer multi-instances.
- **Taille de payload déclarative** : `limit_body_size` fait confiance à l'en-tête
  `Content-Length`. Un client qui l'omet (chunked) ou qui ment peut faire passer un
  corps réel plus gros ; un contrôle effectif nécessiterait de compter les octets au
  niveau ASGI ou une limite au reverse-proxy.
- **Audit logging absent** : aucun événement structuré ne trace qui a appelé quoi et
  quand, au-delà de l'identifiant de corrélation `X-Request-ID`. Statut : Planifié v0.

## Pipeline (résumé du cycle réel de la requête)

`X-API-Key` (401) → `rate_limit_dependency` (429) → validation Pydantic (422) →
`normalize_machine_id` / features temporelles (422 si historique insuffisant) →
modèle chargé ? (503 sinon) → réponse 200.
