"""Seul point d'entrée pour récupérer les données, ou les mettre à jour."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pandas as pd

from .config import LIMIT, MAX_ENREGISTREMENTS, Files_path
from .lecture import Lecteur, LecteurApi, LecteurCsv, LecteurMemoire, LecteurParquet

SOURCES: dict[str, type[LecteurCsv | LecteurParquet | LecteurApi]] = {
    "csv": LecteurCsv,
    "parquet": LecteurParquet,
    "api": LecteurApi,
}


def save_data(data: Iterator[dict[str, Any]], filename: str | Path) -> None:
    """Sauvegarde les enregistrements dans un fichier CSV."""
    pd.DataFrame(data).to_csv(filename, index=False)


def _lignes_api() -> list[dict[str, Any]]:
    """Télécharge l'annuaire par département, jusqu'à MAX_ENREGISTREMENTS.

    L'API refuse offset + limit > 10 000. Aucun département n'atteint ce plafond.
    """
    lecteur_api = LecteurApi()
    lignes: list[dict[str, Any]] = []
    for code in lecteur_api.codes_departement():
        if len(lignes) >= MAX_ENREGISTREMENTS:
            break
        offset = 0
        filtre = f"code_departement = '{code}'"
        while len(lignes) < MAX_ENREGISTREMENTS:
            page = list(lecteur_api.lire(offset, filtre))
            if not page:
                break
            lignes.extend(page[: MAX_ENREGISTREMENTS - len(lignes)])
            print(f"\r{len(lignes)} enregistrements", end="", flush=True)
            if len(page) < LIMIT:
                break
            offset += LIMIT
    print()
    return lignes


def ingestion_donnees(source: str, mettre_a_jour: bool = False) -> Lecteur:
    """Relit le CSV local s'il existe. Sinon le crée. ``mettre_a_jour`` le retélécharge."""
    if Files_path.exists() and not mettre_a_jour:
        print(f"Données déjà présentes dans {Files_path}")
        return LecteurCsv(Files_path)

    if mettre_a_jour and Files_path.exists():
        print(f"Mise à jour des données ({source})...")
    else:
        print(f"Données absentes, ingestion depuis {source}...")

    if source == "api":
        lignes = _lignes_api()
        save_data(iter(lignes), Files_path)
        lecteur: Lecteur = LecteurMemoire(lignes)
    else:
        source_lecteur = SOURCES[source]()
        save_data(source_lecteur.lire(), Files_path)
        lecteur = LecteurCsv(Files_path)
    print(f"Données sauvegardées dans {Files_path} avec succès")
    return lecteur
