# [PÉDAGOGIE] ============================================================================
# [PÉDAGOGIE] FICHIER — tests/test_security.py
# [PÉDAGOGIE] MODULE  — M26 — sécurité d'API et défense en profondeur
# [PÉDAGOGIE] RÔLE    — Appliquer des garde-fous indépendants aux frontières HTTP et prouver leurs
# [PÉDAGOGIE]           codes d'erreur.
# [PÉDAGOGIE] THÉORIE — authentification, taille maximale et limitation de débit couvrent des
# [PÉDAGOGIE]           menaces distinctes
# [PÉDAGOGIE]           • une règle serveur ne doit pas être surchargeable par un paramètre fourni
# [PÉDAGOGIE]             par le client
# [PÉDAGOGIE]           • 400, 401, 413 et 429 décrivent des contrats d'échec différents
# [PÉDAGOGIE] À VOIR  — Les tests doivent observer le statut HTTP et l'absence de contournement,
# [PÉDAGOGIE]           pas seulement une exception Python.
# [PÉDAGOGIE] PIÈGE   — Un rate limit en mémoire ne se partage pas entre processus ; documenter
# [PÉDAGOGIE]           cette limite de conception.
# [PÉDAGOGIE] GARDE   — Toutes les lignes marquées [PÉDAGOGIE] sont des commentaires : elles
# [PÉDAGOGIE]           guident la lecture sans changer l'exécution.
# [PÉDAGOGIE] ============================================================================

# =============================================================================
# FICHIER : tests/test_security.py
# RÔLE    : Tests des PROTECTIONS de sécurité du module 26 (garde-fous de l'API).
# -----------------------------------------------------------------------------
# CE QUE CE FICHIER VÉRIFIE (vue d'ensemble, pour un·e débutant·e) :
#   - La protection "PAYLOAD TROP GROS" : si un client envoie un corps de requête
#     plus volumineux que la limite autorisée, l'API refuse avec un code 413
#     (Payload Too Large). But : éviter qu'une requête énorme ne sature la mémoire
#     ou ne serve à attaquer le service (déni de service).
#   - La protection "RATE LIMIT" (limitation de débit) : un même client ne peut
#     pas envoyer un nombre illimité de requêtes dans une fenêtre de temps donnée.
#     Une fois la limite atteinte, la requête suivante est rejetée avec un code 429
#     (Too Many Requests). But : empêcher les abus / le matraquage de l'API.
#
# CES DEUX MÉCANISMES VIVENT DANS LE MODULE ``indusense.api.security``.
# Les tests appellent soit l'API entière (via TestClient), soit DIRECTEMENT les
# fonctions/variables internes de ce module de sécurité pour les vérifier finement.
# =============================================================================

# --- Imports : on ne change RIEN ici (mêmes noms, même ordre). ---------------

# pytest : le framework de tests. On s'en sert ici notamment pour
# ``pytest.raises(...)``, qui permet de vérifier qu'un bloc de code lève bien
# une exception attendue (sinon le test échoue).
# [PÉDAGOGIE] DÉPENDANCE — pytest : exprime les garanties sous forme de tests exécutables.
import pytest

# HTTPException : l'exception "HTTP" de FastAPI. Quand le code de sécurité veut
# renvoyer une erreur HTTP (ex : 429), il lève une HTTPException portant le code.
from fastapi import HTTPException

# TestClient : le "faux navigateur" qui appelle notre application sans ouvrir de
# vrai port réseau (voir explications détaillées dans test_api.py).
from fastapi.testclient import TestClient

# loguru.logger : la même bibliothèque de journalisation que main.py. On lui
# attache un "sink" temporaire (une liste Python) pour CAPTURER les lignes de
# log émises pendant un test, sans écrire sur disque.
from loguru import logger

# security : le module qui contient les garde-fous (limite de taille du corps,
# limitation de débit, et leurs constantes/états internes).
from indusense.api import security

# app : l'application FastAPI complète (avec ses routes et ses middlewares de sécurité).
from indusense.api.main import app

# On crée le client de test une seule fois, partagé par les tests de ce fichier.
# [PÉDAGOGIE] CONSTANTE / CONTRAT — cette valeur nommée centralise un choix partagé au lieu de le
# [PÉDAGOGIE] disperser.
client = TestClient(app)


# [PÉDAGOGIE] BLOC `test_payload_too_large_returns_413` — ce test transforme un comportement
# [PÉDAGOGIE] attendu en contrat de non-régression.
# [PÉDAGOGIE] CONTRAT — entrées : aucun argument explicite ; preuve : la dernière assertion est
# [PÉDAGOGIE] l'oracle : son échec doit pointer la garantie cassée.
def test_payload_too_large_returns_413():
    """Vérifie que l'API rejette un corps de requête TROP VOLUMINEUX (-> 413).

    POURQUOI : pour se protéger, l'API fixe une taille maximale de corps,
    stockée dans ``security.MAX_BODY_BYTES``. Si le corps dépasse cette limite,
    elle doit répondre 413 (Payload Too Large) sans même tenter de traiter
    la requête. Cela évite la surconsommation de mémoire et certaines attaques.
    """
    r = client.post(
        "/predict-tabular",
        # On fournit la clé API : on veut tester la limite de TAILLE, pas l'auth.
        headers={"X-API-Key": "dev-key"},
        # content=... : ici on envoie un corps BRUT (octets), pas du JSON.
        #   b"x" * (MAX_BODY_BYTES + 1) construit une chaîne d'octets composée
        #   de la lettre "x" répétée (limite autorisée + 1) fois.
        #   -> volontairement UN octet de trop pour DÉPASSER la limite.
        content=b"x" * (security.MAX_BODY_BYTES + 1),
    )

    # Comportement attendu : 413, car le corps dépasse la taille maximale permise.
    # [PÉDAGOGIE] ORACLE — l'assertion compare le résultat observé au contrat attendu par ce test.
    assert r.status_code == 413


# [PÉDAGOGIE] BLOC `test_invalid_content_length_returns_400` — ce test transforme un comportement
# [PÉDAGOGIE] attendu en contrat de non-régression.
# [PÉDAGOGIE] CONTRAT — entrées : aucun argument explicite ; preuve : la dernière assertion est
# [PÉDAGOGIE] l'oracle : son échec doit pointer la garantie cassée.
def test_invalid_content_length_returns_400():
    """Une taille déclarée illisible doit produire une erreur client, jamais un crash serveur."""
    r = client.post(
        "/predict-tabular",
        headers={"X-API-Key": "dev-key", "Content-Length": "pas-un-entier"},
        content=b"{}",
    )

    # [PÉDAGOGIE] ORACLE — l'assertion compare le résultat observé au contrat attendu par ce test.
    assert r.status_code == 400
    # [PÉDAGOGIE] ORACLE — l'assertion compare le résultat observé au contrat attendu par ce test.
    assert r.json() == {"detail": "Content-Length invalide"}


# [PÉDAGOGIE] BLOC `test_rate_limit_policy_is_not_exposed_as_query_parameters` — ce test
# [PÉDAGOGIE] transforme un comportement attendu en contrat de non-régression.
# [PÉDAGOGIE] CONTRAT — entrées : aucun argument explicite ; preuve : la dernière assertion est
# [PÉDAGOGIE] l'oracle : son échec doit pointer la garantie cassée.
def test_rate_limit_policy_is_not_exposed_as_query_parameters():
    """Un client ne doit pas pouvoir augmenter la limite via ``?limit=`` ou ``?window=``."""
    operation = app.openapi()["paths"]["/predict-tabular"]["post"]
    parameter_names = {parameter["name"] for parameter in operation.get("parameters", [])}

    # [PÉDAGOGIE] ORACLE — l'assertion compare le résultat observé au contrat attendu par ce test.
    assert "limit" not in parameter_names
    # [PÉDAGOGIE] ORACLE — l'assertion compare le résultat observé au contrat attendu par ce test.
    assert "window" not in parameter_names


# [PÉDAGOGIE] BLOC `test_rate_limit_blocks_after_limit` — ce test transforme un comportement
# [PÉDAGOGIE] attendu en contrat de non-régression.
# [PÉDAGOGIE] CONTRAT — entrées : aucun argument explicite ; preuve : la dernière assertion est
# [PÉDAGOGIE] l'oracle : son échec doit pointer la garantie cassée.
def test_rate_limit_blocks_after_limit():
    """Vérifie la LIMITATION DE DÉBIT : au-delà de N requêtes, on bloque (-> 429).

    POURQUOI : un même client (identifié par son adresse IP) ne doit pas pouvoir
    inonder l'API. La fonction ``security.rate_limit`` compte les appels d'une IP
    dans une fenêtre de temps. Tant qu'on est sous la limite, elle laisse passer ;
    dès qu'on la dépasse, elle lève une HTTPException avec le code 429.

    NOTE : ce test appelle DIRECTEMENT la fonction interne ``rate_limit`` (au lieu
    de passer par TestClient). On peut ainsi simuler précisément le compteur et
    fabriquer de faux objets "requête" minimalistes.
    """
    # security._hits : le "compteur" interne (mémoire des appels par IP).
    # On le VIDE au début pour partir d'un état propre, indépendant des autres tests.
    # Le ``_`` devant ``_hits`` signale une variable interne/privée du module.
    security._hits.clear()

    # On fabrique de FAUX objets très simples pour imiter ce que ``rate_limit``
    # attend en entrée. Pas besoin d'une vraie requête HTTP complète :
    # il suffit de fournir la même "forme" (les attributs réellement lus).

    # [PÉDAGOGIE] TYPE `_Client` — regroupe un état cohérent et le contrat des opérations
    # [PÉDAGOGIE] associées.
    # [PÉDAGOGIE] THÉORIE — nommer ce type rend les invariants visibles et facilite les tests à la
    # [PÉDAGOGIE] frontière.
    class _Client:
        # rate_limit lit l'adresse IP via req.client.host : on en met une factice.
        host = "9.9.9.9"

    # [PÉDAGOGIE] TYPE `_Req` — regroupe un état cohérent et le contrat des opérations associées.
    # [PÉDAGOGIE] THÉORIE — nommer ce type rend les invariants visibles et facilite les tests à la
    # [PÉDAGOGIE] frontière.
    class _Req:
        # rate_limit lit req.client : on lui donne une instance de _Client ci-dessus.
        client = _Client()

    # req : notre fausse requête, vue par rate_limit comme venant de l'IP 9.9.9.9.
    req = _Req()

    # On appelle rate_limit EXACTEMENT 60 fois (limit=60), dans une fenêtre de 60s.
    # Ces 60 appels sont PILE à la limite : ils doivent TOUS passer sans erreur.
    # [PÉDAGOGIE] ITÉRATION — appliquer la même règle à chaque élément permet de raisonner sur un
    # [PÉDAGOGIE] invariant stable.
    for _ in range(60):
        security.rate_limit(req, limit=60, window=60.0)

    # Le 61e appel dépasse la limite : on s'attend à ce qu'il LÈVE une HTTPException.
    # ``with pytest.raises(HTTPException) as e:`` -> le test réussit seulement si
    # une HTTPException est bien levée à l'intérieur du bloc (sinon il échoue).
    # [PÉDAGOGIE] RESSOURCE — le gestionnaire de contexte garantit ouverture et libération, même
    # [PÉDAGOGIE] en cas d'exception.
    with pytest.raises(HTTPException) as e:
        # Cet appel supplémentaire (le 61e) doit être REFUSÉ.
        security.rate_limit(req, limit=60, window=60.0)

    # e.value : l'exception réellement levée. On vérifie que son code HTTP est 429
    # (Too Many Requests), confirmant que la limitation de débit a bien bloqué.
    # [PÉDAGOGIE] ORACLE — l'assertion compare le résultat observé au contrat attendu par ce test.
    assert e.value.status_code == 429


# [PÉDAGOGIE] BLOC `test_no_secret_or_payload_leak_in_logs` — ce test transforme un comportement
# [PÉDAGOGIE] attendu en contrat de non-régression.
# [PÉDAGOGIE] CONTRAT — entrées : aucun argument explicite ; preuve : la dernière assertion est
# [PÉDAGOGIE] l'oracle : son échec doit pointer la garantie cassée.
def test_rate_limit_burst_returns_429_over_http():
    """Rafale de 70 requêtes RÉELLES via l'API : au moins un 429 doit apparaître.

    POURQUOI : ``test_rate_limit_blocks_after_limit`` prouve la mécanique du
    compteur en appelant ``security.rate_limit`` directement, avec une fausse
    requête fabriquée à la main — mais ça ne prouve pas que la dépendance est
    bien branchée sur la route réelle. Ce test-ci passe par ``TestClient``, donc
    par toute la chaîne HTTP (middlewares, auth, dépendances), pour vérifier que
    le garde-fou agit vraiment sur du trafic qui ressemble à un usage réel.

    NOTE : la politique appliquée ici est celle FIXE de ``rate_limit_dependency``
    (60 requêtes/minute/IP) — pas les 60 du test unitaire au-dessus, qui sont
    juste une coïncidence de valeur par défaut.
    """
    # On repart d'un compteur vide pour ne pas hériter de requêtes d'un autre
    # test (même mécanisme que ``test_rate_limit_blocks_after_limit``).
    security._hits.clear()

    # Un corps par ailleurs valide : on veut isoler le comportement du LIMITEUR
    # DE DÉBIT, pas déclencher un 422/503 qui masquerait le signal recherché.
    readings = [
        {
            "timestamp": f"2025-02-01T{h:02d}:00:00",
            "temperature": 50 + h,
            "pressure_bar": 195 + h * 0.5,
        }
        for h in range(8)
    ]

    # 70 appels réels > 60 (la limite) : les 10 derniers doivent être bloqués.
    # TestClient envoie toutes ces requêtes depuis la même IP simulée -> elles
    # partagent le même compteur côté ``rate_limit_dependency``.
    status_codes = [
        client.post(
            "/predict-tabular",
            headers={"X-API-Key": "dev-key"},
            json={"machine_id": "MACH-01", "readings": readings},
        ).status_code
        for _ in range(70)
    ]

    # On nettoie pour ne pas polluer les tests suivants.
    security._hits.clear()

    # Comportement attendu : au moins une réponse 429 dans la rafale.
    assert 429 in status_codes


def test_no_secret_or_payload_leak_in_logs():
    """Vérifie qu'aucune ligne de log n'expose la clé API ni le contenu du payload.

    POURQUOI (menace *Information disclosure* du threat model, module 26) : un log
    bavard qui reproduit la clé API ou les relevés capteurs transformerait un outil
    de diagnostic en fuite de données. Ce test capture les logs émis pendant un
    appel réel à ``/predict-tabular`` et vérifie leur absence, quel que soit le
    code de réponse obtenu (401 ici : pas besoin d'un modèle chargé).

    IMPORTANT : ce test prouve la non-divulgation, pas l'existence d'un audit
    logging structuré — celui-ci reste Planifié v0 (cf. security_controls.md).
    """
    captured: list[str] = []
    # On attache un "sink" temporaire : chaque ligne de log formatée est ajoutée
    # à la liste `captured`. On le retire à la fin (bloc try/finally) pour ne pas
    # polluer les autres tests.
    secret_value = "un-secret-de-test-tres-identifiable"
    payload_marker = "capteur-donnee-sensible-9982"
    sink_id = logger.add(captured.append, level="TRACE")
    try:
        client.post(
            "/predict-tabular",
            headers={"X-API-Key": secret_value},
            json={"machine_id": payload_marker, "readings": []},
        )
    finally:
        logger.remove(sink_id)

    logs_text = "\n".join(captured)
    # [PÉDAGOGIE] ORACLE — l'assertion compare le résultat observé au contrat attendu par ce test.
    assert secret_value not in logs_text
    # [PÉDAGOGIE] ORACLE — l'assertion compare le résultat observé au contrat attendu par ce test.
    assert payload_marker not in logs_text
