"""Gestion du personnel sans véhicule pour un poste avec place réservée."""

from django.db.models import Exists, OuterRef
from django.urls import reverse

from .models import Parking, Personnel, Vehicule

SESSION_KEY = "personnel_alerte_sans_vehicule"


def poste_a_place_reservee(poste):
    if not poste:
        return False
    return poste.places_affectees.filter(
        parking__type_parking=Parking.TYPE_RESERVE,
    ).exists()


def personnel_exige_vehicule(personnel):
    if not personnel or not personnel.poste_obj_id:
        return False
    if not poste_a_place_reservee(personnel.poste_obj):
        return False
    return not Vehicule.objects.filter(personnel=personnel).exists()


def _personnels_orphelins_db():
    vehicule_existe = Vehicule.objects.filter(personnel_id=OuterRef("pk"))
    return list(
        Personnel.objects.filter(
            actif=True,
            poste_obj__places_affectees__parking__type_parking=Parking.TYPE_RESERVE,
        )
        .annotate(a_vehicule=Exists(vehicule_existe))
        .filter(a_vehicule=False)
        .values_list("pk", flat=True)
        .distinct()
    )


def synchroniser_alertes_vehicule(request):
    session_ids = set(request.session.get(SESSION_KEY, []))
    db_ids = set(_personnels_orphelins_db())
    alertes = sorted(session_ids | db_ids)
    if alertes:
        request.session[SESSION_KEY] = alertes
    else:
        request.session.pop(SESSION_KEY, None)
    return alertes


def enregistrer_alerte_vehicule(request, personnel_pk):
    alertes = set(synchroniser_alertes_vehicule(request))
    alertes.add(personnel_pk)
    request.session[SESSION_KEY] = sorted(alertes)


def resoudre_alerte_vehicule(request, personnel_pk):
    personnel = Personnel.objects.filter(pk=personnel_pk).select_related("poste_obj").first()
    if not personnel:
        synchroniser_alertes_vehicule(request)
        return
    if not personnel_exige_vehicule(personnel):
        alertes = [pk for pk in synchroniser_alertes_vehicule(request) if pk != personnel_pk]
        if alertes:
            request.session[SESSION_KEY] = alertes
        else:
            request.session.pop(SESSION_KEY, None)


def alertes_vehicule_actives(request):
    return synchroniser_alertes_vehicule(request)


def url_autorisee_vehicule(path, alertes):
    if not alertes:
        return True

    liste = reverse("vehicule_liste")
    if path == liste or path.rstrip("/") == liste.rstrip("/"):
        return True

    creer = reverse("vehicule_creer")
    if path == creer or path.rstrip("/") == creer.rstrip("/"):
        return True

    return False
