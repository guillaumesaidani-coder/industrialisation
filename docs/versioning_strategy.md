# Strategie de versioning — InduSense (M24)

| Objet | Source de verite | Identifiant/version | Stockage | Preuve de restauration |
|---|---|---|---|---|
| Code | Depot Git, branche personnelle puis PR vers `main` | Hash de commit (SHA) | Git | `git checkout <sha>` + CI verte (jobs `quality` + `build`) sur ce commit |
| Donnees | `data/gold/gold_dataset.csv` | Empreinte md5 (12 car.), ex. `637be8d38250` — stockee dans le pointeur `.dvc` et dans `gold_md5` de `model_metadata.json` | DVC — pointeur `data/gold/gold_dataset.csv.dvc` dans Git, contenu reel sur le remote `localremote` (`../dvc-store`, hors depot) | `git checkout` du commit puis `dvc checkout` ; `dvc status` doit repondre "Data and pipelines are up to date" |
| Modele | `artifacts/models/rf.joblib` + `model_metadata.json` | `run_id` MLflow (ex. `a31beaadbbc043b895407d3143a86635`) et version enregistree au Model Registry (`indusense-rf`, v1) | DVC (pointeur `.dvc` dans Git, poids reel sur le remote) + MLflow (tracking `sqlite:///mlflow.db` : parametres, metriques, artefact modele) | `dvc checkout` restaure le binaire exact ; le run/la version MLflow restaure le contexte (parametres, metriques, signature) |
| Secrets | Jamais dans Git | N/A | `.env` local (gitignore) pour le poste ; secrets GitHub Actions pour la CI | Hook `pre-commit` (`gitleaks`) bloque toute reintroduction ; un secret deja committe doit etre **revoque** cote fournisseur, pas seulement supprime |

## Questions a trancher

1. **Quel commit produit quel modele ?**
   Le commit qui fige ensemble les pointeurs `.dvc` (donnees + modele) avec `metrics.json`/`params.yaml`. Son message inclut l'empreinte du gold et la metrique cle (ex. `data+model 637be8d38250 | PR-AUC 0.1036`), genere par `scripts/demo_versioning.py`.

2. **Quelle empreinte identifie le Gold utilise ?**
   Le hash md5 (12 premiers caracteres) de `data/gold/gold_dataset.csv`, calcule par `md5()` dans `demo_versioning.py`, stocke dans `model_metadata.json` sous `gold_md5`, et repris dans le nom du run MLflow (`rf-<hash>`).

3. **Comment rejouer un run sans modifier `uv.lock` ?**
   Toujours `uv sync --frozen` (jamais `uv add`) : `--frozen` refuse toute resolution qui devierait du lock. Les extras `dev` et `mlops` sont deja verrouilles, donc `dvc`/`mlflow`/`pre-commit` restent disponibles sans jamais reecrire `uv.lock`.

4. **Comment restaurer code, donnees et modele ensemble ?**
   `git checkout <commit ou tag>` restaure le code et les pointeurs `.dvc`, puis `dvc checkout` recupere les fichiers reels depuis le remote. Le run MLflow portant le meme `gold_md5` redonne le contexte d'entrainement complet (parametres, metriques, modele enregistre au registre).
