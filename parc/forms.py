from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
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
    def __init__(self, *args, personnel_verrouille=None, **kwargs):
        self.personnel_verrouille = personnel_verrouille
        super().__init__(*args, **kwargs)

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

    def configurer_champs(self):
        if self.personnel_verrouille:
            self.fields["personnel"].initial = self.personnel_verrouille
            self.fields["personnel"].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        if self.personnel_verrouille:
            cleaned_data["personnel"] = Personnel.objects.get(pk=self.personnel_verrouille)
        return cleaned_data


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
            "email": forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
        }

    def configurer_champs(self):
        self.fields["email"].required = True

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("L'email est obligatoire.")
        return email


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
            "nom": "Poste",
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
        place = cleaned_data.get("place_parking_affectee")
        if nom:
            cleaned_data["nom"] = formater_nom_poste(nom, bool(place))
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
        self.places_reservees_vacantes = []
        if not commit:
            return poste
        place = self.cleaned_data.get("place_parking_affectee")
        vacantes = PlaceParking.objects.filter(
            poste_affecte=poste,
            parking__type_parking=Parking.TYPE_RESERVE,
        ).exclude(pk=place.pk if place else None)
        self.places_reservees_vacantes = list(vacantes.values_list("pk", flat=True))
        PlaceParking.objects.filter(poste_affecte=poste).exclude(
            pk=place.pk if place else None
        ).update(poste_affecte=None)
        if place:
            place.poste_affecte = poste
            place.save(update_fields=["poste_affecte"])
        poste.synchroniser_casse_nom()
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
            "capacite_total": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
        }

    def clean_capacite_total(self):
        capacite = self.cleaned_data.get("capacite_total")
        if capacite is not None and capacite < 1:
            raise ValidationError("Un parking doit avoir au moins une place.")
        return capacite


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
        postes_pris = PlaceParking.objects.filter(
            poste_affecte__isnull=False,
            parking__type_parking=Parking.TYPE_RESERVE,
        )
        if self.instance.pk:
            postes_pris = postes_pris.exclude(pk=self.instance.pk)
        ids_pris = list(postes_pris.values_list("poste_affecte_id", flat=True))
        filtre = Q(actif=True) & ~Q(pk__in=ids_pris)
        if self.instance.pk and self.instance.poste_affecte_id:
            filtre = filtre | Q(pk=self.instance.poste_affecte_id)
        self.fields["poste_affecte"].queryset = (
            Poste.objects.filter(filtre).distinct().order_by("nom")
        )
        self.fields["poste_affecte"].required = False
        self.fields["poste_affecte"].empty_label = "— Aucun —"

    def clean(self):
        cleaned_data = super().clean()
        parking = cleaned_data.get("parking")
        poste = cleaned_data.get("poste_affecte")
        if not parking:
            return cleaned_data
        if parking.type_parking == Parking.TYPE_UNIVERSEL:
            cleaned_data["poste_affecte"] = None
            return cleaned_data
        if parking.type_parking == Parking.TYPE_RESERVE and not poste:
            raise ValidationError(
                {"poste_affecte": "Une place réservée doit être affectée à un poste."}
            )
        if poste:
            doublon = PlaceParking.objects.filter(
                poste_affecte=poste,
                parking__type_parking=Parking.TYPE_RESERVE,
            )
            if self.instance.pk:
                doublon = doublon.exclude(pk=self.instance.pk)
            if doublon.exists():
                autre = doublon.select_related("parking").first()
                raise ValidationError({
                    "poste_affecte": (
                        f"Le poste « {poste} » est déjà affecté à la place "
                        f"N°{autre.numero} ({autre.parking.nom})."
                    ),
                })
        return cleaned_data


class UtilisateurForm(FormulaireMetier):
    mot_de_passe = forms.CharField(
        label="Mot de passe",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
        help_text="Obligatoire à la création. Laissez vide pour conserver le mot de passe actuel.",
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
        if self.instance.pk:
            self.fields["mot_de_passe"].required = False
            self.fields["mot_de_passe"].help_text = (
                "Laissez vide pour conserver le mot de passe actuel."
            )
        else:
            self.fields["mot_de_passe"].required = True
            self.fields["mot_de_passe"].help_text = (
                "Le mot de passe est obligatoire pour la connexion à l'application."
            )

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
        deja_utilise = Utilisateur.objects.filter(email__iexact=email)
        if self.instance.pk:
            deja_utilise = deja_utilise.exclude(pk=self.instance.pk)
        if deja_utilise.exists():
            raise ValidationError("Cet email est déjà utilisé par un autre compte.")
        return email

    def clean(self):
        cleaned_data = super().clean()

        mot_de_passe = cleaned_data.get("mot_de_passe")
        if not self.instance.pk and not mot_de_passe:
            self.add_error("mot_de_passe", "Le mot de passe est obligatoire à la création.")

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
            if mot_de_passe:
                user.set_password(mot_de_passe)
            user.save()
        else:
            user = User(
                username=utilisateur.identifiant,
                email=utilisateur.email,
                first_name=utilisateur.prenom,
                last_name=utilisateur.nom,
                is_active=utilisateur.actif,
            )
            user.set_password(mot_de_passe)
            user.save()
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
            "class": "ucb-login-input ucb-password-input",
            "placeholder": "Mot de passe",
            "autocomplete": "current-password",
        })
        self.error_messages["invalid_login"] = (
            "Email ou mot de passe incorrect, ou compte utilisateur inactif."
        )
        appliquer_asterisques_obligatoires(self)

    def clean_username(self):
        return self.cleaned_data.get("username", "").strip().lower()


class ReinitialisationMotDePasseForm(PasswordResetForm):
    """Réinitialisation du mot de passe via l'email du profil Utilisateur."""

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": "ucb-login-input",
            "placeholder": "Votre adresse email",
            "autocomplete": "email",
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        appliquer_asterisques_obligatoires(self)

    def clean_email(self):
        return self.cleaned_data.get("email", "").strip().lower()

    def get_users(self, email):
        try:
            utilisateur = Utilisateur.objects.select_related("user").get(
                email__iexact=email,
                actif=True,
            )
        except Utilisateur.DoesNotExist:
            return

        user = utilisateur.user
        if user.is_active and user.has_usable_password():
            yield user


class NouveauMotDePasseForm(SetPasswordForm):
    """Choix d'un nouveau mot de passe après réinitialisation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "ucb-login-input ucb-password-input",
                "autocomplete": "new-password",
            })
            field.help_text = ""
        self.fields["new_password1"].label = "Nouveau mot de passe"
        self.fields["new_password2"].label = "Confirmer le mot de passe"
        appliquer_asterisques_obligatoires(self)

    def clean_new_password1(self):
        password1 = self.cleaned_data.get("new_password1")
        if not password1:
            raise ValidationError("Ce champ est obligatoire.")
        return password1

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if not password2:
            raise ValidationError("Ce champ est obligatoire.")
        if password1 != password2:
            raise ValidationError("Les deux mots de passe ne correspondent pas.")
        return password2


class ChangementMotDePasseForm(PasswordChangeForm):
    """Changement de mot de passe pour un utilisateur connecté."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({
                "class": "form-control ucb-password-input",
                "autocomplete": "current-password" if name == "old_password" else "new-password",
            })
            field.help_text = ""
        self.fields["old_password"].label = "Mot de passe actuel"
        self.fields["new_password1"].label = "Nouveau mot de passe"
        self.fields["new_password2"].label = "Confirmer le nouveau mot de passe"
        appliquer_asterisques_obligatoires(self)

    def clean_new_password1(self):
        password1 = self.cleaned_data.get("new_password1")
        if not password1:
            raise ValidationError("Ce champ est obligatoire.")
        return password1

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if not password2:
            raise ValidationError("Ce champ est obligatoire.")
        if password1 != password2:
            raise ValidationError("Les deux mots de passe ne correspondent pas.")
        return password2
