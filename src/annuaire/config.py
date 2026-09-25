"""
Configuration du projet
"""

URL_BASE = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-annuaire-education/records"

LIMIT = 100
OFFSET = 0
MAX_OFFSET = 3000 
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

