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





