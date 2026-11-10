"""
Les sources de donnees, et le contrat qu'elles partagent.

Le contrat est un Protocol : aucune classe n'herite de rien. Une source est un lecteur si
elle sait produire des enregistrements, point. C'est le typage structurel — « si ca se
comporte comme un lecteur, c'est un lecteur » — et mypy le verifie statiquement.
"""

import csv
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Protocol

import pyarrow.parquet as pq
import requests

from .config import CSV_FILE, DELAI_ATTENTE_S, LIMIT, PARQUET_FILE, TRI, URL_BASE


class Lecteur(Protocol):
    """
    Un lecteur est celui qui sait produire des enregistrements.
    """
    def lire(self) -> Iterator[dict[str, Any]]:
        """
        Produit des enregistrements.
        """

class LecteurMemoire:
    """Relit des enregistrements déjà en mémoire, sans rappeler la source."""

    def __init__(self, lignes: list[dict[str, Any]]) -> None:
        self.lignes = lignes

    def lire(self) -> Iterator[dict[str, Any]]:
        yield from self.lignes


class LecteurCsv:
    """
    Un lecteur CSV est celui qui sait lire des enregistrements depuis un fichier CSV.
    """
    def __init__(self, chemin: Path = CSV_FILE) -> None:
        self.chemin = chemin

    def lire(self) -> Iterator[dict[str, Any]]:
        """
        Produit des enregistrements.
        """
        with self.chemin.open(encoding="utf-8") as fichier:
            for ligne in csv.DictReader(fichier):
                yield {cle: (valeur if valeur != "" else None) for cle, valeur in ligne.items()}


class LecteurParquet:
    """
    Un lecteur Parquet est celui qui sait lire des enregistrements depuis un fichier Parquet.
    """
    def __init__(self, chemin: Path = PARQUET_FILE) -> None:
        self.chemin = chemin

    def lire(self) -> Iterator[dict[str, Any]]:
        """
        Produit des enregistrements.
        """
        yield from pq.read_table(self.chemin).to_pylist()


class LecteurApi:
    """
    Un lecteur API est celui qui sait lire des enregistrements depuis une API.
    """
    def __init__(self, url: str = URL_BASE) -> None:
        self.url = url


    def lire(self, offset: int = 0, filtre: str | None = None) -> Iterator[dict[str, Any]]:
        """Produit une page d'enregistrements, à partir de ``offset``."""
        parametres: dict[str, int | str] = {
            "limit": LIMIT,
            "offset": offset,
            "order_by": TRI,
        }
        if filtre is not None:
            parametres["where"] = filtre
        response = requests.get(self.url, params=parametres, timeout=DELAI_ATTENTE_S)
        response.raise_for_status()
        yield from response.json()["results"]

    def codes_departement(self) -> list[str]:
        """Liste les codes département présents dans l'annuaire."""
        codes: list[str] = []
        offset = 0
        while True:
            parametres: dict[str, int | str] = {
                "select": "code_departement",
                "group_by": "code_departement",
                "order_by": "code_departement",
                "limit": LIMIT,
                "offset": offset,
            }
            response = requests.get(self.url, params=parametres, timeout=DELAI_ATTENTE_S)
            response.raise_for_status()
            page = response.json()["results"]
            if not page:
                break
            codes.extend(
                code for ligne in page if (code := ligne.get("code_departement"))
            )
            if len(page) < LIMIT:
                break
            offset += LIMIT
        return codes



