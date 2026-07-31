"""Indicateurs et historique pour le tableau de bord d'un véhicule."""

from calendar import monthrange
from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from .models import Occupation, Vehicule


PERIODES_VALIDES = ("jour", "semaine", "mois", "annee")

_LIBELLES_PERIODE = {
    "jour": "Aujourd'hui",
    "semaine": "7 derniers jours",
    "mois": "Ce mois",
    "annee": "Cette année",
}


def _maintenant():
    return timezone.now()


def _arrondir_heure(dt):
    return dt.replace(minute=0, second=0, microsecond=0)


def _debut_jour(dt):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def periode_depuis_preset(preset):
    now = _maintenant()
    if preset == "semaine":
        debut = now - timedelta(days=7)
    elif preset == "mois":
        debut = _debut_jour(now.replace(day=1))
    elif preset == "annee":
        debut = _debut_jour(now.replace(month=1, day=1))
    else:
        debut = _debut_jour(now)
    return debut, now


def _formater_duree(delta):
    if not delta or delta.total_seconds() <= 0:
        return "0 min"
    total_minutes = int(delta.total_seconds() // 60)
    heures, minutes = divmod(total_minutes, 60)
    if heures and minutes:
        return f"{heures} h {minutes:02d} min"
    if heures:
        return f"{heures} h"
    return f"{minutes} min"


def _duree_overlap(occ, debut, fin):
    entree = max(occ.date_entree, debut)
    sortie = min(occ.date_sortie or _maintenant(), fin)
    if sortie <= entree:
        return timedelta(0)
    return sortie - entree


def etat_actuel_vehicule(vehicule_id):
    occ = (
        Occupation.objects.filter(vehicule_id=vehicule_id, date_sortie__isnull=True)
        .select_related(
            "place_parking",
            "place_parking__parking",
            "conducteur_entree",
            "conducteur_entree__poste_obj",
        )
        .order_by("-date_entree")
        .first()
    )
    if not occ:
        return {
            "present": False,
            "place": None,
            "conducteur": None,
            "depuis": None,
            "depuis_label": None,
            "duree": None,
        }
    depuis = occ.date_entree
    return {
        "present": True,
        "place": str(occ.place_parking),
        "conducteur": str(occ.conducteur_entree),
        "depuis": depuis.isoformat(),
        "depuis_label": timezone.localtime(depuis).strftime("%d/%m/%Y %H:%M"),
        "duree": _formater_duree(_maintenant() - depuis),
    }


def _detail_historique(occ):
    entree_locale = timezone.localtime(occ.date_entree)
    sortie_locale = timezone.localtime(occ.date_sortie) if occ.date_sortie else None
    conducteur_sortie = str(occ.conducteur_sortie) if occ.conducteur_sortie else "—"
    morceaux = [
        str(occ.place_parking),
        str(occ.conducteur_entree),
        conducteur_sortie,
        entree_locale.strftime("%d/%m/%Y %H:%M"),
    ]
    if sortie_locale:
        morceaux.append(sortie_locale.strftime("%d/%m/%Y %H:%M"))
    if occ.observation:
        morceaux.append(occ.observation)
    return {
        "id": occ.pk,
        "place": str(occ.place_parking),
        "conducteur_entree": str(occ.conducteur_entree),
        "conducteur_sortie": conducteur_sortie,
        "date_entree": occ.date_entree.isoformat(),
        "date_entree_label": entree_locale.strftime("%d/%m/%Y %H:%M"),
        "date_sortie": occ.date_sortie.isoformat() if occ.date_sortie else None,
        "date_sortie_label": sortie_locale.strftime("%d/%m/%Y %H:%M") if sortie_locale else None,
        "duree_label": _formater_duree(occ.duree),
        "en_cours": occ.date_sortie is None,
        "observation": occ.observation or "",
        "recherche_texte": " ".join(morceaux).lower(),
    }


def _occupations_periode(vehicule_id, debut, fin):
    return (
        Occupation.objects.filter(vehicule_id=vehicule_id)
        .filter(
            Q(date_entree__lt=fin)
            & (Q(date_sortie__isnull=True) | Q(date_sortie__gt=debut))
        )
        .select_related(
            "place_parking",
            "place_parking__parking",
            "conducteur_entree",
            "conducteur_entree__poste_obj",
            "conducteur_sortie",
            "conducteur_sortie__poste_obj",
        )
        .order_by("-date_entree")
    )


def _filtrer_historique_mot_cle(lignes, mot_cle):
    q = (mot_cle or "").strip().lower()
    if not q:
        return lignes
    return [ligne for ligne in lignes if q in ligne["recherche_texte"]]


def _kpi_vehicule(occupations_qs, debut, fin):
    entrees = occupations_qs.filter(date_entree__gte=debut, date_entree__lt=fin).count()
    sorties = occupations_qs.filter(
        date_sortie__gte=debut,
        date_sortie__lt=fin,
    ).count()
    duree_totale = timedelta(0)
    places = set()
    for occ in occupations_qs:
        duree_totale += _duree_overlap(occ, debut, fin)
        if occ.date_entree < fin and (occ.date_sortie is None or occ.date_sortie > debut):
            places.add(occ.place_parking_id)
    return {
        "entrees": entrees,
        "sorties": sorties,
        "mouvements": entrees,
        "duree_totale_minutes": int(duree_totale.total_seconds() // 60),
        "duree_totale_label": _formater_duree(duree_totale),
        "places_distinctes": len(places),
    }


def _generer_buckets(debut, fin, preset):
    buckets = []
    if preset == "jour":
        cursor = _arrondir_heure(debut)
        if cursor < debut:
            cursor = cursor
        while cursor < fin:
            bucket_fin = min(cursor + timedelta(hours=1), fin)
            buckets.append({
                "debut": cursor,
                "fin": bucket_fin,
                "label": timezone.localtime(cursor).strftime("%H:%M"),
            })
            cursor += timedelta(hours=1)
    elif preset == "annee":
        cursor = debut.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        while cursor < fin:
            _, nb_jours = monthrange(cursor.year, cursor.month)
            bucket_fin = min(cursor + timedelta(days=nb_jours), fin)
            buckets.append({
                "debut": cursor,
                "fin": bucket_fin,
                "label": cursor.strftime("%m/%Y"),
            })
            cursor = cursor.replace(day=1) + timedelta(days=nb_jours)
    else:
        cursor = _debut_jour(debut)
        while cursor < fin:
            bucket_fin = min(cursor + timedelta(days=1), fin)
            buckets.append({
                "debut": cursor,
                "fin": bucket_fin,
                "label": timezone.localtime(cursor).strftime("%d/%m"),
            })
            cursor += timedelta(days=1)
    return buckets


def _index_bucket(instant, buckets, preset):
    if preset == "jour":
        cible = _arrondir_heure(instant)
    else:
        cible = _debut_jour(instant) if preset != "annee" else instant.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
    for i, bucket in enumerate(buckets):
        if bucket["debut"] <= cible < bucket["fin"]:
            return i
        if preset == "annee" and bucket["debut"].year == cible.year and bucket["debut"].month == cible.month:
            return i
    return None


def serie_flux_vehicule(vehicule_id, debut, fin, preset):
    buckets = _generer_buckets(debut, fin, preset)
    points = [
        {
            "label": b["label"],
            "instant": b["debut"].isoformat(),
            "entrees": 0,
            "sorties": 0,
        }
        for b in buckets
    ]
    occupations = Occupation.objects.filter(vehicule_id=vehicule_id).filter(
        Q(date_entree__gte=debut, date_entree__lt=fin)
        | Q(date_sortie__gte=debut, date_sortie__lt=fin)
    )
    for occ in occupations:
        if occ.date_entree and debut <= occ.date_entree < fin:
            idx = _index_bucket(occ.date_entree, buckets, preset)
            if idx is not None:
                points[idx]["entrees"] += 1
        if occ.date_sortie and debut <= occ.date_sortie < fin:
            idx = _index_bucket(occ.date_sortie, buckets, preset)
            if idx is not None:
                points[idx]["sorties"] += 1
    return {
        "labels": [p["label"] for p in points],
        "entrees": [p["entrees"] for p in points],
        "sorties": [p["sorties"] for p in points],
        "points": points,
    }


def serie_presence_vehicule(vehicule_id, debut, fin, preset):
    buckets = _generer_buckets(debut, fin, preset)
    serie = []
    for bucket in buckets:
        milieu = bucket["debut"] + (bucket["fin"] - bucket["debut"]) / 2
        present = (
            Occupation.objects.filter(vehicule_id=vehicule_id, date_entree__lte=milieu)
            .filter(Q(date_sortie__isnull=True) | Q(date_sortie__gt=milieu))
            .exists()
        )
        duree_bucket = timedelta(0)
        for occ in _occupations_periode(vehicule_id, bucket["debut"], bucket["fin"]):
            duree_bucket += _duree_overlap(occ, bucket["debut"], bucket["fin"])
        minutes = int(duree_bucket.total_seconds() // 60)
        serie.append({
            "label": bucket["label"],
            "instant": bucket["debut"].isoformat(),
            "present": 1 if present else 0,
            "minutes": minutes,
        })
    return serie


def liste_vehicules_recherche():
    presents_ids = set(
        Occupation.objects.filter(date_sortie__isnull=True).values_list("vehicule_id", flat=True)
    )
    vehicules = Vehicule.objects.filter(actif=True).order_by("immatriculation")
    return [
        {
            "id": v.pk,
            "label": str(v),
            "immatriculation": v.immatriculation,
            "marque": v.marque,
            "modele": v.modele,
            "present": v.pk in presents_ids,
        }
        for v in vehicules
    ]


def contexte_dashboard_vehicule(vehicule, periode="jour", mot_cle=""):
    if periode not in PERIODES_VALIDES:
        periode = "jour"
    debut, fin = periode_depuis_preset(periode)
    occupations = _occupations_periode(vehicule.pk, debut, fin)
    historique = [_detail_historique(occ) for occ in occupations]
    historique_filtre = _filtrer_historique_mot_cle(historique, mot_cle)
    return {
        "vehicule": {
            "id": vehicule.pk,
            "label": str(vehicule),
            "immatriculation": vehicule.immatriculation,
            "marque": vehicule.marque,
            "modele": vehicule.modele,
            "couleur": vehicule.couleur,
            "actif": vehicule.actif,
        },
        "periode": periode,
        "periode_libelle": _LIBELLES_PERIODE[periode],
        "debut": debut.isoformat(),
        "fin": fin.isoformat(),
        "etat_actuel": etat_actuel_vehicule(vehicule.pk),
        "kpi": _kpi_vehicule(occupations, debut, fin),
        "flux": serie_flux_vehicule(vehicule.pk, debut, fin, periode),
        "presence": serie_presence_vehicule(vehicule.pk, debut, fin, periode),
        "historique": historique_filtre,
        "historique_total": len(historique),
    }
