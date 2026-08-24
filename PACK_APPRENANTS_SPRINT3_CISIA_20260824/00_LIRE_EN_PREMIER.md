# Sprint 3 CISIA — Pack apprenants · édition cohérence finale du 24/08/2026

Ce pack contient les supports projetés, les guides pas à pas et les exercices à remettre. Il ne contient
ni notes orateur, ni correction formateur, ni sortie de référence pré-calculée du laboratoire vision.

## Avant de commencer

1. Lis d'abord
   `03_GUIDES_FICHES_ET_REVISION\guide_multiplateforme_apprenant_sprint3.md`
   et choisis ta colonne : Windows PowerShell, macOS zsh ou Linux bash.
2. Crée un dossier de travail court : `C:\CISIA\S3` sous Windows, ou
   `~/CISIA/S3` sous macOS/Linux.
3. Clone `https://github.com/thomasfesq/CISIA_24082026_Parcours.git`, crée ta branche personnelle,
   puis ouvre ce dossier dans VS Code avec **Fichier > Ouvrir un dossier**. Le `main` reçu est le point
   de départ reconstruit de fin Sprint 2 ; n'explore pas les jalons futurs.
4. Ouvre **Terminal > Nouveau terminal**. Les commandes se saisissent dans ce
   terminal, jamais dans un fichier Python, une cellule de notebook ou GitHub.
5. Vérifie la racine selon ton système :

```powershell
# Windows PowerShell
Get-Location
Test-Path -LiteralPath .\pyproject.toml
Test-Path -LiteralPath .\uv.lock
git remote get-url origin
git branch --show-current
Get-Content -LiteralPath .\FORMATION\JALON_ACTUEL.md -TotalCount 1
```

```bash
# macOS zsh ou Linux bash
pwd
test -f ./pyproject.toml && echo 'pyproject.toml : OK'
test -f ./uv.lock && echo 'uv.lock : OK'
git remote get-url origin
git branch --show-current
head -n 1 ./FORMATION/JALON_ACTUEL.md
```

Attendu : l'URL du dépôt officiel, le nom de ta branche personnelle et le marqueur
`00-reconstruction-fin-sprint2`. Si tu es sur `main` ou `jalon/...`, crée ou retrouve ta branche
personnelle avant toute modification. N'applique aucun ancien correctif de dépôt : les jalons officiels
contiennent déjà les évolutions au moment pédagogique prévu.

## Ordre d'utilisation

1. Lire `03_GUIDES_FICHES_ET_REVISION\guide_multiplateforme_apprenant_sprint3.pdf`, puis
   `prerequis_express_et_glossaire_sprint3.pdf`.
2. Garder ouverts le guide multiplateforme et
   `03_GUIDES_FICHES_ET_REVISION\pas_a_pas_apprenant_sprint3.pdf` : ce dernier indique l'outil à
   ouvrir, le terminal à lancer, la commande, le résultat attendu et le plan B.
3. Utiliser la présentation PPTX ou PDF du module en cours, puis la fiche correspondante dans
   `fiches_TD_apprenant_sprint3.pdf`.
4. Pour M25, copier le dossier complet
   `05_DONNEES_ET_EXERCICES\07_M25_API_PROOFS\tp_api_m25_v1_20260823` à côté du clone et suivre son
   `README.md`. L'applicateur Python commun fonctionne sous Windows, macOS et
   Linux ; la suite ciblée de référence vaut **12 passed**.
5. Pour PayGuard, décompresser `05_DONNEES_ET_EXERCICES\tp_payguard_apprenants.zip` dans
   un sous-dossier `payguard`, puis ouvrir `pas_a_pas_apprenant_payguard.pdf`. L'état initial normal est
   `10 failed · 1 passed · 1 skipped` ; la preuve finale est `12 passed`. Ne modifie jamais les tests.
6. Pour J5 matin, suivre
   `05_DONNEES_ET_EXERCICES\tp_drift_indusense\PAS_A_PAS_apprenant_indusense.md` ; le formateur
   annonce chaque transition et chaque pause.
7. Ouvrir `05_DONNEES_ET_EXERCICES\vision_metrics_lab_v1_20260823.zip` uniquement à la consigne du
   formateur. Le ZIP contient le laboratoire à produire, sans correction ni résultats de référence.
8. Ne pas ouvrir `05_DONNEES_ET_EXERCICES\GAME_DAY` avant la consigne du formateur. Le guide Markdown
   `GAME_DAY\gameday_apprenant.md` et le PDF séparé `05_DONNEES_ET_EXERCICES\gameday_apprenant.pdf`
   sont deux rendus synchronisés de la même version. Le bundle autonome est dans le dossier `GAME_DAY`.
9. Après chaque journée, compléter le journal de bord et l'auto-évaluation ; déposer la sortie de test,
   les fichiers demandés et l'explication courte exigée par la fiche TD.

Le journal dans `03_GUIDES_FICHES_ET_REVISION` est la copie de lecture ; celui de
`04_FICHIERS_A_COMPLETER` est ta copie de travail à renseigner. Ils démarrent identiques volontairement.

## Règles techniques communes

- Exécuter `uv sync --frozen --extra dev` depuis le projet concerné ; ne pas lancer `uv add` pour réparer
  une séance et ne jamais modifier `uv.lock` sans consigne.
- Toute commande Python du cours passe par `uv run`.
- En cas d'erreur, conserver le message complet, exécuter `Get-Location` sous Windows ou `pwd` sous
  macOS/Linux, vérifier `pyproject.toml`, puis appeler le formateur si le blocage persiste.
- Pour M33, le formateur fournit le chemin absolu du `perf/locustfile.py` pédagogique. Ne pas utiliser un
  fichier homonyme trouvé dans le clone.
- Ne jamais déposer `.env`, clé API, mot de passe, jeton, cookie, donnée personnelle ou capture contenant
  un secret.

SHA-256 PayGuard : `D86238FD4016B5DDB01E9094E539DB0B8370395D53912F4648A12E2E1E814885`.
