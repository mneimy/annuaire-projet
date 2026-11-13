"""Le schema de la base, decrit en Python avec SQLAlchemy Core.

Pourquoi Core et pas l'ORM : un pipeline de donnees deplace des lignes par milliers, il ne
manipule pas des objets metier un par un. Core donne le SQL sans la couche d'objets — et
il donne surtout des requetes PARAMETREES par construction, donc pas d'injection possible.

Le choix de la cle primaire est la decision de la journee. Voir `CLE` plus bas.
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.types import DateTime

metadonnees = MetaData()

# Les colonnes retenues. Le jeu source en compte 71 ; en charger 71 « au cas ou » est le
# meilleur moyen de ne jamais savoir lesquelles sont fiables.
COLONNES = (
    "identifiant",
    "nom",
    "type_etablissement",
    "statut",
    "code_postal",
    "code_commune",
    "nom_commune",
    "code_departement",
    "libelle_departement",
    "code_academie",
    "code_region",
    "latitude",
    "longitude",
    "multi_uai",
    "etat",
    "date_maj_source",
)

# La correspondance source -> base. Elle est explicite, et c'est volontaire : le jour ou
# l'API renomme un champ, le pipeline tombe ici, a un endroit, et pas dans vingt requetes.
DEPUIS_SOURCE = {
    "identifiant": "identifiant_de_l_etablissement",
    "nom": "nom_etablissement",
    "type_etablissement": "type_etablissement",
    "statut": "statut_public_prive",
    "code_postal": "code_postal",
    "code_commune": "code_commune",
    "nom_commune": "nom_commune",
    "code_departement": "code_departement",
    "libelle_departement": "libelle_departement",
    "code_academie": "code_academie",
    "code_region": "code_region",
    "latitude": "latitude",
    "longitude": "longitude",
    "multi_uai": "multi_uai",
    "etat": "etat",
    "date_maj_source": "date_maj_ligne",
}

# La cle primaire. Elle n'est PAS evidente : `identifiant_de_l_etablissement` n'est pas
# unique dans la source (78 identifiants portent plusieurs lignes). Le choix fait ici est
# assume et trace : un identifiant = un etablissement, les antennes sont fusionnees, et le
# chargement journalise exactement combien de lignes ont ete ecrasees.
CLE = ("identifiant",)

etablissement = Table(
    "etablissement",
    metadonnees,
    Column("identifiant", String(8), primary_key=True),
    Column("nom", Text, nullable=False),
    Column("type_etablissement", Text),
    Column("statut", Text),
    Column("code_postal", String(5)),
    Column("code_commune", String(5)),
    Column("nom_commune", Text),
    Column("code_departement", String(3), index=True),
    Column("libelle_departement", Text),
    Column("code_academie", String(2)),
    Column("code_region", String(2)),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("multi_uai", Boolean),
    Column("etat", Text),
    Column("date_maj_source", Date),
    # Les deux colonnes de tracabilite : qui a ecrit cette ligne, et quand. Elles ne
    # viennent pas de la source, elles viennent du pipeline. C'est ce qui permet, trois
    # mois plus tard, de savoir quelle execution a produit quoi.
    Column("charge_le", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("execution", String(32), nullable=False),
)

# Les agregats. Une table, pas une vue : on veut pouvoir la rejouer et la comparer.
agregat_departement = Table(
    "agregat_departement",
    metadonnees,
    Column("code_departement", String(3), primary_key=True),
    Column("libelle_departement", Text),
    Column("etablissements", Integer, nullable=False),
    Column("prives", Integer, nullable=False),
    Column("calcule_le", DateTime(timezone=True), server_default=func.now(), nullable=False),
)
