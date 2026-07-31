"""
Règles d'affectation des postes au personnel.

- Poste SANS place de parking réservée : peut être détenu par plusieurs personnels.
- Poste AVEC place réservée : un seul personnel à la fois.
"""

from .models import Parking, Personnel, Poste


def poste_partageable_entre_personnels(poste):
    """Vrai si le poste n'est affecté à aucune place de parking réservée."""
    return not poste.est_affecte_place_reservee()


def ids_postes_reserves_deja_attribues(exclure_personnel_id=None):
    """Postes réservés déjà occupés par au moins un autre personnel."""
    postes_reserves = Poste.objects.filter(
        places_affectees__parking__type_parking=Parking.TYPE_RESERVE,
        places_affectees__actif=True,
        actif=True,
    )
    qs = Personnel.objects.filter(poste_obj__in=postes_reserves)
    if exclure_personnel_id:
        qs = qs.exclude(pk=exclure_personnel_id)
    return set(qs.values_list("poste_obj_id", flat=True))


def personnel_peut_occuper_poste(poste, personnel=None):
    if poste_partageable_entre_personnels(poste):
        return True
    exclure_id = personnel.pk if personnel and personnel.pk else None
    return poste.pk not in ids_postes_reserves_deja_attribues(exclure_personnel_id=exclure_id)


def queryset_postes_pour_personnel(personnel=None):
    """
    Postes proposables :
    - tous les postes sans place réservée ;
    - les postes réservés encore libres (aucun personnel).
    """
    exclure_id = personnel.pk if personnel and personnel.pk else None
    indisponibles = ids_postes_reserves_deja_attribues(exclure_personnel_id=exclure_id)
    qs = Poste.objects.filter(actif=True).exclude(pk__in=indisponibles)
    if personnel and personnel.pk and personnel.poste_obj_id:
        qs = qs | Poste.objects.filter(pk=personnel.poste_obj_id)
    return qs.distinct().order_by("nom")


def message_poste_indisponible():
    return (
        "Ce poste est lié à une place de parking réservée déjà attribuée à un "
        "autre membre du personnel. Seuls les postes sans place réservée peuvent "
        "être partagés entre plusieurs personnels."
    )
