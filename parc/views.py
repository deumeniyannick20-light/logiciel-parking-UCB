from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import (
    Vehicule, Personnel, Zone,
    Poste, Parking, PlaceParking, Utilisateur, Occupation
)
from .forms import (
    VehiculeForm, PersonnelForm, ZoneForm,
    PosteForm, ParkingForm, PlaceParkingForm, UtilisateurForm, OccupationForm
)


def dashboard(request):
    return render(request, "parc/dashboard.html")


@login_required
def home(request):
    return render(request, "parc/home.html")


# -------------------- VEHICULES --------------------
@login_required
def vehicule_liste(request):
    vehicules = Vehicule.objects.all().order_by("id")
    return render(request, "parc/vehicule_list.html", {"vehicules": vehicules})


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

    return render(request, "parc/vehicule_form.html", {"form": form, "titre": "Ajouter un véhicule"})


@login_required
def vehicule_modifier(request, pk):
    vehicule = Vehicule.objects.get(pk=pk)
    if request.method == "POST":
        form = VehiculeForm(request.POST, instance=vehicule)
        if form.is_valid():
            form.save()
            messages.success(request, "Véhicule modifié avec succès.")
            return redirect("vehicule_liste")
    else:
        form = VehiculeForm(instance=vehicule)

    return render(request, "parc/vehicule_form.html", {"form": form, "titre": "Modifier un véhicule"})


@login_required
def vehicule_supprimer(request, pk):
    vehicule = Vehicule.objects.get(pk=pk)
    if request.method == "POST":
        vehicule.delete()
        messages.success(request, "Véhicule supprimé avec succès.")
        return redirect("vehicule_liste")

    return render(request, "parc/vehicule_confirm_delete.html", {"vehicule": vehicule})


# -------------------- PERSONNELS --------------------
@login_required
def personnel_liste(request):
    personnels = Personnel.objects.all().order_by("nom", "prenom")
    return render(request, "parc/personnel_list.html", {"personnels": personnels})


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

    return render(request, "parc/personnel_form.html", {"form": form, "titre": "Ajouter un personnel"})


@login_required
def personnel_modifier(request, pk):
    personnel = Personnel.objects.get(pk=pk)
    if request.method == "POST":
        form = PersonnelForm(request.POST, instance=personnel)
        if form.is_valid():
            form.save()
            messages.success(request, "Personnel modifié avec succès.")
            return redirect("personnel_liste")
    else:
        form = PersonnelForm(instance=personnel)

    return render(request, "parc/personnel_form.html", {"form": form, "titre": "Modifier un personnel"})


@login_required
def personnel_supprimer(request, pk):
    personnel = Personnel.objects.get(pk=pk)
    if request.method == "POST":
        personnel.delete()
        messages.success(request, "Personnel supprimé avec succès.")
        return redirect("personnel_liste")

    return render(request, "parc/personnel_confirm_delete.html", {"personnel": personnel})


# -------------------- ZONES --------------------
@login_required
def zone_liste(request):
    zones = Zone.objects.all().order_by("nom")
    return render(request, "parc/zone_list.html", {"zones": zones})


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

    return render(request, "parc/zone_form.html", {"form": form, "titre": "Ajouter une zone"})


@login_required
def zone_modifier(request, pk):
    zone = Zone.objects.get(pk=pk)
    if request.method == "POST":
        form = ZoneForm(request.POST, instance=zone)
        if form.is_valid():
            form.save()
            messages.success(request, "Zone modifiée avec succès.")
            return redirect("zone_liste")
    else:
        form = ZoneForm(instance=zone)

    return render(request, "parc/zone_form.html", {"form": form, "titre": "Modifier une zone"})


@login_required
def zone_supprimer(request, pk):
    zone = Zone.objects.get(pk=pk)
    if request.method == "POST":
        zone.delete()
        messages.success(request, "Zone supprimée avec succès.")
        return redirect("zone_liste")

    return render(request, "parc/zone_confirm_delete.html", {"zone": zone})


# -------------------- POSTES --------------------
@login_required
def poste_liste(request):
    postes = Poste.objects.all().order_by("nom")
    return render(request, "parc/poste_list.html", {"postes": postes})
      


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

    return render(request, "parc/poste_form.html", {"form": form, "title": "Ajouter un poste", "list_url": "poste_liste",})


@login_required
def poste_modifier(request, pk):
    poste = Poste.objects.get(pk=pk)
    if request.method == "POST":
        form = PosteForm(request.POST, instance=poste)
        if form.is_valid():
            form.save()
            messages.success(request, "Poste modifié avec succès.")
            return redirect("poste_liste")
    else:
        form = PosteForm(instance=poste)

    return render(request, "parc/poste_form.html", {
        "form": form,
        "title": "Modifier un poste",
        "list_url": "poste_liste",
    })


@login_required
def poste_supprimer(request, pk):
    poste = Poste.objects.get(pk=pk)
    if request.method == "POST":
        poste.delete()
        messages.success(request, "Poste supprimé avec succès.")
        return redirect("poste_liste")

    return render(request, "parc/poste_confirm_delete.html", {
        "item": poste,
        "title": "Supprimer un poste",
        "list_url": "poste_liste",
    })


# -------------------- PARKINGS --------------------
@login_required
def parking_liste(request):
    parkings = Parking.objects.all().order_by("nom")
    return render(request, "parc/parking_list.html", {"parkings": parkings})


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

    return render(request, "parc/parking_form.html", {
        "form": form,
        "title": "Ajouter un parking",
        "list_url": "parking_liste",
    })


@login_required
def parking_modifier(request, pk):
    parking = Parking.objects.get(pk=pk)
    if request.method == "POST":
        form = ParkingForm(request.POST, instance=parking)
        if form.is_valid():
            form.save()
            messages.success(request, "Parking modifié avec succès.")
            return redirect("parking_liste")
    else:
        form = ParkingForm(instance=parking)

    return render(request, "parc/parking_form.html", {
        "form": form,
        "title": "Modifier un parking",
        "list_url": "parking_liste",
    })


@login_required
def parking_supprimer(request, pk):
    parking = Parking.objects.get(pk=pk)
    if request.method == "POST":
        parking.delete()
        messages.success(request, "Parking supprimé avec succès.")
        return redirect("parking_liste")

    return render(request, "parc/parking_confirm_delete.html", {
        "item": parking,
        "title": "Supprimer un parking",
        "list_url": "parking_liste",
    })


# -------------------- PLACES DE PARKING --------------------
@login_required
def placeparking_liste(request):
    places = PlaceParking.objects.all().order_by("parking__nom", "numero")
    return render(request, "parc/placeparking_list.html", {"places": places})


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

    return render(request, "parc/placeparking_form.html", {
        "form": form,
        "title": "Ajouter une place de parking",
        "list_url": "placeparking_liste",
    })


@login_required
def placeparking_modifier(request, pk):
    place = PlaceParking.objects.get(pk=pk)
    if request.method == "POST":
        form = PlaceParkingForm(request.POST, instance=place)
        if form.is_valid():
            form.save()
            messages.success(request, "Place de parking modifiée avec succès.")
            return redirect("placeparking_liste")
    else:
        form = PlaceParkingForm(instance=place)

    return render(request, "parc/placeparking_form.html", {
        "form": form,
        "title": "Modifier une place de parking",
        "list_url": "placeparking_liste",
    })


@login_required
def placeparking_supprimer(request, pk):
    place = PlaceParking.objects.get(pk=pk)
    if request.method == "POST":
        place.delete()
        messages.success(request, "Place de parking supprimée avec succès.")
        return redirect("placeparking_liste")

    return render(request, "parc/placeparking_confirm_delete.html", {
        "item": place,
        "title": "Supprimer une place de parking",
        "list_url": "placeparking_liste",
    })


# -------------------- UTILISATEURS --------------------
@login_required
def utilisateur_liste(request):
    utilisateurs = Utilisateur.objects.all().order_by("user__username")
    return render(request, "parc/utilisateur_list.html", {"utilisateurs": utilisateurs})


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

    return render(request, "parc/utilisateur_form.html", {
        "form": form,
        "title": "Ajouter un utilisateur",
        "list_url": "utilisateur_liste",
    })


@login_required
def utilisateur_modifier(request, pk):
    utilisateur = Utilisateur.objects.get(pk=pk)
    if request.method == "POST":
        form = UtilisateurForm(request.POST, instance=utilisateur)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur modifié avec succès.")
            return redirect("utilisateur_liste")
    else:
        form = UtilisateurForm(instance=utilisateur)

    return render(request, "parc/utilisateur_form.html", {
        "form": form,
        "title": "Modifier un utilisateur",
        "list_url": "utilisateur_liste",
    })


@login_required
def utilisateur_supprimer(request, pk):
    utilisateur = Utilisateur.objects.get(pk=pk)
    if request.method == "POST":
        utilisateur.delete()
        messages.success(request, "Utilisateur supprimé avec succès.")
        return redirect("utilisateur_liste")

    return render(request, "parc/utilisateur_confirm_delete.html", {
        "item": utilisateur,
        "title": "Supprimer un utilisateur",
        "list_url": "utilisateur_liste",
    })


# -------------------- OCCUPATIONS --------------------
# Dans views.py
@login_required
def occupation_liste(request):
    occupations = Occupation.objects.all().order_by("-date_entree")
    return render(request, "parc/occupation_list.html", {
        "occupations": occupations,
    })


@login_required
def occupation_creer(request):
    if request.method == "POST":
        form = OccupationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Occupation créée avec succès.")
            return redirect("occupation_liste")
    else:
        form = OccupationForm()

    return render(request, "parc/occupation_form.html", {
        "form": form,
        "title": "Ajouter une occupation",
        "list_url": "occupation_liste",
    })


@login_required
def occupation_modifier(request, pk):
    occupation = Occupation.objects.get(pk=pk)
    if request.method == "POST":
        form = OccupationForm(request.POST, instance=occupation)
        if form.is_valid():
            form.save()
            messages.success(request, "Occupation modifiée avec succès.")
            return redirect("occupation_liste")
    else:
        form = OccupationForm(instance=occupation)

    return render(request, "parc/occupation_form.html", {
        "form": form,
        "title": "Modifier une occupation",
        "list_url": "occupation_liste",
    })


@login_required
def occupation_supprimer(request, pk):
    occupation = Occupation.objects.get(pk=pk)
    if request.method == "POST":
        occupation.delete()
        messages.success(request, "Occupation supprimée avec succès.")
        return redirect("occupation_liste")

    return render(request, "parc/occupation_confirm_delete.html", {
        "item": occupation,
        "title": "Supprimer une occupation",
        "list_url": "occupation_liste",
    })