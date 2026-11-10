"""
Modèle de données pour l'annuaire scolaire

Ce modèle est utilisé pour valider les données entrantes.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

CodeDepartement = Annotated[str, Field(min_length=2, max_length=3)]

class Etablissement(BaseModel):
    """
    Un établissement scolaire 
    tel qu'on accepte de le faire entrer dans le système.
    """
    identifiant: str = Field(min_length=1)
    nom: str = Field(min_length=1)
    type_etablissement: str
    statut: Literal["Public", "Privé"]
    code_departement: CodeDepartement
    departement: str = Field(min_length=1)
    region: str
    etat: Literal["OUVERT", "FERME", "À FERMER"]

    @field_validator("code_departement")
    @classmethod
    def sur_trois_caracteres(cls, valeur: str) -> str:
        """
        Valide que le code département est sur 3 caractères
        """
        return valeur.zfill(3)

    @property
    def est_ouvert(self) -> bool:
        """
        Retourne True si l'établissement est ouvert, False sinon
        """
        return self.etat == "OUVERT"

