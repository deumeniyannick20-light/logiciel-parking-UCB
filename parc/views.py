from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case, Count, Q, Value, When
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
import json

from .models import (
    Vehicule, Personnel, Zone,
    Poste, Parking, PlaceParking, Utilisateur, Occupation
)
from .forms import (
    VehiculeForm, PersonnelForm, ZoneForm,
    PosteForm, ParkingForm, PlaceParkingForm, UtilisateurForm,
    OccupationEntreeForm,
)
from .dashboard_stats import (
    contexte_tableau_de_bord,
    stats_vehicules,
    stats_parking_universel,
    serie_mensuelle,
)
from .place_alerte import alertes_actives, enregistrer_alertes, resoudre_alerte


@login_required
def dashboard(request):
    return render(request, "parc/dashboard.html")


@login_required
def home(request):
    dashboard = contexte_tableau_de_bord()
    return render(request, "parc/home.html", {
        "dashboard": dashboard,
        "dashboard_json": json.dumps(dashboard),
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


# -------------------- VEHICULES --------------------
@login_required
def vehicule_liste(request):
    vehicules = Vehicule.objects.all().order_by("id")
    return render(request, "parc/vehicule.html", {"vehicules": vehicules})


@login_required
def vehicule_creer(request):
    if request.method == "POST":
        form = VehiculeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Véhicule créé avec succès.")
            return redirect("vehicule_liste")
    else:
        form = VehiculeForm()

    return render(request, "parc/vehicule.html", {"form": form, "titre": "Ajouter un véhicule"})


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
        return redirect("vehicule_liste")

    return render(request, "parc/vehicule.html", {"action": "delete", "vehicule": vehicule})


# -------------------- PERSONNELS --------------------
@login_required
def personnel_liste(request):
    personnels = Personnel.objects.all().order_by("nom", "prenom")
    return render(request, "parc/personnel.html", {"personnels": personnels})


@login_required
def personnel_creer(request):
    if request.method == "POST":
        form = PersonnelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Personnel créé avec succès.")
            return redirect("personnel_liste")
    else:
        form = PersonnelForm()

    return render(request, "parc/personnel.html", {"form": form, "titre": "Ajouter un personnel"})


@login_required
def personnel_modifier(request, pk):
    personnel = get_object_or_404(Personnel, pk=pk)
    if request.method == "POST":
        form = PersonnelForm(request.POST, instance=personnel)
        if form.is_valid():
            form.save()
            messages.success(request, "Personnel modifié avec succès.")
            return redirect("personnel_liste")
    else:
        form = PersonnelForm(instance=personnel)

    return render(request, "parc/personnel.html", {"form": form, "titre": "Modifier un personnel"})


@login_required
def personnel_supprimer(request, pk):
    personnel = get_object_or_404(Personnel, pk=pk)
    if request.method == "POST":
        personnel.delete()
        messages.success(request, "Personnel supprimé avec succès.")
        return redirect("personnel_liste")

    return render(request, "parc/personnel.html", {"action": "delete", "personnel": personnel})


# -------------------- ZONES --------------------
@login_required
def zone_liste(request):
    zones = Zone.objects.all().order_by("nom")
    return render(request, "parc/zone.html", {"zones": zones})


@login_required
def zone_creer(request):
    if request.method == "POST":
        form = ZoneForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Zone créée avec succès.")
            return redirect("zone_liste")
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
        return redirect("zone_liste")

    return render(request, "parc/zone.html", {"action": "delete", "zone": zone})


# -------------------- POSTES --------------------
@login_required
def poste_liste(request):
    postes = Poste.objects.prefetch_related(
        "places_affectees__parking"
    ).order_by("nom")
    return render(request, "parc/poste.html", {"postes": postes})


@login_required
def poste_creer(request):
    if request.method == "POST":
        form = PosteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Poste créé avec succès.")
            return redirect("poste_liste")
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
        return redirect("poste_liste")

    return render(request, "parc/poste.html", {"action": "delete", "poste": poste})


# -------------------- PARKINGS --------------------
@login_required
def parking_liste(request):
    parkings = (
        Parking.objects.select_related("zone")
        .annotate(nb_places=Count("places"))
        .order_by(
            Case(
                When(zone__nom__iexact="bassa", then=Value(0)),
                default=Value(1),
            ),
            "-nb_places",
            Case(
                When(type_parking=Parking.TYPE_UNIVERSEL, then=Value(0)),
                When(type_parking=Parking.TYPE_RESERVE, then=Value(1)),
                default=Value(2),
            ),
            "nom",
        )
    )
    return render(request, "parc/parking.html", {"parkings": parkings})


@login_required
def parking_creer(request):
    if request.method == "POST":
        form = ParkingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Parking créé avec succès.")
            return redirect("parking_liste")
    else:
        form = ParkingForm()

    return render(request, "parc/parking.html", {"form": form, "title": "Ajouter un parking"})


@login_required
def parking_modifier(request, pk):
    parking = get_object_or_404(Parking, pk=pk)
    if request.method == "POST":
        form = ParkingForm(request.POST, instance=parking)
        if form.is_valid():
            form.save()
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
        return redirect("parking_liste")

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
    })


@login_required
def placeparking_creer(request):
    if request.method == "POST":
        form = PlaceParkingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Place de parking créée avec succès.")
            return redirect("placeparking_liste")
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
        return redirect("placeparking_liste")

    return render(request, "parc/placeparking.html", {"action": "delete", "item": place})


# -------------------- UTILISATEURS --------------------
@login_required
def utilisateur_liste(request):
    utilisateurs = Utilisateur.objects.select_related(
        "personnel__poste_obj"
    ).order_by("nom", "prenom")
    return render(request, "parc/utilisateur.html", {"utilisateurs": utilisateurs})


@login_required
def utilisateur_creer(request):
    if request.method == "POST":
        form = UtilisateurForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur créé avec succès.")
            return redirect("utilisateur_liste")
    else:
        form = UtilisateurForm()

    return render(request, "parc/utilisateur.html", {"form": form, "title": "Ajouter un utilisateur"})


@login_required
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


@login_required
def utilisateur_supprimer(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if request.method == "POST":
        utilisateur.delete()
        messages.success(request, "Utilisateur supprimé avec succès.")
        return redirect("utilisateur_liste")

    return render(request, "parc/utilisateur.html", {"action": "delete", "item": utilisateur})


# -------------------- OCCUPATIONS --------------------
@login_required
def occupation_liste(request):
    occupations = Occupation.objects.select_related(
        "vehicule", "place_parking", "utilisateur"
    ).order_by("-date_entree")
    return render(request, "parc/occupation.html", {"occupations": occupations})


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
            return redirect("occupation_liste")
    else:
        form = OccupationEntreeForm()

    return render(request, "parc/occupation.html", {
        "form": form,
        "title": "Enregistrer une entrée",
    })


@login_required
def occupation_sortie(request, pk):
    occupation = get_object_or_404(Occupation, pk=pk, date_sortie__isnull=True)

    if request.method == "POST":
        occupation.date_sortie = timezone.now()
        occupation.full_clean()
        occupation.save()
        messages.success(
            request,
            f"Sortie enregistrée. Durée : {occupation.duree}",
        )
        return redirect("occupation_liste")

    return render(request, "parc/occupation.html", {
        "action": "sortie",
        "item": occupation,
    })


@login_required
def occupation_modifier(request, pk):
    occupation = get_object_or_404(Occupation, pk=pk)

    if request.method == "POST":
        form = OccupationEntreeForm(request.POST, instance=occupation)
    else:
        form = OccupationEntreeForm(instance=occupation)

    form.fields["place_parking"].queryset = PlaceParking.objects.filter(
        Q(statut=PlaceParking.STATUT_LIBRE, actif=True) |
        Q(pk=occupation.place_parking_id)
    )

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
        return redirect("occupation_liste")

    return render(request, "parc/occupation.html", {"action": "delete", "item": occupation})
