from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Case, Q, Value, When
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models import (
    Vehicule, Personnel, Zone,
    Poste, Parking, PlaceParking, Utilisateur, Occupation
)
from .forms import (
    VehiculeForm, PersonnelForm, ZoneForm,
    PosteForm, ParkingForm, PlaceParkingForm, UtilisateurForm,
    OccupationEntreeForm,
    OccupationSortieForm,
    OccupationModifierForm,
)
from .dashboard_stats import (
    contexte_tableau_de_bord,
    stats_vehicules,
    stats_parking_universel,
    serie_mensuelle,
)
from .place_alerte import alertes_actives, enregistrer_alertes, resoudre_alerte
from .liste_signaux import contexte_liste, redirect_liste
from .vehicule_conducteurs import cartographie_conducteurs_vehicules
from .occupation_places import cartographie_places_conducteurs
from .occupation_liste_groupee import grouper_occupations_par_jour_et_vehicule
from .vehicule_dashboard_stats import (
    contexte_dashboard_vehicule,
    liste_vehicules_recherche,
)
from .vehicule_alerte import (
    alertes_vehicule_actives,
    enregistrer_alerte_vehicule,
    personnel_exige_vehicule,
    resoudre_alerte_vehicule,
    retirer_alerte_vehicule,
)
from .decorators import administrateur_requis


@login_required
def dashboard(request):
    return render(request, "parc/dashboard.html")


@login_required
def home(request):
    dashboard = contexte_tableau_de_bord()
    return render(request, "parc/home.html", {
        "dashboard": dashboard,
    })


@login_required
@require_GET
def api_dashboard_vehicules(request):
    donnees = stats_vehicules()
    mois = request.GET.get("mois")
    if mois:
        annee, num_mois = map(int, mois.split("-"))
        donnees["mensuel"] = serie_mensuelle(annee=annee, mois=num_mois)
    return JsonResponse(donnees)


@login_required
@require_GET
def api_dashboard_parking(request, pk):
    parking = get_object_or_404(Parking, pk=pk, type_parking=Parking.TYPE_UNIVERSEL)
    donnees = stats_parking_universel(parking)
    mois = request.GET.get("mois")
    if mois:
        annee, num_mois = map(int, mois.split("-"))
        donnees["mensuel"] = serie_mensuelle(
            parking_id=parking.pk, annee=annee, mois=num_mois
        )
    return JsonResponse(donnees)


@login_required
@require_GET
def api_vehicules_recherche(request):
    return JsonResponse({"vehicules": liste_vehicules_recherche()})


@login_required
@require_GET
def api_dashboard_vehicule(request, pk):
    vehicule = get_object_or_404(Vehicule, pk=pk, actif=True)
    periode = request.GET.get("periode", "jour")
    mot_cle = request.GET.get("q", "")
    return JsonResponse(contexte_dashboard_vehicule(vehicule, periode=periode, mot_cle=mot_cle))


# -------------------- VEHICULES --------------------
@login_required
def vehicule_liste(request):
    vehicules = Vehicule.objects.select_related("personnel").prefetch_related("chauffeurs").order_by("id")
    alertes = alertes_vehicule_actives(request)
    personnel_alerte = None
    if alertes:
        personnel_alerte = Personnel.objects.filter(pk=alertes[0]).first()
    return render(request, "parc/vehicule.html", {
        "vehicules": vehicules,
        "mode_alerte_vehicule": bool(alertes),
        "personnel_alerte": personnel_alerte,
        "liste_titre": "Liste des véhicules",
        **contexte_liste(request, "vehicules", vehicules),
    })


@login_required
def vehicule_creer(request):
    alertes = set(alertes_vehicule_actives(request))
    personnel_verrouille = None
    personnel_pk = request.GET.get("personnel")
    if personnel_pk:
        try:
            pk = int(personnel_pk)
            if not alertes or pk in alertes:
                personnel_verrouille = pk
        except (TypeError, ValueError):
            pass
    elif alertes:
        personnel_verrouille = sorted(alertes)[0]

    if request.method == "POST":
        form = VehiculeForm(request.POST, personnel_verrouille=personnel_verrouille)
        if form.is_valid():
            vehicule = form.save()
            resoudre_alerte_vehicule(request, vehicule.personnel_id)
            messages.success(request, "Véhicule créé avec succès.")
            return redirect_liste(request, "vehicule_liste", "vehicules", "ajout")
    else:
        form = VehiculeForm(personnel_verrouille=personnel_verrouille)

    return render(request, "parc/vehicule.html", {
        "form": form,
        "titre": "Ajouter un véhicule",
        "mode_alerte_vehicule": bool(alertes),
        "personnel_vehicule_verrouille": personnel_verrouille,
    })


@login_required
def vehicule_modifier(request, pk):
    vehicule = get_object_or_404(Vehicule, pk=pk)
    if request.method == "POST":
        form = VehiculeForm(request.POST, instance=vehicule)
        if form.is_valid():
            form.save()
            messages.success(request, "Véhicule modifié avec succès.")
            return redirect("vehicule_liste")
    else:
        form = VehiculeForm(instance=vehicule)

    return render(request, "parc/vehicule.html", {"form": form, "titre": "Modifier un véhicule"})


@login_required
def vehicule_supprimer(request, pk):
    vehicule = get_object_or_404(Vehicule, pk=pk)
    if request.method == "POST":
        vehicule.delete()
        messages.success(request, "Véhicule supprimé avec succès.")
        return redirect_liste(request, "vehicule_liste", "vehicules", "suppression")

    return render(request, "parc/vehicule.html", {"action": "delete", "vehicule": vehicule})


# -------------------- PERSONNELS --------------------
@login_required
def personnel_liste(request):
    personnels = Personnel.objects.select_related("poste_obj").order_by("nom", "prenom")
    nb_postes_distincts = personnels.values("poste_obj_id").distinct().count()
    return render(request, "parc/personnel.html", {
        "personnels": personnels,
        "nb_postes_distincts": nb_postes_distincts,
        "liste_titre": "Liste du personnel",
        **contexte_liste(request, "personnels", personnels),
    })


@login_required
def personnel_creer(request):
    if request.method == "POST":
        form = PersonnelForm(request.POST)
        if form.is_valid():
            personnel = form.save()
            if personnel_exige_vehicule(personnel):
                enregistrer_alerte_vehicule(request, personnel.pk)
                messages.warning(
                    request,
                    "Ce personnel occupe un poste avec place réservée : "
                    "enregistrez son véhicule pour continuer.",
                )
                return redirect("vehicule_liste")
            messages.success(request, "Personnel créé avec succès.")
            return redirect_liste(request, "personnel_liste", "personnels", "ajout")
    else:
        form = PersonnelForm()

    return render(request, "parc/personnel.html", {"form": form, "titre": "Ajouter un personnel"})


@login_required
def personnel_modifier(request, pk):
    personnel = get_object_or_404(Personnel, pk=pk)
    if request.method == "POST":
        form = PersonnelForm(request.POST, instance=personnel)
        if form.is_valid():
            personnel = form.save()
            if personnel_exige_vehicule(personnel):
                enregistrer_alerte_vehicule(request, personnel.pk)
                messages.warning(
                    request,
                    "Ce personnel occupe un poste avec place réservée : "
                    "enregistrez son véhicule pour continuer.",
                )
                return redirect("vehicule_liste")
            resoudre_alerte_vehicule(request, personnel.pk)
            messages.success(request, "Personnel modifié avec succès.")
            return redirect("personnel_liste")
    else:
        form = PersonnelForm(instance=personnel)

    return render(request, "parc/personnel.html", {"form": form, "titre": "Modifier un personnel"})


@login_required
def personnel_annuler_alerte_vehicule(request, pk):
    """Annule la création d'un personnel encore sans véhicule (poste + place réservée)."""
    alertes = set(alertes_vehicule_actives(request))
    personnel = get_object_or_404(Personnel.objects.select_related("poste_obj"), pk=pk)

    if pk not in alertes or not personnel_exige_vehicule(personnel):
        messages.error(request, "Cette action n'est pas disponible pour ce personnel.")
        return redirect("vehicule_liste")

    if request.method != "POST":
        return redirect("vehicule_liste")

    libelle = f"{personnel.nom} {personnel.prenom}".strip()
    with transaction.atomic():
        _supprimer_personnel_et_dependances(personnel)
    retirer_alerte_vehicule(request, pk)
    messages.success(
        request,
        f"Création du personnel « {libelle} » annulée. Le poste réservé est à nouveau disponible.",
    )
    return redirect("personnel_liste")


def _liberer_et_supprimer_occupations_vehicule(vehicule):
    places_a_verifier = set()
    for occupation in Occupation.objects.filter(vehicule=vehicule):
        if occupation.date_sortie is None:
            places_a_verifier.add(occupation.place_parking_id)
        occupation.delete()
    for place_id in places_a_verifier:
        place = PlaceParking.objects.get(pk=place_id)
        if not place.occupations.filter(date_sortie__isnull=True).exists():
            place.statut = PlaceParking.STATUT_LIBRE
            place.save(update_fields=["statut"])


def _supprimer_personnel_et_dependances(personnel):
    vehicules_titulaire = list(personnel.vehicules.all())
    for vehicule in vehicules_titulaire:
        _liberer_et_supprimer_occupations_vehicule(vehicule)
        vehicule.delete()

    for vehicule in Vehicule.objects.filter(chauffeurs=personnel).distinct():
        vehicule.chauffeurs.remove(personnel)
        if not vehicule.personnel_id and not vehicule.chauffeurs.exists():
            _liberer_et_supprimer_occupations_vehicule(vehicule)
            vehicule.delete()

    compte = Utilisateur.objects.filter(personnel_id=personnel.pk).first()
    if compte:
        compte.delete()

    personnel_pk = personnel.pk
    personnel.delete()
    return vehicules_titulaire, compte is not None, personnel_pk


@login_required
def personnel_supprimer(request, pk):
    personnel = get_object_or_404(Personnel, pk=pk)
    vehicules = list(personnel.vehicules.all())
    compte_utilisateur = Utilisateur.objects.filter(personnel_id=personnel.pk).first()

    if request.method == "POST":
        with transaction.atomic():
            vehicules_supprimes, compte_supprime, personnel_pk = _supprimer_personnel_et_dependances(personnel)
        resoudre_alerte_vehicule(request, personnel_pk)
        if vehicules_supprimes:
            messages.success(
                request,
                f"Personnel supprimé avec succès. "
                f"{len(vehicules_supprimes)} véhicule(s) associé(s) ont également été supprimé(s).",
            )
        elif compte_supprime:
            messages.success(
                request,
                "Personnel supprimé avec succès. Le compte utilisateur associé a également été supprimé.",
            )
        else:
            messages.success(request, "Personnel supprimé avec succès.")
        return redirect_liste(request, "personnel_liste", "personnels", "suppression")

    return render(request, "parc/personnel.html", {
        "action": "delete",
        "personnel": personnel,
        "vehicules_lies": vehicules,
        "compte_utilisateur": compte_utilisateur,
    })


# -------------------- ZONES --------------------
@login_required
def zone_liste(request):
    zones = Zone.objects.all().order_by("-superficie", "nom")
    return render(request, "parc/zone.html", {
        "zones": zones,
        "liste_titre": "Liste des zones",
        **contexte_liste(request, "zones", zones),
    })


@login_required
def zone_creer(request):
    if request.method == "POST":
        form = ZoneForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Zone créée avec succès.")
            return redirect_liste(request, "zone_liste", "zones", "ajout")
    else:
        form = ZoneForm()

    return render(request, "parc/zone.html", {"form": form, "titre": "Ajouter une zone"})


@login_required
def zone_modifier(request, pk):
    zone = get_object_or_404(Zone, pk=pk)
    if request.method == "POST":
        form = ZoneForm(request.POST, instance=zone)
        if form.is_valid():
            form.save()
            messages.success(request, "Zone modifiée avec succès.")
            return redirect("zone_liste")
    else:
        form = ZoneForm(instance=zone)

    return render(request, "parc/zone.html", {"form": form, "titre": "Modifier une zone"})


@login_required
def zone_supprimer(request, pk):
    zone = get_object_or_404(Zone, pk=pk)
    if request.method == "POST":
        zone.delete()
        messages.success(request, "Zone supprimée avec succès.")
        return redirect_liste(request, "zone_liste", "zones", "suppression")

    return render(request, "parc/zone.html", {"action": "delete", "zone": zone})


# -------------------- POSTES --------------------
@login_required
def poste_liste(request):
    postes = Poste.objects.prefetch_related(
        "places_affectees__parking"
    ).order_by("nom")
    return render(request, "parc/poste.html", {
        "postes": postes,
        "liste_titre": "Liste des postes",
        **contexte_liste(request, "postes", postes),
    })


@login_required
def poste_creer(request):
    if request.method == "POST":
        form = PosteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Poste créé avec succès.")
            return redirect_liste(request, "poste_liste", "postes", "ajout")
    else:
        form = PosteForm()

    return render(request, "parc/poste.html", {"form": form, "titre": "Ajouter un poste"})


@login_required
def poste_modifier(request, pk):
    poste = get_object_or_404(Poste, pk=pk)
    if request.method == "POST":
        form = PosteForm(request.POST, instance=poste)
        if form.is_valid():
            form.save()
            vacantes = getattr(form, "places_reservees_vacantes", [])
            if vacantes:
                enregistrer_alertes(request, vacantes)
                messages.warning(
                    request,
                    "Une place réservée est désormais sans poste. "
                    "Affectez-lui un poste pour continuer.",
                )
                return redirect("placeparking_liste")
            messages.success(request, "Poste modifié avec succès.")
            return redirect("poste_liste")
    else:
        form = PosteForm(instance=poste)

    return render(request, "parc/poste.html", {"form": form, "titre": "Modifier un poste"})


@login_required
def poste_supprimer(request, pk):
    poste = get_object_or_404(Poste, pk=pk)
    if request.method == "POST":
        vacantes = list(
            PlaceParking.objects.filter(
                poste_affecte=poste,
                parking__type_parking=Parking.TYPE_RESERVE,
            ).values_list("pk", flat=True)
        )
        poste.delete()
        if vacantes:
            enregistrer_alertes(request, vacantes)
            messages.warning(
                request,
                "La suppression du poste a libéré une place réservée. "
                "Affectez-lui un nouveau poste pour continuer.",
            )
            return redirect("placeparking_liste")
        messages.success(request, "Poste supprimé avec succès.")
        return redirect_liste(request, "poste_liste", "postes", "suppression")

    return render(request, "parc/poste.html", {"action": "delete", "poste": poste})


@login_required
@require_GET
def api_parking_places(request, pk):
    """Liste en lecture seule des places d'un parking (popup liste des parkings)."""
    parking = get_object_or_404(Parking, pk=pk)
    reserve = parking.type_parking == Parking.TYPE_RESERVE
    places = (
        PlaceParking.objects.filter(parking=parking, actif=True)
        .select_related("poste_affecte")
        .order_by("numero")
    )
    return JsonResponse({
        "parking": {
            "id": parking.pk,
            "nom": parking.nom,
            "type_parking": parking.type_parking,
            "reserve": reserve,
        },
        "places": [
            {
                "numero": place.numero,
                "statut": place.statut,
                "statut_libelle": place.get_statut_display(),
                "poste": str(place.poste_affecte) if place.poste_affecte_id else None,
            }
            for place in places
        ],
    })


# -------------------- PARKINGS --------------------
@login_required
def parking_liste(request):
    # Classement hiérarchique (liste des parkings uniquement) :
    # 1. zone BASSA avant les autres zones
    # 1.1. au sein d'une même zone : plus de places d'abord
    # 1.1.1. à zone et capacité égales : ordre alphabétique du nom
    parkings = (
        Parking.objects.select_related("zone")
        .order_by(
            Case(
                When(zone__nom__iexact="bassa", then=Value(0)),
                default=Value(1),
            ),
            "zone__nom",
            "-capacite_total",
            "nom",
        )
    )
    return render(request, "parc/parking.html", {
        "parkings": parkings,
        "liste_titre": "Liste des parkings",
        **contexte_liste(request, "parkings", parkings),
    })


@login_required
def parking_creer(request):
    if request.method == "POST":
        form = ParkingForm(request.POST)
        if form.is_valid():
            parking = form.save()
            if parking.type_parking == Parking.TYPE_UNIVERSEL:
                messages.success(
                    request,
                    f"Parking créé avec succès. {parking.capacite_total} place(s) "
                    f"ont été générées automatiquement.",
                )
            else:
                messages.success(request, "Parking créé avec succès.")
            return redirect_liste(request, "parking_liste", "parkings", "ajout")
    else:
        form = ParkingForm()

    return render(request, "parc/parking.html", {"form": form, "title": "Ajouter un parking"})


@login_required
def parking_modifier(request, pk):
    parking = get_object_or_404(Parking, pk=pk)
    if request.method == "POST":
        form = ParkingForm(request.POST, instance=parking)
        if form.is_valid():
            nb_places_avant = parking.places.count()
            parking = form.save()
            if parking.type_parking == Parking.TYPE_UNIVERSEL:
                ajoutees = parking.places.count() - nb_places_avant
                if ajoutees > 0:
                    messages.success(
                        request,
                        f"Parking modifié avec succès. {ajoutees} nouvelle(s) place(s) "
                        f"ont été ajoutées automatiquement.",
                    )
                else:
                    messages.success(request, "Parking modifié avec succès.")
            else:
                messages.success(request, "Parking modifié avec succès.")
            return redirect("parking_liste")
    else:
        form = ParkingForm(instance=parking)

    return render(request, "parc/parking.html", {"form": form, "title": "Modifier un parking"})


@login_required
def parking_supprimer(request, pk):
    parking = get_object_or_404(Parking, pk=pk)
    if request.method == "POST":
        parking.delete()
        messages.success(request, "Parking supprimé avec succès.")
        return redirect_liste(request, "parking_liste", "parkings", "suppression")

    return render(request, "parc/parking.html", {"action": "delete", "item": parking})


# -------------------- PLACES DE PARKING --------------------
@login_required
def placeparking_liste(request):
    places = PlaceParking.objects.select_related(
        "parking", "poste_affecte"
    ).order_by("parking__nom", "numero")
    places_alerte = set(alertes_actives(request))
    return render(request, "parc/placeparking.html", {
        "places": places,
        "places_alerte": places_alerte,
        "mode_alerte_places": bool(places_alerte),
        "liste_titre": "Liste des places de parking",
        **contexte_liste(request, "places", places),
    })


@login_required
def placeparking_creer(request):
    if request.method == "POST":
        form = PlaceParkingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Place de parking créée avec succès.")
            return redirect_liste(request, "placeparking_liste", "places", "ajout")
    else:
        form = PlaceParkingForm()

    return render(request, "parc/placeparking.html", {"form": form, "title": "Ajouter une place de parking"})


@login_required
def placeparking_modifier(request, pk):
    place = get_object_or_404(PlaceParking, pk=pk)
    if request.method == "POST":
        form = PlaceParkingForm(request.POST, instance=place)
        if form.is_valid():
            form.save()
            resoudre_alerte(request, place.pk)
            if alertes_actives(request):
                messages.warning(
                    request,
                    "Cette place est corrigée. Il reste d'autres places réservées sans poste.",
                )
            else:
                messages.success(request, "Place de parking modifiée avec succès.")
            return redirect("placeparking_liste")
    else:
        form = PlaceParkingForm(instance=place)

    return render(request, "parc/placeparking.html", {
        "form": form,
        "title": "Modifier une place de parking",
        "place_alerte_en_cours": pk in alertes_actives(request),
    })


@login_required
def placeparking_supprimer(request, pk):
    place = get_object_or_404(PlaceParking, pk=pk)
    if request.method == "POST":
        place.delete()
        messages.success(request, "Place de parking supprimée avec succès.")
        return redirect_liste(request, "placeparking_liste", "places", "suppression")

    return render(request, "parc/placeparking.html", {"action": "delete", "item": place})


# -------------------- UTILISATEURS --------------------
@administrateur_requis
def utilisateur_liste(request):
    utilisateurs = Utilisateur.objects.select_related(
        "personnel__poste_obj"
    ).order_by("nom", "prenom")
    nb_postes_distincts = utilisateurs.values("personnel__poste_obj_id").distinct().count()
    return render(request, "parc/utilisateur.html", {
        "utilisateurs": utilisateurs,
        "nb_postes_distincts": nb_postes_distincts,
        "liste_titre": "Liste des utilisateurs",
        **contexte_liste(request, "utilisateurs", utilisateurs),
    })


@administrateur_requis
def utilisateur_creer(request):
    if request.method == "POST":
        form = UtilisateurForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur créé avec succès.")
            return redirect_liste(request, "utilisateur_liste", "utilisateurs", "ajout")
    else:
        form = UtilisateurForm()

    return render(request, "parc/utilisateur.html", {"form": form, "title": "Ajouter un utilisateur"})


@administrateur_requis
def utilisateur_modifier(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if request.method == "POST":
        form = UtilisateurForm(request.POST, instance=utilisateur)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur modifié avec succès.")
            return redirect("utilisateur_liste")
    else:
        form = UtilisateurForm(instance=utilisateur)

    return render(request, "parc/utilisateur.html", {"form": form, "title": "Modifier un utilisateur"})


@administrateur_requis
def utilisateur_supprimer(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if request.method == "POST":
        utilisateur.delete()
        messages.success(request, "Utilisateur supprimé avec succès.")
        return redirect_liste(request, "utilisateur_liste", "utilisateurs", "suppression")

    return render(request, "parc/utilisateur.html", {"action": "delete", "item": utilisateur})


# -------------------- OCCUPATIONS --------------------
@login_required
def occupation_liste(request):
    occupations = Occupation.objects.select_related(
        "vehicule",
        "place_parking",
        "utilisateur",
        "conducteur_entree",
        "conducteur_sortie",
        "conducteur_entree__poste_obj",
        "conducteur_sortie__poste_obj",
    ).order_by("-date_entree")
    return render(request, "parc/occupation.html", {
        "occupations_par_jour": grouper_occupations_par_jour_et_vehicule(occupations),
        "liste_titre": "Liste des occupations",
        **contexte_liste(request, "occupations", occupations),
    })


@login_required
def occupation_creer(request):
    if request.method == "POST":
        form = OccupationEntreeForm(request.POST)
        if form.is_valid():
            occupation = form.save(commit=False)
            if hasattr(request.user, "profil_utilisateur"):
                occupation.utilisateur = request.user.profil_utilisateur
            occupation.full_clean()
            occupation.save()
            messages.success(request, "Entrée enregistrée avec succès.")
            return redirect_liste(request, "occupation_liste", "occupations", "ajout")
    else:
        form = OccupationEntreeForm()

    return render(request, "parc/occupation.html", {
        "form": form,
        "title": "Enregistrer une entrée",
        "conducteurs_vehicules_json": cartographie_conducteurs_vehicules(),
        "places_conducteurs_json": cartographie_places_conducteurs(),
    })


@login_required
def occupation_sortie(request, pk):
    occupation = get_object_or_404(
        Occupation.objects.select_related("vehicule").prefetch_related("vehicule__chauffeurs"),
        pk=pk,
        date_sortie__isnull=True,
    )

    if request.method == "POST":
        form = OccupationSortieForm(occupation, request.POST)
        if form.is_valid():
            occupation.conducteur_sortie = form.cleaned_data["conducteur_sortie"]
            occupation.date_sortie = timezone.now()
            occupation.full_clean()
            occupation.save()
            messages.success(
                request,
                f"Sortie enregistrée. Durée : {occupation.duree}",
            )
            return redirect("occupation_liste")
    else:
        form = OccupationSortieForm(occupation)

    return render(request, "parc/occupation.html", {
        "action": "sortie",
        "item": occupation,
        "form": form,
    })


@login_required
def occupation_modifier(request, pk):
    occupation = get_object_or_404(Occupation, pk=pk)

    if request.method == "POST":
        form = OccupationModifierForm(request.POST, instance=occupation)
    else:
        form = OccupationModifierForm(instance=occupation)

    if request.method == "POST":
        if form.is_valid():
            occ = form.save(commit=False)
            if hasattr(request.user, "profil_utilisateur"):
                occ.utilisateur = request.user.profil_utilisateur
            occ.full_clean()
            occ.save()
            messages.success(request, "Occupation modifiée avec succès.")
            return redirect("occupation_liste")

    return render(request, "parc/occupation.html", {
        "form": form,
        "title": "Modifier une occupation",
        "conducteurs_vehicules_json": cartographie_conducteurs_vehicules(),
        "places_conducteurs_json": cartographie_places_conducteurs(),
    })


@login_required
def occupation_supprimer(request, pk):
    occupation = get_object_or_404(Occupation, pk=pk)
    if request.method == "POST":
        place = occupation.place_parking
        etait_active = occupation.date_sortie is None
        occupation.delete()
        if etait_active:
            autre_active = place.occupations.filter(date_sortie__isnull=True).exists()
            if not autre_active:
                place.statut = PlaceParking.STATUT_LIBRE
                place.save(update_fields=["statut"])
        messages.success(request, "Occupation supprimée avec succès.")
        return redirect_liste(request, "occupation_liste", "occupations", "suppression")

    return render(request, "parc/occupation.html", {"action": "delete", "item": occupation})
