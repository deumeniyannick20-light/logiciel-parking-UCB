from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from .models import (
    Vehicule, Personnel, Zone,
    Poste, Parking, PlaceParking, Utilisateur, Occupation
)
from .text_format import formater_champ, CHAMPS_NUMERIQUES, formater_nom_poste


def appliquer_asterisques_obligatoires(form, champs_supplementaires=()):
    supplementaires = set(champs_supplementaires or ())
    for name, field in form.fields.items():
        if not (field.required or name in supplementaires):
            continue
        label = field.label
        if not label:
            continue
        label_str = str(label)
        if "champ-obligatoire" in label_str:
            continue
        field.label = mark_safe(
            f'{label_str}&nbsp;<span class="champ-obligatoire" aria-hidden="true">*</span>'
        )


class CasseTexteFormMixin:
    """Applique majuscules aux champs « nom » et majuscule initiale aux autres textes."""

    def clean(self):
        cleaned_data = super().clean()
        for field_name, field in self.fields.items():
            if field_name not in cleaned_data:
                continue
            if field_name in CHAMPS_NUMERIQUES:
                continue
            if isinstance(field.widget, forms.NumberInput):
                continue
            if isinstance(field, (
                forms.ModelChoiceField,
                forms.BooleanField,
                forms.IntegerField,
                forms.DecimalField,
                forms.ChoiceField,
                forms.EmailField,
            )):
                continue
            cleaned_data[field_name] = formater_champ(field_name, cleaned_data[field_name])
        return cleaned_data


class FormulaireMetier(CasseTexteFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configurer_champs()
        appliquer_asterisques_obligatoires(
            self,
            self.champs_obligatoires_supplementaires(),
        )

    def configurer_champs(self):
        """Surcharger pour queryset, required, ordre des champs, etc."""
        pass

    def champs_obligatoires_supplementaires(self):
        return ()


class VehiculeForm(FormulaireMetier):
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
            "immatriculation": forms.TextInput(attrs={"class": "form-control", "style": "text-transform: uppercase;"}),
            "marque": forms.TextInput(attrs={"class": "form-control"}),
            "modele": forms.TextInput(attrs={"class": "form-control"}),
            "couleur": forms.TextInput(attrs={"class": "form-control"}),
            "personnel": forms.Select(attrs={"class": "form-control"}),
            "chauffeur": forms.Select(attrs={"class": "form-control"}),
        }


class PersonnelForm(FormulaireMetier):
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
            "nom": forms.TextInput(attrs={"class": "form-control", "style": "text-transform: uppercase;"}),
            "prenom": forms.TextInput(attrs={"class": "form-control"}),
            "poste_obj": forms.Select(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class ZoneForm(FormulaireMetier):
    class Meta:
        model = Zone
        fields = ["nom", "superficie", "actif"]
        labels = {
            "nom": "Nom",
            "superficie": "Superficie (m²)",
            "actif": "Actif",
        }
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control", "style": "text-transform: uppercase;"}),
            "superficie": forms.NumberInput(attrs={"class": "form-control"}),
        }


class PosteForm(FormulaireMetier):
    place_parking_affectee = forms.ModelChoiceField(
        label="Place de parking affectée",
        queryset=PlaceParking.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

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

    def configurer_champs(self):
        places = PlaceParking.objects.filter(
            actif=True,
            parking__type_parking=Parking.TYPE_RESERVE,
        ).select_related("parking").order_by("parking__nom", "numero")
        if self.instance.pk:
            places = places.filter(
                Q(poste_affecte__isnull=True) | Q(poste_affecte=self.instance)
            )
            place_actuelle = self.instance.places_affectees.first()
            if place_actuelle:
                self.fields["place_parking_affectee"].initial = place_actuelle
        else:
            places = places.filter(poste_affecte__isnull=True)
        self.fields["place_parking_affectee"].queryset = places
        self.fields["place_parking_affectee"].empty_label = "— Aucune —"
        self.fields["place_parking_affectee"].label_from_instance = (
            lambda obj: f"{obj.parking.nom} — Place N°{obj.numero}"
        )
        self.order_fields(["nom", "description", "place_parking_affectee", "actif"])

    def clean(self):
        cleaned_data = super().clean()
        nom = cleaned_data.get("nom")
        if nom:
            cleaned_data["nom"] = formater_nom_poste(nom, False)
        return cleaned_data

    def clean_place_parking_affectee(self):
        place = self.cleaned_data.get("place_parking_affectee")
        if not place:
            return place
        if place.parking.type_parking != Parking.TYPE_RESERVE:
            raise ValidationError(
                "Seules les places de parking privé peuvent être affectées à un poste."
            )
        if place.poste_affecte_id and place.poste_affecte_id != self.instance.pk:
            raise ValidationError("Cette place est déjà affectée à un autre poste.")
        return place

    def save(self, commit=True):
        poste = super().save(commit=commit)
        if not commit:
            return poste
        place = self.cleaned_data.get("place_parking_affectee")
        PlaceParking.objects.filter(poste_affecte=poste).exclude(
            pk=place.pk if place else None
        ).update(poste_affecte=None)
        if place:
            place.poste_affecte = poste
            place.save(update_fields=["poste_affecte"])
        return poste


class ParkingForm(FormulaireMetier):
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
            "nom": forms.TextInput(attrs={"class": "form-control", "style": "text-transform: uppercase;"}),
            "zone": forms.Select(attrs={"class": "form-control"}),
            "type_parking": forms.Select(attrs={"class": "form-control"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
            "capacite_total": forms.NumberInput(attrs={"class": "form-control"}),
        }


class PlaceParkingForm(FormulaireMetier):
    class Meta:
        model = PlaceParking
        fields = ["parking", "numero", "poste_affecte", "actif"]
        labels = {
            "parking": "Parking",
            "numero": "Numéro",
            "poste_affecte": "Poste affecté",
            "actif": "Actif",
        }
        widgets = {
            "parking": forms.Select(attrs={"class": "form-control"}),
            "numero": forms.TextInput(attrs={"class": "form-control"}),
            "poste_affecte": forms.Select(attrs={"class": "form-control"}),
        }

    def configurer_champs(self):
        postes = Poste.objects.filter(actif=True)
        if self.instance.pk and self.instance.poste_affecte_id:
            postes = Poste.objects.filter(
                Q(actif=True) | Q(pk=self.instance.poste_affecte_id)
            )
        self.fields["poste_affecte"].queryset = postes.order_by("nom")
        self.fields["poste_affecte"].required = False
        self.fields["poste_affecte"].empty_label = "— Aucun —"


class UtilisateurForm(FormulaireMetier):
    mot_de_passe = forms.CharField(
        label="Mot de passe",
        required=True,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
        help_text="Le mot de passe est obligatoire pour la connexion à l'application.",
    )

    class Meta:
        model = Utilisateur
        fields = [
            "personnel", "email",
            "role", "telephone", "actif",
        ]
        labels = {
            "personnel": "Personnel",
            "email": "Email",
            "role": "Rôle dans l'application",
            "telephone": "Téléphone",
            "actif": "Actif",
        }
        widgets = {
            "personnel": forms.Select(attrs={"class": "form-control", "id": "id_personnel"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
            "role": forms.Select(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
        }

    def configurer_champs(self):
        personnel_deja_lies = Utilisateur.objects.exclude(
            pk=self.instance.pk
        ).values_list("personnel_id", flat=True)
        personnel_ids = list(
            Personnel.objects.filter(actif=True)
            .exclude(pk__in=personnel_deja_lies)
            .values_list("pk", flat=True)
        )
        if self.instance.personnel_id:
            personnel_ids.append(self.instance.personnel_id)
        self.fields["personnel"].queryset = Personnel.objects.filter(
            pk__in=personnel_ids
        ).select_related("poste_obj").order_by("nom", "prenom")
        self.fields["personnel"].required = True
        self.fields["personnel"].empty_label = "— Sélectionner un personnel —"
        self.order_fields([
            "personnel", "email",
            "role", "telephone", "mot_de_passe", "actif",
        ])
        self.fields["email"].required = True

    def clean_personnel(self):
        personnel = self.cleaned_data.get("personnel")
        if not personnel:
            raise ValidationError("Sélectionnez un personnel déjà enregistré.")
        deja_utilise = Utilisateur.objects.filter(personnel=personnel)
        if self.instance.pk:
            deja_utilise = deja_utilise.exclude(pk=self.instance.pk)
        if deja_utilise.exists():
            raise ValidationError("Ce personnel possède déjà un compte utilisateur.")
        return personnel

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise ValidationError("L'email est obligatoire pour la connexion à l'application.")
        return email

    def clean(self):
        cleaned_data = super().clean()

        mot_de_passe = cleaned_data.get("mot_de_passe")
        if not mot_de_passe:
            self.add_error("mot_de_passe", "Le mot de passe est obligatoire.")

        personnel = cleaned_data.get("personnel")
        if personnel:
            cleaned_data["nom"] = personnel.nom
            cleaned_data["prenom"] = personnel.prenom
            if not cleaned_data.get("email") and personnel.email:
                cleaned_data["email"] = personnel.email.strip().lower()

        email = cleaned_data.get("email", "").strip().lower()
        if email:
            cleaned_data["identifiant"] = email

        return cleaned_data

    def save(self, commit=True):
        utilisateur = super().save(commit=False)
        personnel = self.cleaned_data["personnel"]
        utilisateur.personnel = personnel
        utilisateur.nom = personnel.nom
        utilisateur.prenom = personnel.prenom
        utilisateur.identifiant = self.cleaned_data["email"]
        User = get_user_model()
        mot_de_passe = self.cleaned_data.get("mot_de_passe")

        if utilisateur.pk and utilisateur.user_id:
            user = utilisateur.user
            user.username = utilisateur.identifiant
            user.first_name = utilisateur.prenom
            user.last_name = utilisateur.nom
            user.email = utilisateur.email
            user.is_active = utilisateur.actif
            user.set_password(mot_de_passe)
            user.save()
        else:
            user = User.objects.create_user(
                username=utilisateur.identifiant,
                email=utilisateur.email,
                password=mot_de_passe,
                first_name=utilisateur.prenom,
                last_name=utilisateur.nom,
                is_active=utilisateur.actif,
            )
            utilisateur.user = user

        if commit:
            utilisateur.save()
        return utilisateur


class OccupationEntreeForm(FormulaireMetier):
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

    def configurer_champs(self):
        self.fields["vehicule"].queryset = Vehicule.objects.filter(actif=True)
        self.fields["place_parking"].queryset = PlaceParking.objects.filter(
            statut=PlaceParking.STATUT_LIBRE,
            actif=True,
        )


class ConnexionEmailForm(AuthenticationForm):
    """Formulaire de connexion : email + mot de passe (design UCB)."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": "ucb-login-input",
            "placeholder": "Email",
            "autocomplete": "email",
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email"
        self.fields["password"].label = "Mot de passe"
        self.fields["password"].widget.attrs.update({
            "class": "ucb-login-input",
            "placeholder": "Mot de passe",
            "autocomplete": "current-password",
        })
        self.error_messages["invalid_login"] = (
            "Email ou mot de passe incorrect, ou compte utilisateur inactif."
        )
        appliquer_asterisques_obligatoires(self)

    def clean_username(self):
        return self.cleaned_data.get("username", "").strip().lower()
