"""Point d'entrée du projet. Les données passent par annuaire.ingestion."""

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from annuaire import analyse
from annuaire.ingestion import SOURCES, ingestion_donnees


def main() -> None:
    parseur = argparse.ArgumentParser(description="Analyse l'Annuaire de l'education.")
    parseur.add_argument("--source", choices=sorted(SOURCES), default="csv")
    parseur.add_argument(
        "--maj",
        action="store_true",
        help="Retélécharge les données même si le fichier existe déjà.",
    )
    arguments = parseur.parse_args()

    print("Démarrage de l'annuaire")
    print("--------------------------------")
    print("1. Ingestion des données...")
    rejets = analyse.Rejets()
    lecteur = ingestion_donnees(arguments.source, mettre_a_jour=arguments.maj)

    print("--------------------------------")
    print("2. Analyse des données...")
    print("--------------------------------")
    etablissements = [e for e in analyse.valider(lecteur, rejets) if e.est_ouvert]
    comptes = Counter(e.departement for e in etablissements)
    publics = sum(e.statut == "Public" for e in etablissements)

    print(f"source : {arguments.source}")
    print(f"{len(etablissements)} établissements ouverts")
    if etablissements:
        print(f"part du public : {publics / len(etablissements) * 100:.1f} %")
    if rejets.total:
        motifs = ", ".join(f"{c}× {m}" for m, c in rejets.par_motif.most_common())
        print(f"⚠ {rejets.total} enregistrements écartés à la validation ({motifs})")
    print("\nTop 5 des départements :")
    for departement, nombre in comptes.most_common(5):
        print(f"  {nombre:5d}  {departement}")


if __name__ == "__main__":
    main()
