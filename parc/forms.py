from django import forms
from django.contrib.auth import get_user_model
from .models import (
    Vehicule, Personnel, Zone,
    Poste, Parking, PlaceParking, Utilisateur, Occupation
)


class VehiculeForm(forms.ModelForm):
    class Meta:
        model = Vehicule
        fields = ["immatriculation", "marque", "modele", "couleur", "personnel", "chauffeur", "actif"]
        labels = {
            "immatriculation": "Immatriculation",
            "marque": "Marque",
            "modele": "Modèle",
            "couleur": "Couleur",
            "personnel": "Titulaire (Personnel)",
            "chauffeur": "Chauffeur (optionnel)",
            "actif": "Actif",
        }
        widgets = {
            "immatriculation": forms.TextInput(attrs={"class": "form-control"}),
            "marque": forms.TextInput(attrs={"class": "form-control"}),
            "modele": forms.TextInput(attrs={"class": "form-control"}),
            "couleur": forms.TextInput(attrs={"class": "form-control"}),
            "personnel": forms.Select(attrs={"class": "form-control"}),
            "chauffeur": forms.Select(attrs={"class": "form-control"}),
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
        fields = ["nom", "description", "est_direction", "actif"]
        labels = {
            "nom": "Nom du poste",
            "description": "Description",
            "est_direction": "Poste de direction (DG, DGA, DRH...)",
            "actif": "Actif",
        }
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ParkingForm(forms.ModelForm):
    class Meta:
        model = Parking
        fields = ["nom", "zone", "type_parking", "adresse", "capacite_total", "actif"]
        labels = {
            "nom": "Nom du parking",
            "zone": "Zone de rattachement",
            "type_parking": "Type de parking",
            "adresse": "Adresse",
            "capacite_total": "Capacité totale",
            "actif": "Actif",
        }
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "zone": forms.Select(attrs={"class": "form-control"}),
            "type_parking": forms.Select(attrs={"class": "form-control"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
            "capacite_total": forms.NumberInput(attrs={"class": "form-control"}),
        }

class PlaceParkingForm(forms.ModelForm):
    class Meta:
        model = PlaceParking
        fields = ["parking", "numero", "poste_affecte", "actif"]
        labels = {
            "parking": "Parking",
            "numero": "Numéro",
            "poste_affecte": "Poste affecté (réservé uniquement)",
            "actif": "Actif",
        }
        widgets = {
            "parking": forms.Select(attrs={"class": "form-control"}),
            "numero": forms.TextInput(attrs={"class": "form-control"}),
            "poste_affecte": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ne proposer que les postes de direction pour l'affectation
        self.fields["poste_affecte"].queryset = Poste.objects.filter(
            est_direction=True, actif=True
        )
        self.fields["poste_affecte"].required = False


class UtilisateurForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        label="Compte utilisateur",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Utilisateur
        fields = ["user", "role", "telephone", "actif"]
        labels = {
            "role": "Rôle dans le logiciel",
            "telephone": "Téléphone",
            "actif": "Actif",
        }
        widgets = {
            "role": forms.Select(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
        }


class OccupationEntreeForm(forms.ModelForm):
    class Meta:
        model = Occupation
        fields = ["vehicule", "place_parking", "observation"]
        labels = {
            "vehicule": "Véhicule (immatriculation)",
            "place_parking": "Place de parking",
            "observation": "Observation",
        }
        widgets = {
            "vehicule": forms.Select(attrs={"class": "form-control"}),
            "place_parking": forms.Select(attrs={"class": "form-control"}),
            "observation": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vehicule"].queryset = Vehicule.objects.filter(actif=True)
        self.fields["place_parking"].queryset = PlaceParking.objects.filter(
            statut=PlaceParking.STATUT_LIBRE,
            actif=True,
        )