"""
Configuration du projet
"""
from pathlib import Path

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

