from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Vehicule, Personnel, Zone
from .forms import VehiculeForm, PersonnelForm, ZoneForm

@login_required
def vehicule_liste(request):
    """LIST — afficher la liste des véhicules."""
    vehicules = Vehicule.objects.all().order_by("id")
    return render(request, "parc/vehicule_list.html", {"vehicules": vehicules})


@login_required
def vehicule_creer(request):
    """
    CREATE — Créer un véhicule
    GET  : affiche le formulaire vide
    POST : valide et enregistre en base
    """
    if request.method == "POST":
        form = VehiculeForm(request.POST)
        if form.is_valid():
            form.save()  # INSERT dans MySQL
            messages.success(request, "Véhicule créé avec succès.")
            return redirect("vehicule_liste")
    else:
        form = VehiculeForm()

    return render(request, "parc/vehicule_form.html", {"form": form, "titre": "Ajouter un véhicule"})

@login_required
def vehicule_modifier(request, pk):
    """
    UPDATE — Modifier un véhicule
    GET  : affiche le formulaire pré-rempli
    POST : valide et enregistre en base
    """
    vehicule = Vehicule.objects.get(pk=pk)
    if request.method == "POST":
        form = VehiculeForm(request.POST, instance=vehicule)
        if form.is_valid():
            form.save()  # UPDATE dans MySQL
            messages.success(request, "Véhicule modifié avec succès.")
            return redirect("vehicule_liste")
    else:
        form = VehiculeForm(instance=vehicule)

    return render(request, "parc/vehicule_form.html", {"form": form, "titre": "Modifier un véhicule"})
@login_required
def vehicule_supprimer(request, pk):
    """
    DELETE — Supprimer un véhicule
    GET  : affiche la confirmation de suppression
    POST : supprime le véhicule en base
    """
    vehicule = Vehicule.objects.get(pk=pk)
    if request.method == "POST":
        vehicule.delete()  # DELETE dans MySQL
        messages.success(request, "Véhicule supprimé avec succès.")
        return redirect("vehicule_liste")

    return render(request, "parc/vehicule_confirm_delete.html", {"vehicule": vehicule})










@login_required
def home(request):
    return render(request, "parc/home.html")

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