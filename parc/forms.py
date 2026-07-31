from django import forms
import json
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
from .vehicule_conducteurs import conducteurs_autorises_pour
from .occupation_places import (
    cartographie_places_conducteurs,
    place_autorisee_pour_conducteur,
    queryset_places_pour_conducteur,
)
from .poste_chauffeur import personnel_chauffeurs_disponibles, personnel_est_chauffeur
from .personnel_postes import (
    message_poste_indisponible,
    personnel_peut_occuper_poste,
    queryset_postes_pour_personnel,
)
from .personnel_email import proposer_email_ucb


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
        fields = ["immatriculation", "marque", "modele", "couleur", "personnel", "chauffeurs", "actif"]
        labels = {
            "immatriculation": "Immatriculation",
            "marque": "Marque",
            "modele": "Modèle",
            "couleur": "Couleur",
            "personnel": "Titulaire (optionnel)",
            "chauffeurs": "Chauffeurs",
            "actif": "Actif",
        }
        widgets = {
            "immatriculation": forms.TextInput(attrs={"class": "form-control", "style": "text-transform: uppercase;"}),
            "marque": forms.TextInput(attrs={"class": "form-control"}),
            "modele": forms.TextInput(attrs={"class": "form-control"}),
            "couleur": forms.TextInput(attrs={"class": "form-control"}),
            "personnel": forms.Select(attrs={"class": "form-control", "id": "id_personnel"}),
            "chauffeurs": forms.CheckboxSelectMultiple(
                attrs={"class": "ucb-chauffeurs-checkboxes", "id": "id_chauffeurs"},
            ),
        }

    def configurer_champs(self):
        self.fields["personnel"].required = False
        self.fields["personnel"].empty_label = "— Aucun titulaire —"
        self.fields["couleur"].required = True
        if self.personnel_verrouille:
            self.fields["personnel"].initial = self.personnel_verrouille
            self.fields["personnel"].disabled = True
        self._maj_chauffeurs()

    def clean_couleur(self):
        couleur = (self.cleaned_data.get("couleur") or "").strip()
        if not couleur:
            raise ValidationError("La couleur est obligatoire.")
        return couleur

    def _titulaire_courant(self):
        if self.personnel_verrouille:
            return Personnel.objects.filter(pk=self.personnel_verrouille).first()
        if self.is_bound:
            personnel_id = self.data.get("personnel")
            if personnel_id:
                return Personnel.objects.filter(pk=personnel_id).first()
        if self.instance and self.instance.pk and self.instance.personnel_id:
            return self.instance.personnel
        return None

    def _maj_chauffeurs(self):
        titulaire = self._titulaire_courant()
        exclure_pk = titulaire.pk if titulaire else None
        queryset = personnel_chauffeurs_disponibles(exclure_pk=exclure_pk)
        if titulaire:
            self.fields["chauffeurs"].required = False
            self.fields["chauffeurs"].label = "Chauffeurs (optionnel)"
        else:
            self.fields["chauffeurs"].required = True
            self.fields["chauffeurs"].label = "Chauffeurs"
        self.fields["chauffeurs"].queryset = queryset

    def clean(self):
        cleaned_data = super().clean()
        if self.personnel_verrouille:
            cleaned_data["personnel"] = Personnel.objects.get(pk=self.personnel_verrouille)

        titulaire = cleaned_data.get("personnel")
        chauffeurs = cleaned_data.get("chauffeurs")
        chauffeur_list = list(chauffeurs) if chauffeurs is not None else []

        if titulaire:
            chauffeur_list = [
                chauffeur for chauffeur in chauffeur_list
                if chauffeur.pk != titulaire.pk
            ]
            cleaned_data["chauffeurs"] = chauffeur_list
        elif not chauffeur_list:
            raise ValidationError(
                "Indiquez un titulaire ou au moins un chauffeur pour ce véhicule."
            )

        for chauffeur in chauffeur_list:
            if not personnel_est_chauffeur(chauffeur):
                raise ValidationError(
                    "Seuls les membres du personnel au poste Chauffeur peuvent être "
                    "affectés comme chauffeurs du véhicule."
                )

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
            "nom": forms.TextInput(attrs={"class": "form-control", "style": "text-transform: uppercase;", "id": "id_nom"}),
            "prenom": forms.TextInput(attrs={"class": "form-control", "id": "id_prenom"}),
            "poste_obj": forms.Select(attrs={"class": "form-control", "id": "id_poste_obj"}),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "id": "id_email",
                "autocomplete": "email",
                "style": "text-transform: lowercase;",
            }),
        }

    def configurer_champs(self):
        self.fields["email"].required = True
        self.fields["poste_obj"].queryset = queryset_postes_pour_personnel(
            self.instance if self.instance.pk else None
        )
        self.fields["poste_obj"].required = True
        self.fields["poste_obj"].empty_label = "— Sélectionner un poste —"
        self.fields["poste_obj"].help_text = ""
        self.fields["email"].help_text = ""

    def clean_poste_obj(self):
        poste = self.cleaned_data.get("poste_obj")
        if not poste:
            raise ValidationError("Le poste occupé est obligatoire.")
        personnel = self.instance if self.instance.pk else None
        if not personnel_peut_occuper_poste(poste, personnel=personnel):
            raise ValidationError(message_poste_indisponible())
        return poste

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email and not self.instance.pk:
            nom = self.cleaned_data.get("nom")
            prenom = self.cleaned_data.get("prenom")
            poste = self.cleaned_data.get("poste_obj")
            if nom and prenom and poste:
                email = proposer_email_ucb(nom, prenom)
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
        fields = ["nom", "description", "est_chauffeur", "actif"]
        labels = {
            "nom": "Poste",
            "description": "Description",
            "est_chauffeur": "Poste de chauffeur",
            "actif": "Actif",
        }
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def configurer_champs(self):
        self.fields["est_chauffeur"].help_text = (
            "À cocher uniquement pour le poste Chauffeur (personnel affectable aux véhicules)."
        )
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
        self.order_fields(["nom", "description", "est_chauffeur", "place_parking_affectee", "actif"])

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

    def clean(self):
        cleaned_data = super().clean()
        capacite = cleaned_data.get("capacite_total")
        type_parking = cleaned_data.get("type_parking")
        if (
            self.instance.pk
            and capacite is not None
            and type_parking == Parking.TYPE_UNIVERSEL
        ):
            nb_places = PlaceParking.objects.filter(parking_id=self.instance.pk).count()
            if capacite < nb_places:
                raise ValidationError({
                    "capacite_total": (
                        f"La capacité ne peut pas être inférieure au nombre de places "
                        f"déjà enregistrées ({nb_places}). Supprimez d'abord les places "
                        f"en trop dans « Gérer les places »."
                    ),
                })
        return cleaned_data


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
        self.fields["parking"].queryset = Parking.objects.filter(actif=True).order_by("nom")
        self.types_parking = json.dumps({
            str(pk): type_parking
            for pk, type_parking in Parking.objects.values_list("pk", "type_parking")
        })

    def clean(self):
        cleaned_data = super().clean()
        parking = cleaned_data.get("parking")
        poste = cleaned_data.get("poste_affecte")
        if not parking:
            return cleaned_data
        if parking.type_parking == Parking.TYPE_UNIVERSEL:
            if poste:
                raise ValidationError({
                    "poste_affecte": (
                        "Un parking universel ne peut pas avoir de poste affecté. "
                        "Sélectionnez « — Aucun — » ou choisissez un parking réservé."
                    ),
                })
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
        fields = ["vehicule", "conducteur_entree", "place_parking", "observation"]
        labels = {
            "vehicule": "Véhicule (immatriculation)",
            "conducteur_entree": "Conducteur",
            "place_parking": "Place de parking",
            "observation": "Observation",
        }
        widgets = {
            "vehicule": forms.Select(attrs={"class": "form-control", "id": "id_vehicule"}),
            "place_parking": forms.Select(attrs={"class": "form-control", "id": "id_place_parking"}),
            "conducteur_entree": forms.Select(attrs={"class": "form-control", "id": "id_conducteur_entree"}),
            "observation": forms.TextInput(attrs={"class": "form-control"}),
        }

    def configurer_champs(self):
        occupations_actives = Occupation.objects.filter(date_sortie__isnull=True)
        if self.instance and self.instance.pk:
            occupations_actives = occupations_actives.exclude(pk=self.instance.pk)

        vehicules_gares = occupations_actives.values_list("vehicule_id", flat=True)
        self.fields["vehicule"].queryset = Vehicule.objects.filter(
            actif=True,
        ).exclude(pk__in=vehicules_gares).select_related("personnel").prefetch_related("chauffeurs")
        self.fields["conducteur_entree"].required = True
        self.fields["conducteur_entree"].empty_label = "— Sélectionnez d'abord un véhicule —"
        self.fields["place_parking"].queryset = PlaceParking.objects.none()
        self.fields["place_parking"].empty_label = "— Sélectionnez d'abord le conducteur —"
        self._maj_conducteurs()
        self._maj_places()

    def _place_courante_id(self):
        if self.instance and self.instance.pk and self.instance.place_parking_id:
            return self.instance.place_parking_id
        return None

    def _vehicule_courant(self):
        vehicule = None
        if self.is_bound:
            vehicule_id = self.data.get("vehicule")
            if vehicule_id:
                vehicule = Vehicule.objects.filter(pk=vehicule_id).select_related(
                    "personnel"
                ).prefetch_related("chauffeurs").first()
        elif self.instance and self.instance.vehicule_id:
            vehicule = self.instance.vehicule
        return vehicule

    def _conducteur_courant(self):
        conducteur = None
        if self.is_bound:
            conducteur_id = self.data.get("conducteur_entree")
            if conducteur_id:
                conducteur = Personnel.objects.select_related("poste_obj").filter(
                    pk=conducteur_id
                ).first()
        elif self.instance and self.instance.conducteur_entree_id:
            conducteur = self.instance.conducteur_entree
        return conducteur

    def _maj_conducteurs(self):
        vehicule = self._vehicule_courant()
        self.fields["conducteur_entree"].queryset = conducteurs_autorises_pour(vehicule)
        if vehicule:
            self.fields["conducteur_entree"].empty_label = "— Sélectionner le conducteur —"
        else:
            self.fields["conducteur_entree"].empty_label = "— Sélectionnez d'abord un véhicule —"

    def _maj_places(self):
        conducteur = self._conducteur_courant()
        qs, place_auto = queryset_places_pour_conducteur(
            conducteur,
            place_courante_id=self._place_courante_id(),
        )
        self.fields["place_parking"].queryset = qs

        if not conducteur:
            self.fields["place_parking"].empty_label = "— Sélectionnez d'abord le conducteur —"
            return

        if place_auto:
            self.fields["place_parking"].initial = place_auto.pk
            self.fields["place_parking"].empty_label = None
            return

        if qs.exists():
            self.fields["place_parking"].empty_label = "— Sélectionner une place —"
        else:
            self.fields["place_parking"].empty_label = "— Aucune place universelle libre —"

    def clean(self):
        cleaned_data = super().clean()
        vehicule = cleaned_data.get("vehicule")
        conducteur = cleaned_data.get("conducteur_entree")
        place = cleaned_data.get("place_parking")

        if vehicule and conducteur:
            autorises = conducteurs_autorises_pour(vehicule)
            if not autorises.filter(pk=conducteur.pk).exists():
                self.add_error(
                    "conducteur_entree",
                    ValidationError(
                        "Le conducteur doit être le titulaire ou un chauffeur du véhicule."
                    ),
                )

        if conducteur and place:
            if not place_autorisee_pour_conducteur(
                conducteur,
                place,
                place_courante_id=self._place_courante_id(),
            ):
                self.add_error(
                    "place_parking",
                    ValidationError(
                        "Cette place n'est pas autorisée pour le conducteur sélectionné."
                    ),
                )
            elif (
                place.parking.type_parking == Parking.TYPE_RESERVE
                and place.statut == PlaceParking.STATUT_OCCUPEE
                and place.pk != self._place_courante_id()
            ):
                self.add_error(
                    "place_parking",
                    ValidationError("La place réservée de ce conducteur est déjà occupée."),
                )

        return cleaned_data


class OccupationSortieForm(forms.Form):
    conducteur_sortie = forms.ModelChoiceField(
        queryset=Personnel.objects.none(),
        label="Conducteur",
        widget=forms.Select(attrs={"class": "form-control"}),
        empty_label="— Sélectionner le conducteur —",
    )

    def __init__(self, occupation, *args, **kwargs):
        self.occupation = occupation
        super().__init__(*args, **kwargs)
        self.fields["conducteur_sortie"].queryset = conducteurs_autorises_pour(
            occupation.vehicule
        )
        self.fields["conducteur_sortie"].required = True

    def clean_conducteur_sortie(self):
        conducteur = self.cleaned_data.get("conducteur_sortie")
        autorises = conducteurs_autorises_pour(self.occupation.vehicule)
        if conducteur and not autorises.filter(pk=conducteur.pk).exists():
            raise ValidationError(
                "Le conducteur doit être le titulaire ou un chauffeur du véhicule."
            )
        return conducteur


class OccupationModifierForm(OccupationEntreeForm):
    class Meta(OccupationEntreeForm.Meta):
        fields = [
            "vehicule",
            "place_parking",
            "conducteur_entree",
            "conducteur_sortie",
            "observation",
        ]
        labels = {
            **OccupationEntreeForm.Meta.labels,
            "conducteur_sortie": "Conducteur à la sortie",
        }
        widgets = {
            **OccupationEntreeForm.Meta.widgets,
            "conducteur_sortie": forms.Select(attrs={"class": "form-control", "id": "id_conducteur_sortie"}),
        }

    def configurer_champs(self):
        super().configurer_champs()
        vehicule = self._vehicule_courant() or (
            self.instance.vehicule if self.instance and self.instance.pk else None
        )
        self.fields["conducteur_sortie"].queryset = conducteurs_autorises_pour(vehicule)
        self.fields["conducteur_sortie"].required = bool(
            self.instance and self.instance.date_sortie
        )
        if not self.instance or not self.instance.date_sortie:
            self.fields["conducteur_sortie"].widget = forms.HiddenInput()
            self.fields["conducteur_sortie"].required = False

    def clean(self):
        cleaned_data = super().clean()
        vehicule = cleaned_data.get("vehicule")
        conducteur_sortie = cleaned_data.get("conducteur_sortie")
        if self.instance and self.instance.date_sortie:
            if not conducteur_sortie:
                self.add_error(
                    "conducteur_sortie",
                    ValidationError("Indiquez le conducteur à la sortie."),
                )
            elif vehicule:
                autorises = conducteurs_autorises_pour(vehicule)
                if not autorises.filter(pk=conducteur_sortie.pk).exists():
                    self.add_error(
                        "conducteur_sortie",
                        ValidationError(
                            "Le conducteur doit être le titulaire ou un chauffeur du véhicule."
                        ),
                    )
        else:
            cleaned_data["conducteur_sortie"] = None
        return cleaned_data


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
