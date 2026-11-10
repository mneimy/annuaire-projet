"""Page Annuaire : filtres, tableau et extraction CSV."""

import pandas as pd
import streamlit as st

from annuaire.interface.chargement import COLONNES, afficher_fraicheur, charger_annuaire

LIBELLES = {
    "identifiant_de_l_etablissement": "Identifiant",
    "nom_etablissement": "Établissement",
    "type_etablissement": "Type",
    "statut_public_prive": "Statut",
    "nom_commune": "Commune",
    "libelle_departement": "Département",
    "libelle_region": "Région",
    "type_contrat_prive": "Contrat privé",
    "ministere_tutelle": "Ministère de tutelle",
    "date_maj_ligne": "Mise à jour",
}


def _filtrer(
    donnees: pd.DataFrame,
    departement: str,
    commune: str,
    statut: str,
    nom: str,
) -> pd.DataFrame:
    vue = donnees
    if departement != "Tous":
        vue = vue[vue["libelle_departement"].eq(departement)]
    if commune:
        vue = vue[vue["nom_commune"].str.contains(commune.strip(), case=False, na=False)]
    if statut != "Tous":
        vue = vue[vue["statut_public_prive"].eq(statut)]
    if nom:
        vue = vue[vue["nom_etablissement"].str.contains(nom.strip(), case=False, na=False)]
    return vue


def _effectif(nombre: int) -> str:
    return f"{nombre:,}".replace(",", "\u202f")


def _afficher(vue: pd.DataFrame) -> pd.DataFrame:
    colonnes = [colonne for colonne in COLONNES if colonne in LIBELLES and colonne in vue.columns]
    affichage = vue[colonnes].rename(columns=LIBELLES)
    if "Mise à jour" in affichage.columns:
        affichage["Mise à jour"] = pd.to_datetime(affichage["Mise à jour"], errors="coerce")
    for colonne in ("Contrat privé", "Ministère de tutelle"):
        if colonne in affichage.columns:
            affichage[colonne] = affichage[colonne].str.capitalize()
    return affichage


def page_annuaire() -> None:
    """Recherche dans l'annuaire et extraction CSV."""
    donnees = charger_annuaire()
    gauche, droite = st.columns([3, 1], vertical_alignment="bottom")
    with gauche:
        st.title("Annuaire")
        st.caption("Rechercher un établissement et extraire la sélection en CSV.")
    if donnees is None:
        return
    with droite, st.container(horizontal_alignment="right"):
        afficher_fraicheur(donnees)

    departements = sorted(valeur for valeur in donnees["libelle_departement"].unique() if valeur)
    with st.container(border=True):
        nom = st.text_input(
            "Établissement",
            placeholder="Rechercher par nom (ex. : Jean Jaurès)",
            icon=":material/search:",
        )
        col_departement, col_commune, col_statut = st.columns([2, 2, 1])
        departement = col_departement.selectbox("Département", ["Tous", *departements])
        commune = col_commune.text_input("Commune", placeholder="Nom de la commune")
        statut = col_statut.segmented_control(
            "Secteur", ["Tous", "Public", "Privé"], default="Tous", width="stretch"
        ) or "Tous"

    vue = _filtrer(donnees, departement, commune, statut, nom)
    affichage = _afficher(vue)

    compteur, export = st.columns([3, 1], vertical_alignment="center")
    compteur.markdown(f"**{_effectif(len(affichage))}** établissements trouvés")
    export.download_button(
        "Extraire en CSV",
        data=affichage.to_csv(index=False).encode("utf-8"),
        file_name="annuaire.csv",
        mime="text/csv",
        icon=":material/download:",
        type="primary",
        width="stretch",
        disabled=affichage.empty,
    )
    st.dataframe(
        affichage,
        hide_index=True,
        height=560,
        column_config={
            "Identifiant": st.column_config.TextColumn(width="small"),
            "Établissement": st.column_config.TextColumn(width="large"),
            "Statut": st.column_config.TextColumn(width="small"),
            "Mise à jour": st.column_config.DateColumn(format="DD/MM/YYYY", width="small"),
        },
    )
