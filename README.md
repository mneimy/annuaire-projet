# Annuaire de l'éducation

Lecture de l'annuaire des établissements scolaires (CSV, Parquet ou API du ministère), validation des enregistrements, puis deux indicateurs : établissements ouverts par département, et part du public.

Python **3.14**. Les dépendances sont gérées avec [uv](https://docs.astral.sh/uv/).

## Installer

Installer uv, une seule fois :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Sous macOS, `brew install uv` convient aussi. Vérifier avec `uv --version`.

À la racine du projet, créer l'environnement et installer les librairies figées dans `uv.lock` (le groupe `dev` : Ruff et mypy, est inclus) :

```bash
uv sync
```

uv lit `.python-version` (`3.14`), télécharge cet interpréteur s'il manque, crée `.venv/`, puis installe le projet. On ne lance pas `pip install` à la main : `uv run` utilise ce `.venv`.

## Mettre à jour les librairies

Les versions autorisées sont dans `pyproject.toml`. Le fichier `uv.lock` fige la résolution exacte. Une mise à jour se fait en deux temps : recalculer le lock, puis réinstaller.

Tout mettre à jour dans les bornes du `pyproject.toml` :

```bash
uv lock --upgrade
uv sync
```

Une seule librairie :

```bash
uv lock --upgrade-package pandas
uv sync
```

Voir ce qui est installé :

```bash
uv tree
```

## Ajouter ou retirer une librairie

Ajouter (uv écrit `pyproject.toml` et `uv.lock`, puis installe) :

```bash
uv add polars
uv add --dev ruff
```

Retirer :

```bash
uv remove polars
```

`uv add` et `uv remove` synchronisent l'environnement. Inutile de chaîner un `uv sync` derrière.

## Démarrer

`main.py` ajoute `src/` au chemin Python, puis appelle `ingestion.ingestion_donnees`. On le lance **depuis la racine** du projet : le fichier produit est `donnees/etablissements_ingestion.csv`.

```bash
uv run python main.py --help
uv run python main.py --source parquet
uv run python main.py --source api --maj
```

`--source` vaut `csv` (défaut), `parquet` ou `api`.

L'application web se lance aussi depuis la racine. La première page est le tableau de bord, la seconde l'annuaire (filtres, extraction CSV, date de mise à jour) :

```bash
uv run streamlit run app.py
```

| Source | Lecture | À savoir |
|---|---|---|
| `csv` | `donnees/etablissements.csv` (~212 Mo) | Fichier complet, lecture lente. |
| `parquet` | `donnees/etablissements.parquet` | Extrait léger, pratique pour un premier lancement. |
| `api` | API data.education.gouv.fr | Au plus 3 000 enregistrements (`MAX_ENREGISTREMENTS`), réseau requis. |

Le dossier `donnees/` est local : il est ignoré par git (`.gitignore`). Sans ces fichiers, `csv` et `parquet` échouent.

Depuis la racine, seul `--help` est fiable. Un `--source csv` ou `parquet` lancé à la racine cherche `../donnees/` en dehors du projet.

## Carte du projet

```text
main.py                  point d'entrée : ingestion, puis analyse
app.py                   application web Streamlit
comparer.py              quatre façons de compter, chronométrables
donnees/                 CSV et Parquet locaux
src/annuaire/
  config.py              URL, limites, colonnes, chemins, correspondance des champs
  lecture.py             Lecteur CSV, Parquet, API (même contrat)
  model.py               Etablissement validé par Pydantic
  analyse.py             validation, comptes, part du public
  ingestion.py           téléchargement, fichier local, mise à jour
  nettoyage.py           filtre pandas (colonnes, département, état)
  interface/             pages Streamlit (tableau de bord, annuaire)
```

Deux façons de travailler coexistent.

Le chemin utilisé par `main.py` est typé. `ingestion.py` est le seul endroit qui récupère les données. `lecture.py` produit des dictionnaires. `analyse.valider` les transforme en `Etablissement` et compte les rejets. `main.py` ne garde ensuite que les établissements ouverts.

`nettoyage.clean_data` filtre un tableau pandas. `analyse.pourcentage_etablissements_publics_privés` calcule la part du public en parcourant les lignes. Ces deux fonctions ne sont pas branchées sur `main.py`.

## Rôle de chaque script

### `main.py`

Lanceur. Il place `src/` sur `sys.path`, appelle `ingestion_donnees`, puis affiche les indicateurs : nombre d'ouverts, part du public, enregistrements écartés, top 5 des départements. `--maj` force un nouveau téléchargement.

### `src/annuaire/config.py`

Constantes partagées : URL de l'API, `LIMIT`, `MAX_OFFSET`, `MAX_ENREGISTREMENTS`, colonnes gardées, états gardés, chemins CSV et Parquet, dictionnaire `CHAMPS` (nom du modèle → nom de la colonne source).

### `src/annuaire/lecture.py`

Trois lecteurs, un contrat (`Lecteur.lire`). `LecteurCsv` et `LecteurParquet` lisent `donnees/`. `LecteurApi` interroge l'API. Le reste du code ne sait pas d'où viennent les lignes.

### `src/annuaire/model.py`

Modèle `Etablissement` : identifiant, nom, type, statut (`Public` ou `Privé`), code département (complété sur 3 caractères), département, région, état. `est_ouvert` est vrai quand l'état vaut `OUVERT`.

### `src/annuaire/analyse.py`

`valider` transforme chaque ligne brute en `Etablissement` et note les rejets. `ouverts_par_departement` compte les ouverts. `pourcentage_etablissements_publics_privés` travaille sur un DataFrame pandas, pas sur le modèle.

### `src/annuaire/ingestion.py`

`ingestion_donnees` relit `donnees/etablissements_ingestion.csv` s'il existe. Sinon, ou avec `--maj`, il télécharge la source demandée (`csv`, `parquet` ou `api`) et réécrit ce fichier.

### `src/annuaire/nettoyage.py`

`clean_data` ne garde que `columns_to_keep`, enlève les départements vides, et ne conserve que les états listés dans `etat_to_keep` (`OUVERT`).

### `comparer.py`

Même question (ouverts par département), quatre coûts différents : boucle `iloc`, `apply`, pandas vectorisé sur deux colonnes, Polars en lecture paresseuse sur `donnees/zstd.parquet`.

Ce script se lance **depuis la racine** (`Path("./donnees")`), pas depuis `src/` :

```bash
uv run python -c "
from comparer import APPROCHES
import time
for nom, fonction in APPROCHES.items():
    debut = time.perf_counter()
    resultat = fonction()
    print(f'{nom}: {len(resultat)} départements en {time.perf_counter() - debut:.2f} s')
"
```

La variante naïve et `apply` lisent tout le CSV : prévoir du temps.

## S'orienter dans le code

Pour changer un seuil, une colonne ou un chemin : `config.py` seulement.

Pour une nouvelle source (autre fichier, autre API) : une classe avec `lire()` dans `lecture.py`, puis une entrée dans le dictionnaire `SOURCES` de `ingestion.py`. La validation et l'affichage ne bougent pas.

Pour une règle métier (statut, code département, « ouvert ») : `model.py`. Les lignes refusées remontent dans `Rejets`, affichées par `main.py`.

Pour un indicateur : une fonction dans `analyse.py`, appelée depuis `main.py`.

Vérifier le style et les types :

```bash
uv run ruff check .
uv run mypy src
```

Notebook : `uv run jupyter lab`, à lancer depuis la racine pour `comparer.py` et `donnees/`. Pour importer `annuaire`, le noyau doit voir `src/` (`main.py` l'ajoute tout seul ; un notebook, non).
