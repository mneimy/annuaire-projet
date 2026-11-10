"""Graphiques Altair partagés par les pages, et mise en forme des nombres."""

import altair as alt
import pandas as pd

PUBLIC = "#2453A6"
PRIVE = "#E07A3F"
NON_RENSEIGNE = "#A3AEC2"
SECTEURS = ["Public", "Privé", "Non renseigné"]
COULEURS_SECTEURS = alt.Scale(domain=SECTEURS, range=[PUBLIC, PRIVE, NON_RENSEIGNE])

HAUTEUR_BARRE = 26


def effectif(nombre: int) -> str:
    """68558 -> « 68 558 » (espace fine insécable)."""
    return f"{nombre:,}".replace(",", " ")


def pourcentage(valeur: float, decimales: int = 1) -> str:
    """80.73 -> « 80,7 % »."""
    return f"{valeur:.{decimales}f}".replace(".", ",") + " %"


def barres(
    serie: pd.Series, libelle: str, couleur: str = PUBLIC, format_valeur: str = "d"
) -> alt.Chart:
    """Barres horizontales triées, valeur écrite au bout de chaque barre."""
    donnees = serie.rename("Effectif").rename_axis(libelle).reset_index()
    base = alt.Chart(donnees).encode(
        y=alt.Y(
            f"{libelle}:N",
            sort="-x",
            title=None,
            axis=alt.Axis(labelLimit=260, labelFontSize=12, ticks=False, domain=False),
            scale=alt.Scale(paddingInner=0.3),
        ),
        x=alt.X("Effectif:Q", title=None, axis=None),
        tooltip=[alt.Tooltip(f"{libelle}:N"), alt.Tooltip("Effectif:Q", format=format_valeur)],
    )
    graphique = base.mark_bar(color=couleur, cornerRadiusEnd=4)
    valeurs = base.mark_text(align="left", dx=4, fontSize=11, color="#4A5568").encode(
        text=alt.Text("Effectif:Q", format=format_valeur)
    )
    return (graphique + valeurs).properties(height=alt.Step(HAUTEUR_BARRE))


def barres_par_secteur(tableau: pd.DataFrame, libelle: str) -> alt.Chart:
    """Barres horizontales empilées Public / Privé / Non renseigné.

    `tableau` vient de `analyse.repartition_par_statut` : une ligne par modalité.
    """
    ordre = list(tableau.index)
    longues = (
        tableau[SECTEURS]
        .rename_axis(libelle)
        .reset_index()
        .melt(id_vars=libelle, var_name="Secteur", value_name="Effectif")
    )
    longues = longues[longues["Effectif"] > 0]
    longues["Part"] = longues["Effectif"] / longues.groupby(libelle)["Effectif"].transform("sum")
    return (
        alt.Chart(longues)
        .mark_bar()
        .encode(
            y=alt.Y(
                f"{libelle}:N",
                sort=ordre,
                title=None,
                axis=alt.Axis(labelLimit=260, labelFontSize=12, ticks=False, domain=False),
                scale=alt.Scale(paddingInner=0.3),
            ),
            x=alt.X("Effectif:Q", title=None, axis=alt.Axis(format="~s", grid=True)),
            color=alt.Color(
                "Secteur:N",
                scale=COULEURS_SECTEURS,
                legend=alt.Legend(orient="top", title=None, direction="horizontal"),
            ),
            order=alt.Order("ordre_secteur:Q"),
            tooltip=[
                alt.Tooltip(f"{libelle}:N"),
                alt.Tooltip("Secteur:N"),
                alt.Tooltip("Effectif:Q", format="d"),
                alt.Tooltip("Part:Q", format=".1%"),
            ],
        )
        .transform_calculate(
            ordre_secteur="indexof(['Public', 'Privé', 'Non renseigné'], datum.Secteur)"
        )
        .properties(height=alt.Step(HAUTEUR_BARRE))
    )


def colonnes_annuelles(serie: pd.Series) -> alt.Chart:
    """Histogramme des ouvertures par année."""
    donnees = serie.rename("Ouvertures").rename_axis("Année").reset_index()
    donnees["Année"] = donnees["Année"].astype(str)
    return (
        alt.Chart(donnees)
        .mark_bar(color=PUBLIC, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("Année:O", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Ouvertures:Q", title=None),
            tooltip=["Année:O", alt.Tooltip("Ouvertures:Q", format="d")],
        )
        .properties(height=260)
    )
