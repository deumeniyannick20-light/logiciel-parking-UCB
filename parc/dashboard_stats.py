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


def _arrondir_minute(dt):
    return dt.replace(second=0, microsecond=0)


def _detail_evenement(occ, type_evenement):
    vehicule = occ.vehicule
    if type_evenement == "entree":
        conducteur = occ.conducteur_entree
        instant = occ.date_entree
    else:
        conducteur = occ.conducteur_sortie
        instant = occ.date_sortie
    return {
        "type": type_evenement,
        "instant": instant.isoformat() if instant else None,
        "label": instant.strftime("%H:%M") if instant else None,
        "immatriculation": vehicule.immatriculation,
        "marque": vehicule.marque,
        "modele": vehicule.modele,
        "vehicule": str(vehicule),
        "conducteur": str(conducteur) if conducteur else "—",
        "place": str(occ.place_parking),
    }


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
    ).select_related(
        "vehicule",
        "conducteur_entree",
        "conducteur_sortie",
        "place_parking",
        "place_parking__parking",
    )
    if parking_id:
        qs = qs.filter(place_parking__parking_id=parking_id)
    evenements = []
    for occ in qs:
        if occ.date_entree >= debut and occ.date_entree < fin:
            evenements.append(_detail_evenement(occ, "entree"))
        if occ.date_sortie and occ.date_sortie >= debut and occ.date_sortie < fin:
            evenements.append(_detail_evenement(occ, "sortie"))
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


def serie_flux_24h(heures=24):
    """Entrées et sorties horaires sur 24 h, avec détail minute par événement."""
    fin = _arrondir_heure(_maintenant()) + timedelta(hours=1)
    debut = fin - timedelta(hours=heures)
    points_horaires = []
    for i in range(heures):
        instant = debut + timedelta(hours=i)
        points_horaires.append({
            "label": instant.strftime("%H:%M"),
            "instant": instant.isoformat(),
            "entrees": 0,
            "sorties": 0,
            "evenements": [],
        })

    def _index_horaire(instant):
        return int((_arrondir_heure(instant) - debut).total_seconds() // 3600)

    occupations = Occupation.objects.filter(
        Q(date_entree__gte=debut, date_entree__lt=fin)
        | Q(date_sortie__gte=debut, date_sortie__lt=fin)
    ).select_related(
        "vehicule",
        "conducteur_entree",
        "conducteur_sortie",
        "place_parking",
    )

    for occ in occupations:
        if occ.date_entree and debut <= occ.date_entree < fin:
            idx = _index_horaire(occ.date_entree)
            if 0 <= idx < len(points_horaires):
                points_horaires[idx]["entrees"] += 1
                points_horaires[idx]["evenements"].append(_detail_evenement(occ, "entree"))
        if occ.date_sortie and debut <= occ.date_sortie < fin:
            idx = _index_horaire(occ.date_sortie)
            if 0 <= idx < len(points_horaires):
                points_horaires[idx]["sorties"] += 1
                points_horaires[idx]["evenements"].append(_detail_evenement(occ, "sortie"))

    for point in points_horaires:
        point["evenements"].sort(key=lambda ev: ev.get("instant") or "")

    entrees = [point["entrees"] for point in points_horaires]
    sorties = [point["sorties"] for point in points_horaires]
    return {
        "labels": [point["label"] for point in points_horaires],
        "entrees": entrees,
        "sorties": sorties,
        "points": points_horaires,
        "tendance_entrees": tendance_depuis_valeurs(entrees),
        "tendance_sorties": tendance_depuis_valeurs(sorties),
    }


def tendance_fenetre_minutes(valeurs, fenetre=60):
    """Compare la dernière heure glissante à l'heure précédente."""
    if len(valeurs) < fenetre:
        return {"direction": "stable", "variation": 0}
    actuel = sum(valeurs[-fenetre:])
    if len(valeurs) >= fenetre * 2:
        avant = sum(valeurs[-fenetre * 2:-fenetre])
    else:
        avant = sum(valeurs[:-fenetre])
    if actuel > avant:
        direction = "hausse"
    elif actuel < avant:
        direction = "baisse"
    else:
        direction = "stable"
    return {"direction": direction, "variation": actuel - avant}


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
