from django import forms
from django.contrib.auth import get_user_model
from .models import (
    Vehicule, Personnel, Zone,
    Poste, Parking, PlaceParking, Utilisateur, Occupation
)


class VehiculeForm(forms.ModelForm):
    class Meta:
        model = Vehicule
        fields = ["immatriculation", "marque", "modele", "couleur", "personnel", "actif"]
        labels = {
            "immatriculation": "Immatriculation",
            "marque": "Marque",
            "modele": "Modèle",
            "couleur": "Couleur",
            "personnel": "Propriétaire (Personnel)",
            "actif": "Actif",
        }
        widgets = {
            "immatriculation": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: CE 123 AB"}),
            "marque": forms.TextInput(attrs={"class": "form-control"}),
            "modele": forms.TextInput(attrs={"class": "form-control"}),
            "couleur": forms.TextInput(attrs={"class": "form-control"}),
            "personnel": forms.Select(attrs={"class": "form-control"}),
        }




class PersonnelForm(forms.ModelForm):
    class Meta:
        model = Personnel
        fields = ["nom", "prenom", "poste_obj", "email", "actif"]
        labels = {
            "nom": "Nom",
            "prenom": "Prénom",
            "poste_obj": "Poste occupé",
            "email": "Email",
            "actif": "Actif",
        }
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "prenom": forms.TextInput(attrs={"class": "form-control"}),
            "poste_obj": forms.Select(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
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
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "superficie": forms.NumberInput(attrs={"class": "form-control"}),
            "services": forms.TextInput(attrs={"class": "form-control"}),
            "nombre_employes": forms.NumberInput(attrs={"class": "form-control"}),
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
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ParkingForm(forms.ModelForm):
    class Meta:
        model = Parking
        fields = ["nom", "zone", "adresse", "capacite_total", "actif"]
        labels = {
            "nom": "Nom du parking",
            "zone": "Zone de rattachement",
            "adresse": "Adresse",
            "capacite_total": "Capacité totale",
            "actif": "Actif",
        }
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "zone": forms.Select(attrs={"class": "form-control"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
            "capacite_total": forms.NumberInput(attrs={"class": "form-control"}),
        }


class PlaceParkingForm(forms.ModelForm):
    class Meta:
        model = PlaceParking
        fields = ["parking", "numero", "statut", "type_place", "poste_affecte", "actif"]
        labels = {
            "parking": "Parking",
            "numero": "Numéro",
            "statut": "Statut",
            "type_place": "Type de place",
            "poste_affecte": "Réservée au poste (Optionnel)",
            "actif": "Actif",
        }
        widgets = {
            "parking": forms.Select(attrs={"class": "form-control"}),
            "numero": forms.TextInput(attrs={"class": "form-control"}),
            "statut": forms.Select(attrs={"class": "form-control"}),
            "type_place": forms.TextInput(attrs={"class": "form-control"}),
            "poste_affecte": forms.Select(attrs={"class": "form-control"}),
        }


class UtilisateurForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        label="Compte utilisateur",
        widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = Utilisateur
        fields = ["user", "poste", "telephone", "actif"]
        labels = {
            "poste": "Poste",
            "telephone": "Téléphone",
            "actif": "Actif",
        }
        widgets = {
            "poste": forms.Select(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
        }


class OccupationForm(forms.ModelForm):
    class Meta:
        model = Occupation
        fields = ["place_parking", "vehicule", "utilisateur", "est_active"]
        labels = {
            "place_parking": "Place de parking",
            "vehicule": "Véhicule",
            "utilisateur": "Enregistré par",
            "est_active": "Occupation active",
        }
        widgets = {
            "place_parking": forms.Select(attrs={"class": "form-control"}),
            "vehicule": forms.Select(attrs={"class": "form-control"}),
            "utilisateur": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtre intelligent : ne propose que les places actuellement libres
        self.fields["place_parking"].queryset = PlaceParking.objects.filter(statut="libre", actif=True)