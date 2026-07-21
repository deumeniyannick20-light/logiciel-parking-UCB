from django import forms
from .models import Vehicule, Personnel, Zone


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