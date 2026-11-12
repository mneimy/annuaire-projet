"""Habillage commun : feuille de style des cartes, encart « Source des données »."""

import base64
from pathlib import Path

import streamlit as st

STATIC = Path(__file__).resolve().parent / "static"
LOGO_SOURCE = STATIC / "logo_data_gouv.svg"
LOGO_MN_CONSEIL = STATIC / "logo_mn_conseil.png"
ICONE_MN_CONSEIL = STATIC / "logo_mn_conseil_icone.png"

URL_JEU_DE_DONNEES = "https://www.data.gouv.fr/datasets/annuaire-de-leducation"
URL_API = "https://data.education.gouv.fr/explore/dataset/fr-en-annuaire-education/"
URL_LICENCE = "https://www.data.gouv.fr/pages/legal/licences/etalab-2-0"

CSS = """
<style>
/* Cartes d'indicateurs : fond blanc, liseré coloré à gauche, ombre légère. */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E3E8F1 !important;
    border-left: 4px solid var(--carte-accent, #2453A6) !important;
    border-radius: 0.75rem;
    padding: 0.9rem 0.95rem 0.8rem 0.95rem !important;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04), 0 4px 14px rgba(16, 24, 40, 0.05);
    transition: box-shadow 0.15s ease, transform 0.15s ease;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 2px 4px rgba(16, 24, 40, 0.06), 0 10px 24px rgba(16, 24, 40, 0.09);
    transform: translateY(-1px);
}
[data-testid="stMetricLabel"] p {
    font-size: 0.84rem !important;
    font-weight: 600 !important;
    color: #5B6679 !important;
}
[data-testid="stMetricValue"] {
    font-family: "Plus Jakarta Sans", sans-serif;
    font-weight: 800;
    font-size: 2.05rem !important;
    letter-spacing: -0.02em;
    color: #13223F;
}
[data-testid="stMetricDelta"] {
    font-size: 0.8rem;
}

/* Deuxième rangée d'indicateurs (privé et services) : accent orange. */
.st-key-indicateurs_services [data-testid="stMetric"] {
    --carte-accent: #E07A3F;
}

/* Blocs de graphiques : même langage visuel que les cartes. */
/* Le padding vient du conteneur à bordure de Streamlit : ne pas le surcharger,
   sinon les graphiques calculent une largeur fausse et débordent. */
[class*="st-key-bloc_"] {
    background: #FFFFFF;
    border-color: #E3E8F1 !important;
    border-radius: 0.9rem !important;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04), 0 4px 14px rgba(16, 24, 40, 0.04);
}

/* Onglets un peu plus marqués. */
[data-baseweb="tab-list"] button p {
    font-weight: 600;
    font-size: 0.95rem;
}

/* Encart « Source des données » dans la barre latérale. */
.source-donnees {
    background: #FFFFFF;
    border-radius: 0.75rem;
    padding: 0.9rem 0.9rem 0.8rem 0.9rem;
    margin-top: 0.5rem;
    color: #1B2537;
    font-size: 0.78rem;
    line-height: 1.45;
}
.source-donnees .titre {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.68rem;
    font-weight: 700;
    color: #5B6679;
    margin-bottom: 0.55rem;
}
.source-donnees img {
    width: 150px;
    display: block;
    margin-bottom: 0.6rem;
}
.source-donnees a {
    color: #2453A6 !important;
    text-decoration: none;
    font-weight: 600;
}
.source-donnees a:hover { text-decoration: underline; }
.source-donnees .licence {
    color: #5B6679;
    margin-top: 0.4rem;
}

/* Logo MN Conseil en haut de la barre latérale : plus grand que la taille native. */
[data-testid="stSidebarLogo"],
[data-testid="stSidebarHeader"] img {
    height: 2.75rem !important;
    max-width: 100% !important;
}

/* Mention de l'auteur, tout en bas de la barre latérale. */
.mention-auteur {
    margin-top: 0.9rem;
    padding-top: 0.75rem;
    border-top: 1px solid #2A4170;
    color: #9FB0CF;
    font-size: 0.74rem;
    line-height: 1.45;
    text-align: center;
}
.mention-auteur strong { color: #E4EAF5; font-weight: 700; }
</style>
"""


def appliquer_style() -> None:
    """Injecte la feuille de style commune à toutes les pages."""
    st.html(CSS)


def logo_mn_conseil() -> None:
    """Logo MN Conseil en tête de la barre latérale (icône seule quand elle est repliée)."""
    st.logo(str(LOGO_MN_CONSEIL), size="large", icon_image=str(ICONE_MN_CONSEIL))


def _logo_en_data_uri() -> str:
    contenu = base64.b64encode(LOGO_SOURCE.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{contenu}"


def encart_source() -> None:
    """Encart en bas de la barre latérale : d'où viennent les données, sous quelle licence."""
    with st.sidebar:
        st.html(
            f"""
            <div class="source-donnees">
              <div class="titre">Source des données</div>
              <a href="{URL_JEU_DE_DONNEES}" target="_blank" rel="noopener">
                <img src="{_logo_en_data_uri()}" alt="data.gouv.fr">
              </a>
              <div>
                <a href="{URL_JEU_DE_DONNEES}" target="_blank" rel="noopener">Annuaire de l'éducation</a>,
                ministère de l'Éducation nationale, publié sur data.gouv.fr.
                Récupéré via l'<a href="{URL_API}" target="_blank" rel="noopener">API data.education.gouv.fr</a>.
              </div>
              <div class="licence">
                <a href="{URL_LICENCE}" target="_blank" rel="noopener">Licence Ouverte 2.0</a> (Etalab)
              </div>
            </div>
            """
        )


def mention_auteur() -> None:
    """Mention de développement, sous l'encart source."""
    with st.sidebar:
        st.html(
            """
            <div class="mention-auteur">
              Conçu et développé par <strong>MN Conseil</strong><br>
              Projet pédagogique · co-développé avec l'IA
            </div>
            """
        )
