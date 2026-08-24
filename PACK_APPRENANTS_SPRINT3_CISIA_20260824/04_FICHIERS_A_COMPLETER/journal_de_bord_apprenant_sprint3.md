# Journal de bord — Sprint 3 CISIA · InduSense 4.0

> **Pourquoi ce document ?** Le **journal de bord** est un **livrable certifiant** : c'est lui qui prouve, module après module, **ce que tu as fait, avec quelle preuve, pour quelle compétence**. Bien tenu, il devient ton **antisèche de soutenance** (l'oral porte sur **C1→C9**, tout le projet).
> **Le rituel, à la fin de CHAQUE module.** Remplis l'entrée du module : *date · ce que j'ai fait · ma preuve · compétence(s) visée(s) · une difficulté ou question*. Une preuve = une **capture**, une **commande qui répond**, un **résultat chiffré** ou un **fichier produit**. Range tes captures dans un dossier `preuves/` numéroté.
> **Format conseillé.** Un Notebook (ou ce document) que tu complètes en direct. À l'oral, tu raconteras chaque preuve avec la structure **contexte → problème → choix → preuve → limite**.
> **Calendrier 2026.** J1 24/08 · J2 25/08 · J3 26/08 · J4 01/09 · J5 02/09 · J6 03/09. Le formateur annonce le rythme et les transitions selon l'avancement réel du groupe.

---

## Comment remplir une entrée

Pour chaque module, complète les 5 champs. Exemple (module 24) :

| Champ | Exemple rempli |
|---|---|
| **Date** | mar. 25/08 — après-midi |
| **Ce que j'ai fait** | Activé pre-commit (ruff/black/gitleaks) + ajouté un job `build` en CI ; versionné le gold avec DVC |
| **Ma preuve** | capture `preuves/24_ci_verte.png` (pipeline vert) + sortie `gitleaks: leaks found: 1` (commit bloqué) |
| **Compétence(s)** | C6 (implémenter / intégrer les briques) |
| **Difficulté / question** | `dvc add` refusait le fichier déjà suivi par git → réflexe `git rm --cached` |

---

## Mes entrées (à compléter)

### J1 — lun. 24/08

**Module 23 — Refactoring & structure projet** · *C6*
- Ce que j'ai fait : …
- Ma preuve : … (ex. `uv run pytest -q` vert · capture)
- Compétence(s) : C6 (· lien C3 : features sans fuite)
- Difficulté / question : …

**Module 24 — CI/CD, tests & versioning** · *C6*
- Ce que j'ai fait : …
- Ma preuve : … (CI verte · `gitleaks` bloque · `dvc status`)
- Compétence(s) : C6
- Difficulté / question : …

### J2 — mar. 25/08

**Module 25 — API REST (FastAPI)** · *C7*
- Ce que j'ai fait : …
- Ma preuve : … (`/health` 200 · `/predict-tabular` 200 · `/docs`)
- Compétence(s) : C7 (architecture / intégration) · C6
- Difficulté / question : …

**Module 26 — Sécurité & menaces** · *C2*
- Ce que j'ai fait : …
- Ma preuve : … (401 sans clé · 429 rate limit · 413 payload)
- Compétence(s) : C2 (risques) · C6
- Difficulté / question : …

### J3 — mer. 26/08

**Module 27 — Conteneurisation (Docker)** · *C6*
- Ce que j'ai fait : … / Ma preuve : … (`docker build` · image non-root) / Compétence(s) : C6 / Difficulté : …

**Module 28 — Déploiement local & compose** · *C6 · C7*
- Ce que j'ai fait : … / Ma preuve : … (`docker compose up -d --wait` · api + db *healthy* · 3 smoke tests verts) / Compétence(s) : C6, C7 / Difficulté : …

### J4 — mar. 01/09

*(Matin : M29 puis M30. Après-midi : M31-M32 en **passe 1 sur `tp_payguard`**.)*

**Module 29 — Orchestration Prefect (design)** · *C6 · C7*
- Ce que j'ai fait : … / Ma preuve : … (design du flow `ingest→feature→predict→store` + flow « hello ») / Compétence(s) : C6, C7 / Difficulté : …

**Module 30 — Implémentation du flow** · *C6*
- Ce que j'ai fait : … / Ma preuve : … (2 runs → 0 doublon, `count(*)` stable) / Compétence(s) : C6 / Difficulté : …

### J5 — mer. 02/09

*(Matin : M31-M32, **passe 2 InduSense dans le miroir officiel `tp_drift_indusense`**. Après-midi : M33 puis M34 et clôture du bloc technique.)*

**Module 31 — Data drift & métriques** · *C3 · C8* · travail réparti entre J4 après-midi et J5 matin
- Ce que j'ai fait : … / Ma preuve nominale J5 : … (miroir `tp_drift_indusense` : fenêtre 2 +8 °C → PSI température **≈ 6,845** · fenêtre 3 → rappel **≈ 0,053** avec PSI muet · suite **11 passed**) / Extension éventuelle, à étiqueter : … (`docs/TP_drift.md` : 6,834 / 0,092 / 8 tests ; simulation : ≈ 3,32) / Compétence(s) : C3, C8 / Difficulté : …

**Module 32 — Drift report + alerting (JSON + SQLite)** · *C3 · C8* · travail réparti entre J4 après-midi et J5 matin
- Ce que j'ai fait : … / Ma preuve : … (`reports\drift_report_f2.json` lisible · une ligne SQLite `drift_events` · saine→0 · +8 °C→1 · relance→0 · **11 passed**, sans Evidently) / Compétence(s) : C3, C8 / Difficulté : …

**Module 33 — Observabilité API (Prometheus)** · *C6 · C8*
- Ce que j'ai fait : … / Ma preuve : … (`/metrics` scrapeable · cible `indusense-api` **UP** au scrape · requête **PromQL p95** de latence + taux 5xx · 5 SLI/SLO) / Compétence(s) : C6, C8 / Difficulté : …

**Module 34 — Dashboards & runbooks (Grafana)** · *C6 · C8*
- Ce que j'ai fait : … / Ma preuve : … (dashboard v1 exporté **JSON** importable ≥ 3 panels · 2 alertes Grafana avec `for:` · **runbook joué** jusqu'à résolution) / Compétence(s) : C6, C8 / Difficulté : …

### J6 — jeu. 03/09 — Journée Game Day « Opération lundi matin »

**Game Day — réparer un dépôt cassé, prouver C8/C9** · *C8 · C9*
- Ce que j'ai fait : … (dépôt `J6-gameday` cloné · pannes triées · réparations menées, ex. n/14 pannes)
- Ma preuve : … (CI de nouveau verte · `docker compose up -d --wait` *healthy* · `/health` + `/ready` 200 · dashboard qui remonte)
- Post-mortem (ce qui a cassé, pourquoi, comment l'éviter) : …
- Pitch (la réparation que j'ai expliquée à mon binôme/au groupe) : …
- Compétence(s) : C8 (mesurer/maintenir), C9 (amélioration continue)
- Difficulté / question : …

---

## Bilan de fin de sprint (à relire avant la soutenance)

- **Mon récit projet** (3 phrases) : du **Gold dataset** (S1) au **modèle** (S2), **industrialisé** et **surveillé** (S3)…
- **Mes 3 plus belles preuves** : 1) … 2) … 3) …
- **Mes 2 limites assumées** (le jury adore) : … / …
- **Ce que je ferais ensuite** (C9) : sur dérive, **ouvrir une investigation documentée** (jamais de réentraînement aveugle) → si les **labels** et les **critères** le justifient, entraîner un **candidat**, comparer **champion/challenger**, passer les **gates de validation**, puis **décider humainement** du déploiement · …

*Journal de bord — Sprint 3 CISIA · InduSense 4.0 · AELION. Tiens-le à jour : c'est ta meilleure préparation à l'oral.*
