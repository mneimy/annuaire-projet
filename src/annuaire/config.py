"""
Configuration du projet
"""
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Reglages(BaseSettings):
    """Les parametres du chargement. Prefixe `ANNUAIRE_` pour ne rien confondre."""

    model_config = SettingsConfigDict(
        env_prefix="ANNUAIRE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    base_url: PostgresDsn
    source: Path = Path("donnees/brut")
    lot: int = Field(default=2_000, ge=1, le=3_000)
    journal_niveau: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    journal_json: bool = False

    @property
    def url_pour_sqlalchemy(self) -> str:
        """L'URL complete, mot de passe compris.

        Attention : `str(url)` masque le mot de passe par `***` cote SQLAlchemy. Ici c'est
        pydantic qui tient l'URL, et il ne le masque pas — ce qui veut dire qu'il ne faut
        JAMAIS journaliser cette chaine. C'est la raison d'etre de `url_pour_journal`.
        """
        return str(self.base_url)

    @property
    def url_pour_journal(self) -> str:
        """La meme URL, sans le mot de passe. C'est celle-ci qu'on ecrit dans le journal."""
        hote = self.base_url.hosts()[0]
        return f"{self.base_url.scheme}://{hote['username']}@{hote['host']}:{hote['port']}{self.base_url.path}"

URL_BASE = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-annuaire-education/records"

LIMIT = 100
OFFSET = 1000
MAX_OFFSET = 3000
CSV_FILE = Path("donnees/etablissements.csv")
PARQUET_FILE = Path("donnees/etablissements.parquet")
MAX_ENREGISTREMENTS = 70000
DELAI_ATTENTE_S = 30
TRI = "identifiant_de_l_etablissement"
Files_path = Path("donnees/etablissements_ingestion.csv")

etat_to_keep = [
    "OUVERT"
]

columns_to_keep = [
    "identifiant_de_l_etablissement",
    "nom_etablissement",
    "type_etablissement",
    "statut_public_prive",
    "code_postal",
    "nom_commune",
    "code_departement",
    "libelle_departement",
    "libelle_region",
    "etat",
    "date_ouverture",
]

status_to_keep = [
    "Public"
]

CHAMPS = {
    "identifiant": "identifiant_de_l_etablissement",
    "nom": "nom_etablissement",
    "type_etablissement": "type_etablissement",
    "statut": "statut_public_prive",
    "code_departement": "code_departement",
    "departement": "libelle_departement",
    "region": "libelle_region",
    "etat": "etat",
}

