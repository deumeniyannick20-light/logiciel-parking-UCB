"""Regroupe les occupations par jour calendaire puis par véhicule."""

from collections import defaultdict

from django.utils import timezone

_JOURS = (
    "lundi",
    "mardi",
    "mercredi",
    "jeudi",
    "vendredi",
    "samedi",
    "dimanche",
)
_MOIS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)


def libelle_jour(date_jour):
    return (
        f"{_JOURS[date_jour.weekday()].capitalize()} "
        f"{date_jour.day} {_MOIS[date_jour.month - 1]} {date_jour.year}"
    )


def grouper_occupations_par_jour_et_vehicule(occupations):
    """
    Retourne une liste de blocs journaliers, du plus récent au plus ancien.

    Chaque bloc contient :
    - date : date calendaire (entrée)
    - libelle : intitulé affiché (ex. « Lundi 30 juillet 2026 »)
    - lignes : véhicules du jour, chacun avec ses mouvements triés chronologiquement
    """
    par_jour = defaultdict(lambda: defaultdict(list))

    for occupation in occupations:
        jour = timezone.localtime(occupation.date_entree).date()
        par_jour[jour][occupation.vehicule_id].append(occupation)

    blocs = []
    for date_jour in sorted(par_jour.keys(), reverse=True):
        lignes = []
        for mouvements in par_jour[date_jour].values():
            mouvements.sort(key=lambda occ: occ.date_entree)
            lignes.append({
                "vehicule": mouvements[0].vehicule,
                "mouvements": mouvements,
            })
        lignes.sort(
            key=lambda ligne: ligne["mouvements"][-1].date_entree,
            reverse=True,
        )
        blocs.append({
            "date": date_jour,
            "libelle": libelle_jour(date_jour),
            "lignes": lignes,
        })

    return blocs
