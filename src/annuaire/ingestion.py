"""
Ingestion des données de l'annuaire de l'éducation nationale

""" 

import pandas as pd
import requests
from annuaire.config import LIMIT, MAX_OFFSET, URL_BASE


def get_data(offset: int = 0) :
    """
    Récupère les données de l'annuaire de l'éducation nationale
    """
    while offset < MAX_OFFSET:
        url = f"{URL_BASE}?limit={LIMIT}&offset={offset}"
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data["results"])
        return df   

