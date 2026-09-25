"""
Contien les fonctions d'analyse des données de l'annuaire de l'éducation nationale

"""
from collections import Counter
import pandas as pd


def etablissements_par_departement(df: pd.DataFrame) -> dict[str, int]:
    """
    Analyse des établissements par département et retourne 
    le dictionnaire des départements avec le nombre d'établissements 
    trié par nombre d'établissements décroissant
    """
    results: dict[str, int] = {}

    for i in range(len(df)):
        dep = df.iloc[i]["libelle_departement"]
        if dep in results:
            results[dep] = results[dep] + 1
        else:
            results[dep] = 1
    tries = sorted(results.items(), key=lambda item: item[1], reverse=True)
    return dict(tries)    


def pourcentage_etablissements_publics_privés(df: pd.DataFrame) -> str:
    """
    Analyse des établissements publics et privés,
    retourne le pourcentage d'établissements publics.
    """
    public = 0
    privé = 0
    for i in range(len(df)):
        if df.iloc[i]["statut_public_prive"] == "Public":
            public = public + 1
        else:
            privé = privé + 1
        prc_public = public / (public + privé) * 100

    return f"Pourcentage d'établissements publics: {prc_public}%"

def etab_ouvert_par_annee(df: pd.DataFrame) -> dict:
    """
    Analyse des établissements ouverts par année,
    retourne le dictionnaire des années avec le nombre d'établissements ouverts.
    """
    df["annee"] = df["date_ouverture"].str[0:4]
    return df.groupby("annee").size().tail(20)



