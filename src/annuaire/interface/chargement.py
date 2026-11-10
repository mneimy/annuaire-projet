"""Lecture du CSV d'ingestion et contrôle de sa fraîcheur."""

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from annuaire.config import Files_path

COLONNES = [
    "identifiant_de_l_etablissement",
    "nom_etablissement",
    "type_etablissement",
    "statut_public_prive",
    "nom_commune",
    "libelle_departement",
    "libelle_region",
    "etat",
    "type_contrat_prive",
    "ministere_tutelle",
    "date_maj_ligne",
]

# Colonnes utiles au seul tableau de bord. Lues si elles existent dans le CSV.
COLONNES_ANALYSE = [
    "appartenance_education_prioritaire",
    "restauration",
    "hebergement",
    "ulis",
    "date_ouverture",
    "latitude",
    "longitude",
]

DELAI_PEREMPTION = timedelta(days=31)
PARIS = ZoneInfo("Europe/Paris")


def racine_projet() -> Path:
    """Racine du dépôt, quel que soit le répertoire de lancement."""
    return Path(__file__).resolve().parents[3]


def chemin_donnees() -> Path:
    """CSV produit par ingestion_donnees, résolu depuis la racine du projet."""
    if Files_path.is_absolute():
        return Files_path
    return racine_projet() / Files_path


def date_mise_a_jour(df: pd.DataFrame, chemin: Path) -> date:
    """Date la plus récente de `date_maj_ligne`, sinon la date du fichier."""
    if "date_maj_ligne" in df.columns:
        dates = pd.to_datetime(df["date_maj_ligne"], errors="coerce")
        if dates.notna().any():
            return dates.max().date()
    return datetime.fromtimestamp(chemin.stat().st_mtime, PARIS).date()


def donnees_perimees(jour: date, aujourd_hui: date | None = None) -> bool:
    """Vrai si la dernière mise à jour a plus d'un mois."""
    aujourd_hui = aujourd_hui or datetime.now(PARIS).date()
    return aujourd_hui - jour > DELAI_PEREMPTION


@st.cache_data(show_spinner="Chargement de l'annuaire…")
def _lire(chemin: str, horodatage: float) -> pd.DataFrame:
    del horodatage
    voulues = set(COLONNES) | set(COLONNES_ANALYSE)
    return pd.read_csv(
        chemin, dtype=str, usecols=lambda nom: nom in voulues, keep_default_na=False
    )


def charger_annuaire() -> pd.DataFrame | None:
    """Charge le CSV local. Affiche une erreur et renvoie None s'il manque."""
    chemin = chemin_donnees()
    if not chemin.exists():
        st.error(
            f"Aucune donnée dans `{chemin.name}`. "
            "Lancez d'abord `uv run python main.py --source api`."
        )
        return None
    return _lire(str(chemin), chemin.stat().st_mtime)


def afficher_fraicheur(df: pd.DataFrame) -> None:
    """Badge de dernière mise à jour, et avertissement si elle a plus d'un mois."""
    jour = date_mise_a_jour(df, chemin_donnees())
    perimees = donnees_perimees(jour)
    st.badge(
        f"Données du {jour:%d/%m/%Y}",
        icon=":material/warning:" if perimees else ":material/check_circle:",
        color="orange" if perimees else "green",
    )
    if perimees:
        st.warning(
            "Ces données ont plus d'un mois. Mettez-les à jour avec "
            "`uv run python main.py --source api --maj`."
        )
