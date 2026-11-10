"""Point d'entree. C'est le SEUL endroit qui choisit une source."""

import argparse
from collections import Counter

from annuaire import analyse
from annuaire.lecture import Lecteur, LecteurApi, LecteurCsv, LecteurParquet

SOURCES: dict[str, type[LecteurCsv | LecteurParquet | LecteurApi]] = {
    "csv": LecteurCsv,
    "parquet": LecteurParquet,
    "api": LecteurApi,
}


def main() -> None:
    parseur = argparse.ArgumentParser(description="Analyse l'Annuaire de l'education.")
    parseur.add_argument("--source", choices=sorted(SOURCES), default="csv")
    arguments = parseur.parse_args()

    lecteur: Lecteur = SOURCES[arguments.source]()

    rejets = analyse.Rejets()
    etablissements = [e for e in analyse.valider(lecteur, rejets) if e.est_ouvert]
    comptes = Counter(e.departement for e in etablissements)
    publics = sum(e.statut == "Public" for e in etablissements)

    print(f"source : {arguments.source}")
    print(f"{len(etablissements)} établissements ouverts")
    print(f"part du public : {publics / len(etablissements) * 100:.1f} %")
    if rejets.total:
        motifs = ", ".join(f"{c}× {m}" for m, c in rejets.par_motif.most_common())
        print(f"⚠ {rejets.total} enregistrements écartés à la validation ({motifs})")
    print("\nTop 5 des départements :")
    for departement, nombre in comptes.most_common(5):
        print(f"  {nombre:5d}  {departement}")


if __name__ == "__main__":
    main()
