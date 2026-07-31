"""Règles de choix de place à l'entrée selon le poste du conducteur."""

from .models import Parking, Personnel, PlaceParking


def place_reservee_pour_poste(poste):
    if not poste:
        return None
    return (
        PlaceParking.objects.filter(
            poste_affecte=poste,
            parking__type_parking=Parking.TYPE_RESERVE,
            actif=True,
        )
        .select_related("parking", "poste_affecte")
        .first()
    )


def places_universelles_libres():
    return PlaceParking.objects.filter(
        parking__type_parking=Parking.TYPE_UNIVERSEL,
        statut=PlaceParking.STATUT_LIBRE,
        actif=True,
    ).select_related("parking").order_by("parking__nom", "numero")


def queryset_places_pour_conducteur(conducteur, place_courante_id=None):
    """
    Retourne (queryset, place_auto) :
    - place réservée : une seule place, pré-sélectionnée ;
    - sinon : uniquement les places du parking universel libres.
    """
    if not conducteur:
        return PlaceParking.objects.none(), None

    place_reservee = place_reservee_pour_poste(conducteur.poste_obj)
    if place_reservee:
        return PlaceParking.objects.filter(pk=place_reservee.pk), place_reservee

    qs = places_universelles_libres()
    if place_courante_id:
        qs = qs | PlaceParking.objects.filter(
            pk=place_courante_id,
            parking__type_parking=Parking.TYPE_UNIVERSEL,
            actif=True,
        )
    return qs.distinct(), None


def place_autorisee_pour_conducteur(conducteur, place, place_courante_id=None):
    if not conducteur or not place:
        return False

    qs, _place_auto = queryset_places_pour_conducteur(
        conducteur,
        place_courante_id=place_courante_id,
    )
    return qs.filter(pk=place.pk).exists()


def cartographie_places_conducteurs():
    """Données JSON pour le formulaire d'entrée (filtrage côté navigateur)."""
    universelles = [
        {"id": place.pk, "label": str(place)}
        for place in places_universelles_libres()
    ]

    conducteurs = {}
    for personnel in Personnel.objects.filter(actif=True).select_related("poste_obj"):
        place_reservee = place_reservee_pour_poste(personnel.poste_obj)
        if place_reservee:
            conducteurs[str(personnel.pk)] = {
                "mode": "reserve",
                "place": {
                    "id": place_reservee.pk,
                    "label": str(place_reservee),
                    "libre": place_reservee.statut == PlaceParking.STATUT_LIBRE,
                },
            }
        else:
            conducteurs[str(personnel.pk)] = {"mode": "universel"}

    return {
        "places_universelles": universelles,
        "conducteurs": conducteurs,
    }
