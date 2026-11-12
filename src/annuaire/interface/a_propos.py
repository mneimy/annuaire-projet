"""Page À propos : objectif pédagogique, démarche, et fiche de chaque indicateur."""

from dataclasses import dataclass

import streamlit as st

from annuaire.interface.style import URL_API, URL_JEU_DE_DONNEES, URL_LICENCE


@dataclass(frozen=True)
class Indicateur:
    """Fiche descriptive d'un indicateur du tableau de bord."""

    icone: str
    nom: str
    definition: str
    calcul: str
    fonction: str
    vigilance: str


INDICATEURS = [
    Indicateur(
        ":material/school:",
        "Établissements ouverts",
        "Nombre d'établissements à l'état « OUVERT » dans le périmètre choisi.",
        "Nombre de lignes du fichier après filtre. L'ingestion ne garde que les établissements "
        "ouverts ; la carte détaille aussi le nombre d'écoles.",
        "len(vue)",
        (
            "Un établissement = une ligne de l'annuaire (UAI). Une cité scolaire peut compter "
            "plusieurs UAI : collège et lycée sont alors comptés séparément."
        ),
    ),
    Indicateur(
        ":material/account_balance:",
        "Secteur public",
        "Part des établissements publics.",
        "Publics ÷ (publics + privés) × 100. Les établissements sans statut renseigné "
        "(surtout des services administratifs) sont exclus du dénominateur.",
        "analyse.part_public",
        (
            "Exclure les « non renseignés » évite de sous-estimer la part du public, mais on "
            "l'affiche à part pour rester transparent."
        ),
    ),
    Indicateur(
        ":material/diversity_3:",
        "Éducation prioritaire",
        "Part des établissements rattachés à un réseau d'éducation prioritaire (REP ou REP+).",
        "(REP + REP+) ÷ total des établissements × 100.",
        "analyse.education_prioritaire",
        (
            "L'éducation prioritaire concerne les écoles et collèges : rapportée à tous les types, "
            "la part est mécaniquement plus faible. Filtrez sur « Collège » pour la lire au bon niveau."
        ),
    ),
    Indicateur(
        ":material/trending_up:",
        "Ouvertures sur 12 mois",
        "Établissements ouverts au cours des 12 derniers mois, comparés aux 12 mois précédents.",
        "Comptage sur la colonne date_ouverture, la date de référence étant la mise à jour "
        "la plus récente du fichier. Le mini-graphe montre les dix dernières années.",
        "analyse.ouvertures_recentes, analyse.ouvertures_par_annee",
        (
            "Biais de survie : l'annuaire ne contient que les établissements encore ouverts. "
            "Ce n'est pas un historique des ouvertures, mais l'âge du parc actuel."
        ),
    ),
    Indicateur(
        ":material/handshake:",
        "Privé sous contrat",
        "Part des établissements privés liés à l'État par un contrat (d'association ou simple).",
        "Sous contrat ÷ (sous contrat + hors contrat) × 100, sur les privés dont le contrat est connu.",
        "analyse.prive_sous_contrat",
        (
            "Les libellés de la source sont hétérogènes (« C0NTRAT » avec un zéro, abréviations) : "
            "ils sont normalisés par analyse.libelle_contrat avant comptage."
        ),
    ),
    Indicateur(
        ":material/restaurant:",
        "Restauration, internat, ULIS",
        "Part des établissements qui proposent une restauration scolaire, un hébergement "
        "(internat) ou un dispositif ULIS (inclusion des élèves en situation de handicap).",
        "Établissements à 1 ÷ établissements renseignés (0 ou 1) × 100.",
        "analyse.taux_service",
        (
            "Environ 7 % des établissements n'ont pas l'information : ils sont exclus du calcul "
            "plutôt que comptés comme « sans service »."
        ),
    ),
]

GRAPHIQUES = [
    (
        "Implantation (carte)",
        (
            "Chaque point est un établissement géolocalisé ; bleu public, orange privé. "
            "En vue nationale, seule la métropole est affichée pour garder une échelle lisible."
        ),
    ),
    (
        "Départements et régions",
        (
            "Effectifs empilés public / privé / non renseigné, triés par total. "
            "Fonction : analyse.repartition_par_statut."
        ),
    ),
    (
        "Par type d'établissement",
        "Même découpage par type (école, collège, lycée, médico-social…).",
    ),
    (
        "Ouvertures par année",
        "Année d'ouverture des établissements toujours ouverts, sur vingt ans.",
    ),
    (
        "Ministère de tutelle",
        (
            "Effectif et part de chaque ministère ; l'Éducation nationale domine, "
            "les autres tutelles (santé, agriculture…) sont lisibles dans le tableau."
        ),
    ),
    (
        "Types de contrat et part du privé",
        (
            "Répartition des contrats du privé, et part du privé "
            "par région (ou par département si une région est choisie)."
        ),
    ),
]

PIPELINE = """
digraph {
    rankdir=LR;
    bgcolor="transparent";
    node [shape=box, style="rounded,filled", fillcolor="#FFFFFF", color="#C9D6EE",
          fontname="Helvetica", fontsize=11, margin="0.18,0.1"];
    edge [color="#2453A6", arrowsize=0.7];
    api   [label="API data.education.gouv.fr\\nCSV · Parquet", fillcolor="#E8EEF8"];
    lect  [label="lecture.py\\nLecteurs (Protocol)"];
    valid [label="model.py\\nValidation pydantic"];
    net   [label="nettoyage.py · ingestion.py\\nCSV d'ingestion"];
    ana   [label="analyse.py\\nIndicateurs pandas"];
    app   [label="interface/\\nApplication Streamlit", fillcolor="#FCEBDF", color="#E07A3F"];
    api -> lect -> valid -> net -> ana -> app;
}
"""


def _fiche(indicateur: Indicateur, numero: int) -> None:
    with st.container(border=True, key=f"bloc_fiche_{numero}", height="stretch"):
        st.markdown(f"#### {indicateur.icone} {indicateur.nom}")
        st.markdown(indicateur.definition)
        st.markdown(f"**Calcul.** {indicateur.calcul}")
        st.markdown(f"**Dans le code.** `{indicateur.fonction}`")
        st.caption(f":material/lightbulb: {indicateur.vigilance}")


def page_a_propos() -> None:
    """Objectif du projet, démarche de co-développement et définition des indicateurs."""
    st.title("À propos")
    st.caption(
        "Pourquoi ce projet existe, comment il a été construit, et ce que mesure chaque indicateur."
    )

    objectif, demarche = st.columns(2, gap="medium")
    with objectif, st.container(border=True, key="bloc_objectif", height="stretch"):
        st.subheader(":material/menu_book: Un objectif pédagogique")
        st.markdown(
            "Ce projet sert de fil rouge au module **Développement Python (M2)**. "
            "Il s'inscrit dans une démarche de **partage du savoir-faire** : montrer, sur un "
            "jeu de données public et réel, le chemin complet d'un projet data, de la donnée "
            "brute jusqu'à une application que l'on peut mettre entre les mains d'un utilisateur."
        )
        st.markdown(
            "- lire plusieurs sources (API, CSV, Parquet) derrière un même contrat ;\n"
            "- valider les données avec pydantic et compter ce qu'on écarte ;\n"
            "- calculer des indicateurs testables, séparés de l'affichage ;\n"
            "- restituer avec Streamlit, en expliquant chaque chiffre ;\n"
            "- outiller la qualité : uv, Ruff, mypy."
        )
    with demarche, st.container(border=True, key="bloc_demarche", height="stretch"):
        st.subheader(":material/smart_toy: Co-développé avec l'IA")
        st.markdown(
            "Le projet a été réalisé en **co-développement, assisté par l'IA**. "
            "Le formateur fixe l'intention, l'architecture et les règles de qualité ; "
            "l'assistant propose du code, des refactorisations et des vérifications ; "
            "chaque proposition est relue, exécutée et confrontée aux données avant d'être gardée."
        )
        st.markdown(
            "L'IA accélère l'écriture, pas le jugement. Les choix de définition d'un indicateur "
            "(quel dénominateur, que faire des valeurs manquantes) restent des décisions humaines, "
            "documentées ci-dessous. C'est aussi ce que l'on veut transmettre : savoir piloter "
            "un assistant, et savoir vérifier ce qu'il produit."
        )

    with st.container(border=True, key="bloc_pipeline"):
        st.subheader(":material/account_tree: Du jeu de données à l'application")
        st.graphviz_chart(PIPELINE)

    st.space("small")
    st.header("Les indicateurs")
    st.caption(
        "Pour chacun : ce qu'il mesure, comment il est calculé, où le trouver dans le code, "
        "et le piège à connaître pour bien le lire."
    )
    for debut in range(0, len(INDICATEURS), 2):
        colonnes = st.columns(2, gap="medium")
        for decalage, (colonne, indicateur) in enumerate(
            zip(colonnes, INDICATEURS[debut : debut + 2], strict=False)
        ):
            with colonne:
                _fiche(indicateur, debut + decalage)

    with st.container(border=True, key="bloc_graphiques_def"):
        st.subheader(":material/bar_chart: Les graphiques")
        for titre, description in GRAPHIQUES:
            st.markdown(f"**{titre}** — {description}")

    with st.container(border=True, key="bloc_source"):
        st.subheader(":material/database: Source et licence")
        st.markdown(
            f"Données : [Annuaire de l'éducation]({URL_JEU_DE_DONNEES}), ministère de "
            f"l'Éducation nationale, publié sur data.gouv.fr et interrogé via "
            f"l'[API data.education.gouv.fr]({URL_API}). Réutilisation sous "
            f"[Licence Ouverte 2.0]({URL_LICENCE}). Les traitements et indicateurs sont ceux "
            "de ce projet et n'engagent pas le producteur des données."
        )
