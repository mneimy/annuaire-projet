"""
Contien les fonctions d'analyse des données de l'annuaire de l'éducation nationale

"""
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field

import pandas as pd
from pydantic import ValidationError

from .config import CHAMPS
from .lecture import Lecteur
from .model import Etablissement


@dataclass
class Rejets:
    """Combien d'enregistrements ont ete ecartes, et pourquoi.

    Un pipeline qui jette des lignes en silence est un pipeline qui ment. On compte.
    """

    total: int = 0
    par_motif: Counter[str] = field(default_factory=Counter)

    def noter(self, erreur: ValidationError) -> None:
        self.total += 1
        for detail in erreur.errors():
            self.par_motif[str(detail["loc"][0])] += 1




def valider(lecteur: Lecteur, rejets: Rejets | None = None) -> Iterator[Etablissement]:
    """Transforme les enregistrements bruts en entites validees, en ecartant les invalides."""
    for brut in lecteur.lire():
        try:
            yield Etablissement.model_validate(
                {cible: brut.get(source) for cible, source in CHAMPS.items()}
            )
        except ValidationError as erreur:
            if rejets is not None:
                rejets.noter(erreur)

def ouverts_par_departement(lecteur: Lecteur) -> Counter[str]:
    """
    Compte les établissements ouverts par département, quelle que soit la source.
    """
    return Counter(e.departement for e in valider(lecteur) if e.est_ouvert)




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


def repartition_public_prive(df: pd.DataFrame) -> tuple[int, int, int]:
    """Comptes Public, Privé, et statut non renseigné."""
    statut = df["statut_public_prive"].fillna("")
    public = int(statut.eq("Public").sum())
    prive = int(statut.eq("Privé").sum())
    return public, prive, int(len(df) - public - prive)


def part_public(df: pd.DataFrame) -> float:
    """Part du public parmi les établissements dont le statut est renseigné."""
    public, prive, _autre = repartition_public_prive(df)
    total = public + prive
    if total == 0:
        return 0.0
    return public / total * 100


def total_etablissements_ouverts(df: pd.DataFrame) -> int:
    """Nombre d'établissements à l'état OUVERT."""
    return int(df["etat"].eq("OUVERT").sum())


def classement_ouverts_par_departement(df: pd.DataFrame) -> pd.Series:
    """Établissements ouverts par département, du plus nombreux au moins nombreux."""
    ouverts = df.loc[df["etat"].eq("OUVERT"), "libelle_departement"].fillna("").str.strip()
    ouverts = ouverts.replace("", "Non renseigné")
    return ouverts.value_counts()


def contrats_prives(df: pd.DataFrame) -> pd.Series:
    """Types de contrat des établissements privés, hors valeur vide ou « SANS OBJET »."""
    contrats = df.loc[df["statut_public_prive"].eq("Privé"), "type_contrat_prive"]
    contrats = contrats.fillna("").str.strip()
    contrats = contrats[~contrats.str.upper().isin({"", "SANS OBJET"})]
    return contrats.value_counts()


def contrat_prive_le_plus_utilise(df: pd.DataFrame) -> tuple[str, int]:
    """Libellé et effectif du type de contrat privé le plus fréquent."""
    comptes = contrats_prives(df)
    if comptes.empty:
        return "Aucun", 0
    return str(comptes.index[0]), int(comptes.iloc[0])


def etablissements_par_ministere(df: pd.DataFrame) -> pd.Series:
    """Effectif par ministère de tutelle."""
    ministeres = df["ministere_tutelle"].fillna("").str.strip().replace("", "Non renseigné")
    return ministeres.value_counts()


def etablissements_par_type(df: pd.DataFrame) -> pd.Series:
    """Effectif des établissements ouverts par type."""
    types = df.loc[df["etat"].eq("OUVERT"), "type_etablissement"].fillna("").str.strip()
    return types.replace("", "Non renseigné").value_counts()


# --- Indicateurs du tableau de bord -------------------------------------------------------

NON_RENSEIGNE = "Non renseigné"
CONTRATS_HORS = {"HORS CONTRAT"}
CONTRATS_IGNORES = {"", "SANS OBJET", "INCONNU DU GESTIONNAIRE"}


def _nettoyer(serie: pd.Series) -> pd.Series:
    """Libellés sans espaces parasites, valeur vide remplacée par « Non renseigné »."""
    return serie.fillna("").str.strip().replace("", NON_RENSEIGNE)


def education_prioritaire(df: pd.DataFrame) -> tuple[int, int, float]:
    """Effectifs REP, REP+, et part de l'éducation prioritaire dans l'ensemble."""
    reseau = df["appartenance_education_prioritaire"].fillna("").str.strip()
    rep = int(reseau.eq("REP").sum())
    rep_plus = int(reseau.eq("REP+").sum())
    part = (rep + rep_plus) / len(df) * 100 if len(df) else 0.0
    return rep, rep_plus, part


def libelle_contrat(contrat: str) -> str:
    """Libellé lisible d'un type de contrat (corrige le « C0NTRAT » de la source)."""
    texte = contrat.strip().upper().replace("C0NTRAT", "CONTRAT").replace("TTES", "TOUTES")
    return texte.capitalize()


def contrats_prives_lisibles(df: pd.DataFrame) -> pd.Series:
    """Effectif des établissements privés par type de contrat, libellés lisibles."""
    comptes = contrats_prives(df)
    comptes = comptes[~comptes.index.str.upper().isin(CONTRATS_IGNORES)]
    comptes.index = comptes.index.map(libelle_contrat)
    return comptes.groupby(level=0).sum().sort_values(ascending=False)


def prive_sous_contrat(df: pd.DataFrame) -> tuple[int, int, float]:
    """Privés sous contrat, privés hors contrat, et part sous contrat (statut connu)."""
    comptes = contrats_prives(df)
    comptes = comptes[~comptes.index.str.upper().isin(CONTRATS_IGNORES)]
    hors = int(comptes[comptes.index.str.upper().isin(CONTRATS_HORS)].sum())
    sous = int(comptes.sum()) - hors
    total = sous + hors
    return sous, hors, (sous / total * 100 if total else 0.0)


def taux_service(df: pd.DataFrame, colonne: str) -> tuple[float | None, int]:
    """Part des établissements qui offrent un service (colonne 0/1), parmi les renseignés."""
    valeurs = pd.to_numeric(df[colonne], errors="coerce").dropna()
    if valeurs.empty:
        return None, 0
    return float(valeurs.eq(1).mean() * 100), int(valeurs.eq(1).sum())


def dates_ouverture(df: pd.DataFrame) -> pd.Series:
    """Dates d'ouverture valides."""
    return pd.to_datetime(df["date_ouverture"], errors="coerce").dropna()


def ouvertures_recentes(df: pd.DataFrame, reference: pd.Timestamp) -> tuple[int, int]:
    """Ouvertures sur les 12 mois précédant `reference`, et sur les 12 mois d'avant."""
    dates = dates_ouverture(df)
    un_an = pd.DateOffset(years=1)
    recentes = dates.between(reference - un_an, reference, inclusive="right")
    precedentes = dates.between(reference - 2 * un_an, reference - un_an, inclusive="right")
    return int(recentes.sum()), int(precedentes.sum())


def ouvertures_par_annee(df: pd.DataFrame, depuis: int) -> pd.Series:
    """Nombre d'ouvertures (toujours ouvertes aujourd'hui) par année, depuis `depuis`."""
    annees = dates_ouverture(df).dt.year
    annees = annees[annees >= depuis]
    return annees.value_counts().sort_index().astype(int)


def repartition_par_statut(df: pd.DataFrame, colonne: str) -> pd.DataFrame:
    """Effectifs par modalité de `colonne`, ventilés Public / Privé / Non renseigné.

    Une ligne par modalité, triée du plus grand total au plus petit, colonnes
    « Public », « Privé », « Non renseigné », « Total ».
    """
    statut = df["statut_public_prive"].fillna("").str.strip().replace("", NON_RENSEIGNE)
    tableau = pd.crosstab(_nettoyer(df[colonne]), statut)
    for secteur in ("Public", "Privé", NON_RENSEIGNE):
        if secteur not in tableau.columns:
            tableau[secteur] = 0
    tableau = tableau[["Public", "Privé", NON_RENSEIGNE]]
    tableau["Total"] = tableau.sum(axis=1)
    tableau.index.name = colonne
    return tableau.sort_values("Total", ascending=False)
