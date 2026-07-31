"""Identification du poste Chauffeur et du personnel éligible."""

from django.db.models import Min, Q

from .models import Personnel, Poste


def postes_chauffeur():
    return Poste.objects.filter(
        Q(est_chauffeur=True) | Q(nom__iexact="chauffeur"),
        actif=True,
    )


def personnel_est_chauffeur(personnel):
    if not personnel or not personnel.poste_obj_id:
        return False
    poste = personnel.poste_obj
    return poste.est_chauffeur or poste.nom.strip().lower() == "chauffeur"


def personnel_chauffeurs_disponibles(exclure_pk=None):
    base = Personnel.objects.filter(
        actif=True,
        poste_obj__in=postes_chauffeur(),
    )
    if exclure_pk:
        base = base.exclude(pk=exclure_pk)

    pks_uniques = (
        base.values("nom", "prenom", "poste_obj_id")
        .annotate(pk_retenu=Min("pk"))
        .values_list("pk_retenu", flat=True)
    )
    return (
        Personnel.objects.filter(pk__in=pks_uniques)
        .select_related("poste_obj")
        .order_by("nom", "prenom")
    )
