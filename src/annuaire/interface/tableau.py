"""Page Tableau de bord."""

import math

import pandas as pd
import pydeck as pdk
import streamlit as st

from annuaire import analyse
from annuaire.interface import graphiques as g
from annuaire.interface.chargement import afficher_fraicheur, charger_annuaire

TOUTES = "Toute la France"
TOUS = "Tous les types"

# Cadre de la carte quand aucune région n'est choisie : la métropole seule,
# sinon les DROM étirent la vue sur le globe entier.
METROPOLE = {"lat": (41.0, 51.5), "lon": (-5.5, 10.0)}


def _perimetre(donnees: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    """Filtres de la barre latérale. Renvoie la vue filtrée, la région et le type."""
    with st.sidebar:
        st.subheader("Périmètre")
        regions = sorted(
            valeur for valeur in donnees["libelle_region"].unique() if valeur
        )
        region = st.selectbox("Région", [TOUTES, *regions], key="tdb_region")
        types = sorted(
            valeur for valeur in donnees["type_etablissement"].unique() if valeur
        )
        type_etab = st.selectbox("Type d'établissement", [TOUS, *types], key="tdb_type")
    vue = donnees
    if region != TOUTES:
        vue = vue[vue["libelle_region"].eq(region)]
    if type_etab != TOUS:
        vue = vue[vue["type_etablissement"].eq(type_etab)]
    return vue, region, type_etab


def _entete(donnees: pd.DataFrame, region: str, type_etab: str) -> None:
    gauche, droite = st.columns([3, 1], vertical_alignment="bottom")
    with gauche:
        st.title("Tableau de bord")
        perimetre = region if region != TOUTES else "France entière"
        if type_etab != TOUS:
            perimetre += f" · {type_etab}"
        st.caption(f"Annuaire de l'éducation — établissements ouverts · {perimetre}")
    with droite, st.container(horizontal_alignment="right"):
        afficher_fraicheur(donnees)


def _indicateurs(vue: pd.DataFrame, reference: pd.Timestamp) -> None:
    public, prive, _autre = analyse.repartition_public_prive(vue)
    rep, rep_plus, part_rep = analyse.education_prioritaire(vue)
    sous, hors, part_sous = analyse.prive_sous_contrat(vue)
    recentes, precedentes = analyse.ouvertures_recentes(vue, reference)
    historique = analyse.ouvertures_par_annee(vue, depuis=reference.year - 10)
    types = vue["type_etablissement"].value_counts()

    ligne_1 = st.columns(4)
    ligne_1[0].metric(
        "Établissements ouverts",
        g.effectif(len(vue)),
        icon=":material/school:",
        delta=f"dont {g.effectif(int(types.get('Ecole', 0)))} écoles",
        delta_color="off",
        delta_arrow="off",
        help=" · ".join(
            f"{g.effectif(int(nombre))} {libelle}" for libelle, nombre in types.items()
        ),
        border=True,
        height="stretch",
    )
    ligne_1[1].metric(
        "Secteur public",
        g.pourcentage(analyse.part_public(vue)) if public + prive else "—",
        icon=":material/account_balance:",
        delta=f"{g.effectif(public)} publics · {g.effectif(prive)} privés",
        delta_color="off",
        delta_arrow="off",
        help="Part du public parmi les établissements dont le statut est renseigné.",
        border=True,
        height="stretch",
    )
    ligne_1[2].metric(
        "Éducation prioritaire",
        g.pourcentage(part_rep),
        icon=":material/diversity_3:",
        delta=f"{g.effectif(rep)} REP · {g.effectif(rep_plus)} REP+",
        delta_color="off",
        delta_arrow="off",
        help="Part des établissements rattachés à un réseau REP ou REP+.",
        border=True,
        height="stretch",
    )
    ligne_1[3].metric(
        "Ouvertures sur 12 mois",
        g.effectif(recentes),
        icon=":material/trending_up:",
        delta=recentes - precedentes,
        delta_color="off",
        delta_description="vs 12 mois précédents",
        chart_data=historique.tolist() or None,
        chart_type="bar",
        help=f"Établissements ouverts depuis le {reference - pd.DateOffset(years=1):%d/%m/%Y} "
        "et toujours en activité. La courbe montre les ouvertures des dix dernières années.",
        border=True,
        height="stretch",
    )

    ligne_2 = st.container(key="indicateurs_services").columns(4)
    ligne_2[0].metric(
        "Privé sous contrat",
        g.pourcentage(part_sous) if sous + hors else "—",
        icon=":material/handshake:",
        delta=f"{g.effectif(hors)} hors contrat",
        delta_color="off",
        delta_arrow="off",
        help="Part des établissements privés liés à l'État par un contrat "
        "(association ou simple), parmi ceux dont le contrat est connu.",
        border=True,
        height="stretch",
    )
    services = [
        (
            "restauration",
            "Restauration scolaire",
            ":material/restaurant:",
            "Établissements proposant une cantine.",
        ),
        (
            "hebergement",
            "Internat",
            ":material/bed:",
            "Établissements proposant un hébergement.",
        ),
        (
            "ulis",
            "Dispositif ULIS",
            ":material/accessible:",
            "Unités localisées pour l'inclusion scolaire.",
        ),
    ]
    for colonne, (champ, libelle, icone, aide) in zip(
        ligne_2[1:], services, strict=True
    ):
        if champ not in vue.columns:
            colonne.metric(libelle, "—", icon=icone, border=True)
            continue
        taux, nombre = analyse.taux_service(vue, champ)
        colonne.metric(
            libelle,
            g.pourcentage(taux) if taux is not None else "—",
            icon=icone,
            delta=f"{g.effectif(nombre)} établissements",
            delta_color="off",
            delta_arrow="off",
            help=f"{aide} Calculé sur les établissements où l'information est renseignée.",
            border=True,
            height="stretch",
        )


COULEURS_CARTE = {
    "Public": [36, 83, 166, 150],
    "Privé": [224, 122, 63, 200],
}
GRIS_CARTE = [163, 174, 194, 150]


@st.cache_data(show_spinner=False)
def _points(vue: pd.DataFrame, metropole: bool) -> pd.DataFrame:
    points = pd.DataFrame(
        {
            "lat": pd.to_numeric(vue["latitude"], errors="coerce"),
            "lon": pd.to_numeric(vue["longitude"], errors="coerce"),
            "nom": vue["nom_etablissement"],
            "commune": vue["nom_commune"],
            "statut": vue["statut_public_prive"].replace("", "Non renseigné"),
        }
    ).dropna(subset=["lat", "lon"])
    if metropole:
        points = points[
            points["lat"].between(*METROPOLE["lat"])
            & points["lon"].between(*METROPOLE["lon"])
        ]
    points["couleur"] = points["statut"].map(
        lambda statut: COULEURS_CARTE.get(statut, GRIS_CARTE)
    )
    # Le dernier point dessiné recouvre les autres : le privé, minoritaire, passe dessus.
    return points.sort_values("statut", key=lambda c: c.eq("Privé"))


LARGEUR_CARTE, HAUTEUR_CARTE = 600, 440  # pixels (largeur approximative de la colonne)


def _zoom(ecart_lon: float, ecart_lat: float, latitude: float) -> float:
    """Zoom deck.gl qui fait tenir l'étendue dans la carte.

    Au zoom z, le monde mesure 512 × 2^z pixels pour 360° de longitude ;
    en Mercator, un degré de latitude est étiré de 1 / cos(latitude).
    """
    ecart_lon = max(ecart_lon, 0.02)
    ecart_lat = max(ecart_lat / math.cos(math.radians(latitude)), 0.02)
    zoom_lon = math.log2(LARGEUR_CARTE * 360 / (512 * ecart_lon))
    zoom_lat = math.log2(HAUTEUR_CARTE * 360 / (512 * ecart_lat))
    return float(min(max(min(zoom_lon, zoom_lat) - 0.15, 3), 11))


def _carte(vue: pd.DataFrame, region: str) -> None:
    if not {"latitude", "longitude"} <= set(vue.columns):
        st.info("Coordonnées absentes du fichier : carte indisponible.")
        return
    metropole = region == TOUTES
    points = _points(vue, metropole)
    if points.empty:
        st.info("Aucun établissement géolocalisé dans ce périmètre.")
        return
    couche = pdk.Layer(
        "ScatterplotLayer",
        data=points,
        get_position=["lon", "lat"],
        get_fill_color="couleur",
        get_radius=60,
        radius_min_pixels=1.2,
        radius_max_pixels=6,
        pickable=True,
    )
    # Cadrage sur l'étendue des points (1er-99e centile, pour ignorer les coordonnées aberrantes).
    lat_min, lat_max = points["lat"].quantile([0.01, 0.99])
    lon_min, lon_max = points["lon"].quantile([0.01, 0.99])
    latitude = float((lat_min + lat_max) / 2)
    vue_initiale = pdk.ViewState(
        latitude=latitude,
        longitude=float((lon_min + lon_max) / 2),
        zoom=_zoom(lon_max - lon_min, lat_max - lat_min, latitude),
    )
    st.pydeck_chart(
        pdk.Deck(
            layers=[couche],
            initial_view_state=vue_initiale,
            map_provider="carto",
            map_style="light",
            tooltip={"text": "{nom}\n{commune} · {statut}"},
        ),
        height=HAUTEUR_CARTE,
    )
    st.caption(
        "Chaque point est un établissement. Bleu : public · orange : privé."
        + (
            " Métropole uniquement ; choisissez une région pour l'outre-mer."
            if metropole
            else ""
        )
    )


def _territoires(vue: pd.DataFrame, region: str) -> None:
    carte, classement = st.columns([1.15, 1], gap="large")
    with carte, st.container(border=True, key="bloc_carte", height="stretch"):
        st.subheader("Implantation")
        _carte(vue, region)
    with (
        classement,
        st.container(border=True, key="bloc_departements", height="stretch"),
    ):
        departements = analyse.repartition_par_statut(vue, "libelle_departement")
        if region == TOUTES:
            st.subheader("Départements les mieux dotés")
            departements = departements.head(15)
        else:
            st.subheader("Départements")
        st.altair_chart(g.barres_par_secteur(departements, "Département"))

    if region == TOUTES:
        with st.container(border=True, key="bloc_regions"):
            st.subheader("Régions")
            regions = analyse.repartition_par_statut(vue, "libelle_region")
            st.altair_chart(g.barres_par_secteur(regions, "Région"))


def _structure(vue: pd.DataFrame, reference: pd.Timestamp) -> None:
    types, ouvertures = st.columns(2, gap="large")
    with types, st.container(border=True, key="bloc_types", height="stretch"):
        st.subheader("Par type d'établissement")
        st.altair_chart(
            g.barres_par_secteur(
                analyse.repartition_par_statut(vue, "type_etablissement"), "Type"
            )
        )
    with ouvertures, st.container(border=True, key="bloc_ouvertures", height="stretch"):
        st.subheader("Ouvertures par année")
        st.caption(
            "Établissements toujours ouverts aujourd'hui, selon leur année d'ouverture "
            f"({reference.year} : année en cours)."
        )
        st.altair_chart(
            g.colonnes_annuelles(analyse.ouvertures_par_annee(vue, reference.year - 20))
        )

    with st.container(border=True, key="bloc_ministeres"):
        st.subheader("Ministère de tutelle")
        ministeres = analyse.etablissements_par_ministere(vue).rename("Établissements")
        tableau = ministeres.rename_axis("Ministère").reset_index()
        tableau["Ministère"] = tableau["Ministère"].str.capitalize()
        tableau["Part"] = (
            tableau["Établissements"] / tableau["Établissements"].sum() * 100
        )
        st.dataframe(
            tableau,
            hide_index=True,
            column_config={
                "Établissements": st.column_config.NumberColumn(format="localized"),
                "Part": st.column_config.ProgressColumn(
                    format="%.1f %%", min_value=0, max_value=100
                ),
            },
        )


def _prive(vue: pd.DataFrame, region: str) -> None:
    contrats_col, parts_col = st.columns(2, gap="large")
    with contrats_col, st.container(border=True, key="bloc_contrats", height="stretch"):
        st.subheader("Types de contrat")
        contrats = analyse.contrats_prives_lisibles(vue)
        if contrats.empty:
            st.info("Aucun établissement privé dans ce périmètre.")
        else:
            st.altair_chart(g.barres(contrats, "Contrat", couleur=g.PRIVE))
    with parts_col, st.container(border=True, key="bloc_parts", height="stretch"):
        niveau, libelle = (
            ("libelle_region", "Région")
            if region == TOUTES
            else ("libelle_departement", "Département")
        )
        st.subheader(f"Part du privé par {libelle.lower()}")
        repartition = analyse.repartition_par_statut(vue, niveau)
        connus = repartition["Public"] + repartition["Privé"]
        part = (repartition["Privé"] / connus * 100).where(connus > 0).dropna()
        part = part.sort_values(ascending=False).head(15).round(1)
        st.altair_chart(g.barres(part, libelle, couleur=g.PRIVE, format_valeur=".1f"))
        st.caption("En % des établissements dont le statut est renseigné.")


def page_tableau() -> None:
    """Indicateurs de l'annuaire."""
    donnees = charger_annuaire()
    if donnees is None:
        st.title("Tableau de bord")
        return

    vue, region, type_etab = _perimetre(donnees)
    _entete(donnees, region, type_etab)
    if vue.empty:
        st.info("Aucun établissement dans ce périmètre.")
        return

    reference = pd.Timestamp(
        pd.to_datetime(donnees["date_maj_ligne"], errors="coerce").max()
    )
    if pd.isna(reference):
        reference = pd.Timestamp.now().normalize()

    _indicateurs(vue, reference)
    st.space("small")

    territoires, structure, prive = st.tabs(
        [
            ":material/map: Territoires",
            ":material/category: Structure",
            ":material/handshake: Secteur privé",
        ]
    )
    with territoires:
        _territoires(vue, region)
    with structure:
        _structure(vue, reference)
    with prive:
        _prive(vue, region)
