from django import forms
from django.contrib.auth import get_user_model
from .models import (
    Vehicule, Personnel, Zone,
    Poste, Parking, PlaceParking, Utilisateur, Occupation
)


class VehiculeForm(forms.ModelForm):
    class Meta:
        model = Vehicule
        fields = ["immatriculation", "marque", "modele", "couleur", "actif"]
        labels = {
            "immatriculation": "Immatriculation",
            "marque": "Marque",
            "modele": "Modèle",
            "couleur": "Couleur",
            "actif": "Actif",
        }
        widgets = {
            "immatriculation": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: CE 123 AB"}),
            "marque": forms.TextInput(attrs={"class": "form-control"}),
            "modele": forms.TextInput(attrs={"class": "form-control"}),
            "couleur": forms.TextInput(attrs={"class": "form-control"}),
        }


class PersonnelForm(forms.ModelForm):
    class Meta:
        model = Personnel
        fields = ["nom", "prenom", "poste", "email", "actif"]
        labels = {
            "nom": "Nom",
            "prenom": "Prénom",
            "poste": "Poste",
            "email": "Email",
            "actif": "Actif",
        }


class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ["nom", "superficie", "services", "nombre_employes", "actif"]
        labels = {
            "nom": "Nom",
            "superficie": "Superficie (m²)",
            "services": "Services",
            "nombre_employes": "Nombre d'employés",
            "actif": "Actif",
        }


class PosteForm(forms.ModelForm):
    class Meta:
        model = Poste
        fields = ["nom", "description", "actif"]
        labels = {
            "nom": "Nom du poste",
            "description": "Description",
            "actif": "Actif",
        }


class ParkingForm(forms.ModelForm):
    class Meta:
        model = Parking
        fields = ["nom", "adresse", "capacite_total", "actif"]
        labels = {
            "nom": "Nom du parking",
            "adresse": "Adresse",
            "capacite_total": "Capacité totale",
            "actif": "Actif",
        }


class PlaceParkingForm(forms.ModelForm):
    class Meta:
        model = PlaceParking
        fields = ["parking", "numero", "statut", "type_place", "actif"]
        labels = {
            "parking": "Parking",
            "numero": "Numéro",
            "statut": "Statut",
            "type_place": "Type de place",
            "actif": "Actif",
        }


class UtilisateurForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        label="Compte utilisateur"
    )

    class Meta:
        model = Utilisateur
        fields = ["user", "poste", "telephone", "actif"]
        labels = {
            "poste": "Poste",
            "telephone": "Téléphone",
            "actif": "Actif",
        }


class OccupationForm(forms.ModelForm):
    class Meta:
        model = Occupation
        fields = ["place_parking", "utilisateur", "est_active"]
        labels = {
            "place_parking": "Place de parking",
            "utilisateur": "Utilisateur",
            "est_active": "Active",
        }