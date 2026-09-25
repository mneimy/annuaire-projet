"""
contien les fonctions de nettoyage des données de l'annuaire de l'éducation nationale
"""

import pandas as pd
from annuaire.config import columns_to_keep, etat_to_keep


def clean_data(df: pd.DataFrame) -> pd.DataFrame :
    """
    Nettoyage des données de l'annuaire de l'éducation nationale
    """
    df = df[columns_to_keep]
    df = df[df["libelle_departement"].notna()]
    df = df[df["etat"].isin(etat_to_keep)]
    return df