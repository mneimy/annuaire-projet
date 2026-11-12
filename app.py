"""Application web : tableau de bord, puis annuaire."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st

from annuaire.interface.a_propos import page_a_propos
from annuaire.interface.annuaire_page import page_annuaire
from annuaire.interface.style import (
    appliquer_style,
    encart_source,
    logo_mn_conseil,
    mention_auteur,
)
from annuaire.interface.tableau import page_tableau

FAVICON = (
    Path(__file__).resolve().parent
    / "src"
    / "annuaire"
    / "interface"
    / "static"
    / "favicon.png"
)

st.set_page_config(
    page_title="Annuaire de l'éducation",
    page_icon=str(FAVICON),
    layout="wide",
)
logo_mn_conseil()

navigation = st.navigation(
    [
        st.Page(
            page_tableau,
            title="Tableau de bord",
            icon=":material/dashboard:",
            url_path="",
            default=True,
        ),
        st.Page(
            page_annuaire,
            title="Annuaire",
            icon=":material/menu_book:",
            url_path="annuaire",
        ),
        st.Page(
            page_a_propos,
            title="À propos",
            icon=":material/info:",
            url_path="a-propos",
        ),
    ]
)
appliquer_style()
navigation.run()
# Après la page : l'encart et la mention se placent sous les filtres de la barre latérale.
encart_source()
mention_auteur()
