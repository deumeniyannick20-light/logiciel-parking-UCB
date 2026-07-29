"""Gestion des places réservées sans poste (alerte obligatoire)."""

import re

from django.urls import reverse

from .models import Parking, PlaceParking

SESSION_KEY = "places_alerte_sans_poste"


def _places_orphelines_db():
    return list(
        PlaceParking.objects.filter(
            parking__type_parking=Parking.TYPE_RESERVE,
            poste_affecte__isnull=True,
            actif=True,
        ).values_list("pk", flat=True)
    )


def synchroniser_alertes(request):
    """Fusionne session et places orphelines en base."""
    session_ids = set(request.session.get(SESSION_KEY, []))
    db_ids = set(_places_orphelines_db())
    alertes = sorted(session_ids | db_ids)
    if alertes:
        request.session[SESSION_KEY] = alertes
    else:
        request.session.pop(SESSION_KEY, None)
    return alertes


def enregistrer_alertes(request, place_pks):
    alertes = set(synchroniser_alertes(request))
    alertes.update(place_pks)
    request.session[SESSION_KEY] = sorted(alertes)


def resoudre_alerte(request, place_pk):
    place = PlaceParking.objects.filter(pk=place_pk).select_related("parking").first()
    if not place:
        synchroniser_alertes(request)
        return
    if (
        place.parking.type_parking == Parking.TYPE_RESERVE
        and place.poste_affecte_id
    ):
        alertes = [pk for pk in synchroniser_alertes(request) if pk != place_pk]
        if alertes:
            request.session[SESSION_KEY] = alertes
        else:
            request.session.pop(SESSION_KEY, None)


def alertes_actives(request):
    return synchroniser_alertes(request)


def url_autorisee(path, alertes):
    if not alertes:
        return True

    liste = reverse("placeparking_liste")
    if path == liste or path.rstrip("/") == liste.rstrip("/"):
        return True

    pattern = re.compile(r"^/places-parking/(\d+)/modifier/?$")
    match = pattern.match(path)
    if match and int(match.group(1)) in alertes:
        return True

    return False
