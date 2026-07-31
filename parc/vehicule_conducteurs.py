"""Conducteurs autorisés pour un véhicule (titulaire et/ou chauffeurs)."""

from .models import Personnel, Vehicule


def ids_conducteurs_autorises(vehicule):
    if not vehicule:
        return set()
    ids = set()
    if vehicule.personnel_id:
        ids.add(vehicule.personnel_id)
    if vehicule.pk:
        ids.update(vehicule.chauffeurs.values_list("pk", flat=True))
    return ids


def conducteurs_autorises_pour(vehicule):
    ids = ids_conducteurs_autorises(vehicule)
    if not ids:
        return Personnel.objects.none()
    return Personnel.objects.filter(pk__in=ids).order_by("nom", "prenom")


def libelle_conducteur(personnel, vehicule):
    if vehicule and vehicule.personnel_id == personnel.pk:
        return f"{personnel} (titulaire)"
    return f"{personnel} (chauffeur)"


def cartographie_conducteurs_vehicules():
    carte = {}
    vehicules = (
        Vehicule.objects.filter(actif=True)
        .select_related("personnel")
        .prefetch_related("chauffeurs")
    )
    for vehicule in vehicules:
        options = []
        if vehicule.personnel_id:
            options.append({
                "id": vehicule.personnel_id,
                "label": libelle_conducteur(vehicule.personnel, vehicule),
            })
        for chauffeur in vehicule.chauffeurs.all():
            if chauffeur.pk == vehicule.personnel_id:
                continue
            options.append({
                "id": chauffeur.pk,
                "label": libelle_conducteur(chauffeur, vehicule),
            })
        carte[str(vehicule.pk)] = options
    return carte


def conducteur_autorise_pour_vehicule(vehicule, personnel):
    if not vehicule or not personnel:
        return False
    return personnel.pk in ids_conducteurs_autorises(vehicule)
