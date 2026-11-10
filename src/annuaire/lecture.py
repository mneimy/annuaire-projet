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

from .config import CSV_FILE, MAX_ENREGISTREMENTS, OFFSET, PARQUET_FILE, TRI, URL_BASE


class Lecteur(Protocol):
    """
    Un lecteur est celui qui sait produire des enregistrements.
    """
    def lire(self) -> Iterator[dict[str, Any]]:
        """
        Produit des enregistrements.
        """

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


    def lire(self) -> Iterator[dict[str, str | int]]:
        """
        Produit des enregistrements.
        """
        parametres: dict[str, int | str] = {
            "limit": MAX_ENREGISTREMENTS,
            "offset": OFFSET,
            "sort": TRI,
        }
        response = requests.get(self.url, params=parametres)
        response.raise_for_status()
        
        yield from response.json()["results"]



