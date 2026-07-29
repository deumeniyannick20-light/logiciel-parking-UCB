"""Calcul des indicateurs et séries temporelles pour le tableau de bord."""

from calendar import monthrange
from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from .models import Occupation, Parking, PlaceParking, Vehicule


def _maintenant():
    return timezone.now()


def _arrondir_heure(dt):
    return dt.replace(minute=0, second=0, microsecond=0)


def _occupations_actives_a(instant, parking_id=None):
    qs = Occupation.objects.filter(date_entree__lte=instant).filter(
        Q(date_sortie__isnull=True) | Q(date_sortie__gt=instant)
    )
    if parking_id:
        qs = qs.filter(place_parking__parking_id=parking_id)
    return qs


def _evenements_periode(debut, fin, parking_id=None):
    qs = Occupation.objects.filter(
        Q(date_entree__gte=debut, date_entree__lt=fin)
        | Q(date_sortie__gte=debut, date_sortie__lt=fin)
    ).select_related("vehicule", "place_parking", "place_parking__parking")
    if parking_id:
        qs = qs.filter(place_parking__parking_id=parking_id)
    evenements = []
    for occ in qs:
        if occ.date_entree >= debut and occ.date_entree < fin:
            evenements.append({
                "type": "entree",
                "instant": occ.date_entree.isoformat(),
                "vehicule": str(occ.vehicule),
                "place": str(occ.place_parking),
            })
        if occ.date_sortie and occ.date_sortie >= debut and occ.date_sortie < fin:
            evenements.append({
                "type": "sortie",
                "instant": occ.date_sortie.isoformat(),
                "vehicule": str(occ.vehicule),
                "place": str(occ.place_parking),
            })
    evenements.sort(key=lambda e: e["instant"])
    return evenements


def serie_presence_24h(parking_id=None, points=24):
    """Série horaire des véhicules ou places occupées sur les dernières 24 h."""
    fin = _arrondir_heure(_maintenant()) + timedelta(hours=1)
    debut = fin - timedelta(hours=points)
    serie = []
    instant = debut
    while instant < fin:
        suivant = instant + timedelta(hours=1)
        if parking_id:
            valeur = _occupations_actives_a(instant, parking_id).count()
        else:
            valeur = (
                _occupations_actives_a(instant)
                .values("vehicule_id")
                .distinct()
                .count()
            )
        serie.append({
            "label": instant.strftime("%H:%M"),
            "instant": instant.isoformat(),
            "valeur": valeur,
            "evenements": _evenements_periode(instant, suivant, parking_id),
        })
        instant = suivant
    return serie


def tendance_depuis_serie(serie):
    if len(serie) < 2:
        return {"direction": "stable", "variation": 0}
    avant = serie[-2]["valeur"]
    actuel = serie[-1]["valeur"]
    if actuel > avant:
        direction = "hausse"
    elif actuel < avant:
        direction = "baisse"
    else:
        direction = "stable"
    variation = actuel - avant
    return {"direction": direction, "variation": variation}


def stats_vehicules():
    enregistres = Vehicule.objects.filter(actif=True).count()
    presents = (
        Occupation.objects.filter(date_sortie__isnull=True)
        .values("vehicule_id")
        .distinct()
        .count()
    )
    serie = serie_presence_24h()
    tendance = tendance_depuis_serie(serie)
    return {
        "enregistres": enregistres,
        "presents": presents,
        "tendance": tendance,
        "sparkline_24h": serie,
    }


def stats_parking_universel(parking):
    places = PlaceParking.objects.filter(parking=parking, actif=True)
    total = places.count()
    occupees = places.filter(statut=PlaceParking.STATUT_OCCUPEE).count()
    libres = max(total - occupees, 0)
    pct = round((occupees / total) * 100, 1) if total else 0
    serie = serie_presence_24h(parking_id=parking.pk)
    return {
        "id": parking.pk,
        "nom": parking.nom,
        "total": total,
        "libres": libres,
        "occupes": occupees,
        "pct_occupe": pct,
        "alerte": pct >= 80,
        "tendance": tendance_depuis_serie(serie),
        "sparkline_24h": serie,
    }


def stats_parkings_universels():
    parkings = Parking.objects.filter(
        type_parking=Parking.TYPE_UNIVERSEL,
        actif=True,
    ).order_by("nom")
    return [stats_parking_universel(p) for p in parkings]


def serie_mensuelle(parking_id=None, annee=None, mois=None):
    maintenant = _maintenant()
    annee = annee or maintenant.year
    mois = mois or maintenant.month
    _, nb_jours = monthrange(annee, mois)
    debut_mois = timezone.make_aware(datetime(annee, mois, 1))
    fin_mois = debut_mois + timedelta(days=nb_jours)
    serie = []
    for jour in range(1, nb_jours + 1):
        debut_jour = timezone.make_aware(datetime(annee, mois, jour))
        fin_jour = debut_jour + timedelta(days=1)
        if parking_id:
            pic = max(
                (
                    _occupations_actives_a(
                        debut_jour + timedelta(hours=h),
                        parking_id,
                    ).count()
                    for h in range(24)
                ),
                default=0,
            )
        else:
            pic = max(
                (
                    _occupations_actives_a(debut_jour + timedelta(hours=h))
                    .values("vehicule_id")
                    .distinct()
                    .count()
                    for h in range(24)
                ),
                default=0,
            )
        serie.append({
            "jour": jour,
            "label": debut_jour.strftime("%d/%m"),
            "instant": debut_jour.isoformat(),
            "valeur": pic,
            "evenements": _evenements_periode(debut_jour, fin_jour, parking_id),
        })
    return {
        "annee": annee,
        "mois": mois,
        "libelle_mois": debut_mois.strftime("%B %Y"),
        "serie": serie,
    }


def stats_mouvements_jour():
    debut = _maintenant().replace(hour=0, minute=0, second=0, microsecond=0)
    fin = debut + timedelta(days=1)
    return {
        "entrees": Occupation.objects.filter(
            date_entree__gte=debut, date_entree__lt=fin
        ).count(),
        "sorties": Occupation.objects.filter(
            date_sortie__gte=debut, date_sortie__lt=fin
        ).count(),
    }


def serie_libres_24h(points=24):
    """Places libres universelles — série horaire sur 24 h."""
    places_total = PlaceParking.objects.filter(
        parking__type_parking=Parking.TYPE_UNIVERSEL,
        parking__actif=True,
        actif=True,
    ).count()
    fin = _arrondir_heure(_maintenant()) + timedelta(hours=1)
    debut = fin - timedelta(hours=points)
    serie = []
    instant = debut
    while instant < fin:
        occ = (
            _occupations_actives_a(instant)
            .filter(place_parking__parking__type_parking=Parking.TYPE_UNIVERSEL)
            .count()
        )
        serie.append({
            "label": instant.strftime("%H:%M"),
            "valeur": max(places_total - occ, 0),
        })
        instant += timedelta(hours=1)
    return serie


def stats_occupation_globale_universel():
    places = PlaceParking.objects.filter(
        parking__type_parking=Parking.TYPE_UNIVERSEL,
        parking__actif=True,
        actif=True,
    )
    total = places.count()
    occupes = places.filter(statut=PlaceParking.STATUT_OCCUPEE).count()
    libres = max(total - occupes, 0)
    pct = round((occupes / total) * 100, 1) if total else 0
    sparkline = serie_libres_24h()
    return {
        "total": total,
        "occupes": occupes,
        "libres": libres,
        "pct": pct,
        "alerte": pct >= 80,
        "sparkline_24h": sparkline,
        "tendance": tendance_depuis_serie(sparkline),
    }


def serie_flux_24h(points=24):
    """Entrées et sorties horaires sur les dernières 24 h."""
    fin = _arrondir_heure(_maintenant()) + timedelta(hours=1)
    debut = fin - timedelta(hours=points)
    labels = []
    entrees = []
    sorties = []
    instant = debut
    while instant < fin:
        suivant = instant + timedelta(hours=1)
        labels.append(instant.strftime("%H:%M"))
        entrees.append(
            Occupation.objects.filter(
                date_entree__gte=instant, date_entree__lt=suivant
            ).count()
        )
        sorties.append(
            Occupation.objects.filter(
                date_sortie__gte=instant, date_sortie__lt=suivant
            ).count()
        )
        instant = suivant
    return {
        "labels": labels,
        "entrees": entrees,
        "sorties": sorties,
        "tendance_entrees": tendance_depuis_valeurs(entrees),
        "tendance_sorties": tendance_depuis_valeurs(sorties),
    }


def tendance_depuis_valeurs(valeurs):
    if len(valeurs) < 2:
        return {"direction": "stable", "variation": 0}
    avant, actuel = valeurs[-2], valeurs[-1]
    if actuel > avant:
        direction = "hausse"
    elif actuel < avant:
        direction = "baisse"
    else:
        direction = "stable"
    return {"direction": direction, "variation": actuel - avant}


def contexte_tableau_de_bord():
    occupation = stats_occupation_globale_universel()
    flux = serie_flux_24h()
    return {
        "vehicules": stats_vehicules(),
        "parkings_universels": stats_parkings_universels(),
        "mouvements_jour": stats_mouvements_jour(),
        "occupation_globale": occupation,
        "flux_24h": flux,
        "taux_disponibilite": round(100 - occupation["pct"], 1) if occupation["total"] else 100,
    }
