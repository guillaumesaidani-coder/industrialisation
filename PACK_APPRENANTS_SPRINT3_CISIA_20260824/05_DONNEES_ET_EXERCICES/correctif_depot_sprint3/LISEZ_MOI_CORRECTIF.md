# ARCHIVE OBSOLÈTE — ne pas appliquer ce correctif

> ⚠️ **Ne pas exécuter, ne pas débloquer et ne pas appliquer les fichiers de ce dossier.** Cette archive
> est conservée uniquement pour la traçabilité d'un état antérieur au dépôt
> `CISIA_24082026_Parcours`. Le `main` et les jalons officiels contiennent désormais les évolutions au
> moment pédagogique prévu. Appliquer ce patch créerait un état local non conforme au parcours.
>
> `APPLIQUER_CORRECTIF_SPRINT3.ps1` est volontairement neutralisé : il s'arrête immédiatement avec une
> explication, avant de résoudre un chemin, lire le dépôt ou modifier un fichier.

## Pourquoi cette archive est conservée

Au contrôle du **23/08/2026**, un ancien état de `main` ne contenait pas encore quatre corrections que
les supports utilisaient. Le patch historique couvrait alors :

1. le wrapper FastAPI `rate_limit_dependency` qui empêche de contourner le quota par des paramètres de requête ;
2. le refus propre en **400** d'un `Content-Length` illisible ;
3. les images Prometheus `v2.53.0` et Grafana `11.1.0` épinglées ;
4. l'installation CI reproductible avec `uv sync --frozen --extra dev`.

Ces informations expliquent la provenance de l'archive ; elles ne constituent plus une procédure de
séance. Pour travailler, cloner le dépôt officiel, rester sur une branche personnelle et charger
uniquement `jalon/01` à `jalon/12` au signal du formateur avec les scripts `mettre_a_niveau`.

<details>
<summary>Historique obsolète conservé pour audit — ne pas exécuter</summary>

## À préparer

- **Explorateur Windows** : décompresser ce dossier à un emplacement connu.
- **VS Code** : ouvrir le dossier `CISIA_24082026_Parcours` avec **Fichier > Ouvrir un dossier**.
- **Terminal PowerShell de VS Code** : menu **Terminal > Nouveau terminal**. Vérifier que `pyproject.toml` et `uv.lock` sont visibles dans l'explorateur.
- Garder le chemin complet du script sous la main : dans l'Explorateur Windows, **Maj + clic droit > Copier en tant que chemin**.

## Application — dans PowerShell, pas dans un fichier Python ni dans GitHub

Depuis le terminal ouvert à la racine de `CISIA_24082026_Parcours` :

```powershell
$correctif = "C:\CHEMIN\VERS\correctif_depot_sprint3\APPLIQUER_CORRECTIF_SPRINT3.ps1"
& $correctif -RepoPath "."
```

Si PowerShell bloque uniquement ce script téléchargé :

```powershell
Unblock-File -LiteralPath $correctif
& $correctif -RepoPath "."
```

Ne changez pas durablement la politique d'exécution de Windows.

## Preuve attendue

Le script affiche `OK — socle Sprint 3 aligné localement` puis exactement quatre fichiers modifiés. Contrôler ensuite :

```powershell
Select-String -Path .\src\indusense\api\security.py -Pattern "def rate_limit_dependency|Content-Length invalide"
Select-String -Path .\docker-compose.yml -Pattern "prom/prometheus:v2.53.0|grafana/grafana:11.1.0"
Select-String -Path .\.github\workflows\ci.yml -Pattern "uv sync --frozen --extra dev"
uv sync --frozen --extra dev --extra mlops
uv run python -m black --check --no-cache .
uv run ruff check --no-cache .
uv run python -m pytest -q
```

Résultat contrôlé sur un clone propre de `origin/main` : **31 fichiers Black conformes**, Ruff sans
erreur et **30 tests réussis**. Sous Windows, la forme `uv run python -m ...` est volontaire : elle
évite les problèmes de lancement d'un exécutable console quand le chemin du clone est profond.

Relancer le script doit afficher `déjà présent` et ne rien modifier : c'est le contrôle d'idempotence.

## Si le script refuse

Ne forcez pas avec `git checkout`, `git reset` ou un copier-coller partiel. Conservez le message affiché et demandez au formateur : le dépôt contient probablement une autre révision ou un travail local à préserver.

</details>
