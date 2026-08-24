# Drift InduSense — commandes macOS et Linux

Ce fichier est le compagnon exact du
`PAS_A_PAS_apprenant_indusense.md`. Gardez la progression, les objectifs, les
questions et les preuves du pas à pas principal ; remplacez uniquement ses
blocs PowerShell par les blocs ci-dessous.

| Système | Dossier court conseillé | Terminal VS Code |
|---|---|---|
| macOS | `~/CISIA/S3/tp_drift_indusense` | zsh |
| Linux | `~/CISIA/S3/tp_drift_indusense` | bash |

Dans VS Code : **Fichier > Ouvrir le dossier**, choisissez
`tp_drift_indusense`, puis **Terminal > Nouveau terminal**. Toutes les commandes
se lancent depuis le dossier qui contient `pyproject.toml` et `uv.lock`.

## Préflight

```bash
for path in ./pyproject.toml ./uv.lock ./data/reference_normale.csv; do
  if [[ -f "$path" ]]; then
    printf 'OK %s\n' "$path"
  else
    printf 'ABSENT %s\n' "$path" >&2
  fi
done
uv sync --frozen --extra dev
uv run python --version
uv run python -c "import sklearn; print(sklearn.__version__)"
git status --short -- uv.lock 2>/dev/null || true
```

Attendu : trois lignes `OK`, Python 3.13.x, scikit-learn 1.9.0 et aucune
modification de `uv.lock`. Si une ligne indique `ABSENT`, rouvrez le bon dossier
avant de continuer.

## Modèle et seuil

```bash
uv run python ./scripts/train_model.py
cat ./models/threshold.json
```

## Quatre fenêtres

```bash
uv run python ./scripts/drift_lab.py --fenetre 1 --reference normale
uv run python ./scripts/evaluate_fenetre.py --fenetre 1

uv run python ./scripts/drift_lab.py --fenetre 2 --reference normale
uv run python ./scripts/evaluate_fenetre.py --fenetre 2

uv run python ./scripts/drift_lab.py --fenetre 3 --reference normale
uv run python ./scripts/evaluate_fenetre.py --fenetre 3

uv run python ./scripts/drift_lab.py --fenetre janvier --reference normale
uv run python ./scripts/evaluate_fenetre.py --fenetre janvier
```

## Contre-épreuve

```bash
uv run python ./scripts/drift_lab.py --fenetre janvier --reference haute
uv run python ./scripts/drift_lab.py --fenetre 2 --reference normale --machine MACH-03
```

## Rapport et anti-spam

```bash
uv run python ./scripts/alerting_demo.py --report-out ./reports/drift_report_f2.json
cat ./reports/drift_report_f2.json
```

## Tests et contrat

```bash
uv run python -m pytest ./tests/test_alerting_demo.py -q -p no:cacheprovider
uv run python -m pytest ./tests -q -p no:cacheprovider
grep -nE 'drift_events|cooldown_hours|INSERT INTO' ./scripts/alerting_demo.py
```

## Preuves

Les fichiers à déposer sont les mêmes sur les trois systèmes. Dans un chemin à
copier, utilisez `/`, par exemple `reports/drift_report_f2.json`. Vérifiez la
présence des preuves :

```bash
test -f ./reports/drift_report_f2.json && echo 'rapport JSON : OK'
test -f ./models/threshold.json && echo 'seuil : OK'
uv run python -m pytest ./tests -q -p no:cacheprovider
```

## Dépannage macOS/Linux

- `uv: command not found` : fermez et rouvrez le terminal après l'installation
  de `uv`; ne remplacez pas la synchronisation gelée par `pip install`.
- `permission denied` sur un script : lancez-le avec `bash chemin/script.sh` ;
  les scripts Python se lancent toujours avec `uv run python`.
- `$'\r': command not found` : le fichier a reçu des fins de ligne Windows ;
  reprenez la copie officielle au lieu de réécrire le script.
- Dossier sous iCloud, partage réseau ou chemin très long : recopiez le TP vers
  `~/CISIA/S3/tp_drift_indusense`.
- Le dossier n'est pas un dépôt Git : l'absence de sortie de `git status`
  n'empêche pas le TP autonome.

N'utilisez ni `sudo`, ni `uv add`, ni `uv lock` pour « réparer » la séance.
