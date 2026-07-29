from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from .text_format import formater_instance_texte, formater_nom_poste


class NormalisationTexteMixin:
    """Normalise la casse des champs texte avant enregistrement."""

    champs_texte = ()

    def normaliser_texte(self):
        formater_instance_texte(self, self.champs_texte)


class Zone(NormalisationTexteMixin, models.Model):
    champs_texte = ("nom", "services")
    nom = models.CharField(max_length=100, unique=True)
    superficie = models.DecimalField(max_digits=8, decimal_places=2, help_text="Superficie en m²")
    services = models.CharField(max_length=200, blank=True)
    nombre_employes = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Zone"
        verbose_name_plural = "Zones"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.superficie} m²)"

    def save(self, *args, **kwargs):
        self.normaliser_texte()
        super().save(*args, **kwargs)


class Poste(NormalisationTexteMixin, models.Model):
    champs_texte = ("description",)
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    est_direction = models.BooleanField(
        default=False,
        help_text="Cocher pour les postes de direction (DG, DGA, DRH...)"
    )
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        ordering = ["nom"]

    def __str__(self):
        return self.nom

    def normaliser_texte(self):
        if self.nom:
            self.nom = formater_nom_poste(self.nom, self.est_direction)
        formater_instance_texte(self, self.champs_texte)

    def save(self, *args, **kwargs):
        self.normaliser_texte()
        super().save(*args, **kwargs)


class Parking(NormalisationTexteMixin, models.Model):
    champs_texte = ("nom", "adresse")
    TYPE_UNIVERSEL = "universel"
    TYPE_RESERVE = "reserve"
    TYPE_CHOICES = [
        (TYPE_UNIVERSEL, "Universel (tous employés véhiculés)"),
        (TYPE_RESERVE, "Réservé (cadres supérieurs / direction)"),
    ]

    nom = models.CharField(max_length=100, unique=True)
    zone = models.ForeignKey(
        Zone,
        on_delete=models.CASCADE,
        related_name="parkings",
    )
    adresse = models.CharField(max_length=255, blank=True)
    type_parking = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_UNIVERSEL,
    )
    capacite_total = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Parking"
        verbose_name_plural = "Parkings"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.get_type_parking_display()})"

    def save(self, *args, **kwargs):
        self.normaliser_texte()
        super().save(*args, **kwargs)


class PlaceParking(NormalisationTexteMixin, models.Model):
    champs_texte = ()
    STATUT_LIBRE = "libre"
    STATUT_OCCUPEE = "occupee"
    STATUT_CHOICES = [
        (STATUT_LIBRE, "Libre"),
        (STATUT_OCCUPEE, "Occupée"),
    ]

    parking = models.ForeignKey(Parking, on_delete=models.CASCADE, related_name="places")
    numero = models.CharField(max_length=20)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=STATUT_LIBRE)
    actif = models.BooleanField(default=True)

    # 0..1 : optionnel — uniquement pour parkings réservés
    poste_affecte = models.ForeignKey(
        Poste,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="places_affectees",
    )

    class Meta:
        verbose_name = "Place de parking"
        verbose_name_plural = "Places de parking"
        unique_together = ("parking", "numero")
        ordering = ["parking__nom", "numero"]

    def clean(self):
        if self.parking.type_parking == Parking.TYPE_UNIVERSEL and self.poste_affecte_id:
            raise ValidationError(
                "Une place de parking universel ne peut pas être affectée à un poste."
            )
        if self.parking.type_parking == Parking.TYPE_RESERVE and not self.poste_affecte_id:
            raise ValidationError(
                "Une place de parking privé doit être affectée à un poste."
            )

    def __str__(self):
        return f"{self.parking.nom} - Place N°{self.numero}"

    def save(self, *args, **kwargs):
        self.normaliser_texte()
        super().save(*args, **kwargs)


class Personnel(NormalisationTexteMixin, models.Model):
    champs_texte = ("nom", "prenom")
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    poste_obj = models.ForeignKey(
        Poste,
        on_delete=models.PROTECT,
        related_name="personnels",
    )
    email = models.EmailField(blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Personnel"
        verbose_name_plural = "Personnel"
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.poste_obj})"

    def save(self, *args, **kwargs):
        self.normaliser_texte()
        super().save(*args, **kwargs)


class Vehicule(NormalisationTexteMixin, models.Model):
    champs_texte = ("immatriculation", "marque", "modele", "couleur")
    immatriculation = models.CharField(max_length=20, unique=True)
    marque = models.CharField(max_length=50)
    modele = models.CharField(max_length=50)
    couleur = models.CharField(max_length=30, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    # Propriétaire / titulaire (obligatoire)
    personnel = models.ForeignKey(
        Personnel,
        on_delete=models.PROTECT,
        related_name="vehicules",
    )
    # Chauffeur éventuel (0..1)
    chauffeur = models.ForeignKey(
        Personnel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicules_conduits",
    )

    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ["immatriculation"]

    def clean(self):
        if self.chauffeur_id and self.chauffeur_id == self.personnel_id:
            raise ValidationError("Le chauffeur ne peut pas être la même personne que le titulaire.")

    def __str__(self):
        return f"{self.immatriculation} - {self.marque} {self.modele}"

    def save(self, *args, **kwargs):
        self.normaliser_texte()
        super().save(*args, **kwargs)


class Utilisateur(NormalisationTexteMixin, models.Model):
    champs_texte = ("nom", "prenom")
    ROLE_ADMINISTRATEUR = "administrateur"
    ROLE_OPERATEUR = "operateur"
    ROLE_CHOICES = [
        (ROLE_ADMINISTRATEUR, "Administrateur"),
        (ROLE_OPERATEUR, "Opérateur"),
    ]

    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    identifiant = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Compte utilisateur",
        help_text="Identifiant de connexion à l'application",
    )
    email = models.EmailField(blank=True)
    personnel = models.OneToOneField(
        Personnel,
        on_delete=models.PROTECT,
        related_name="compte_utilisateur",
        verbose_name="Personnel",
        help_text="L'utilisateur doit être un membre du personnel déjà enregistré.",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profil_utilisateur",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_OPERATEUR)
    telephone = models.CharField(max_length=20, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.identifiant})"

    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}".strip()

    @property
    def initiales(self):
        return "".join(
            partie[0].upper()
            for partie in self.nom_complet.split()
            if partie
        )

    @property
    def poste_entreprise(self):
        if self.personnel_id:
            return self.personnel.poste_obj
        return None

    def save(self, *args, **kwargs):
        if self.personnel_id:
            self.nom = self.personnel.nom
            self.prenom = self.personnel.prenom
            if not self.email and self.personnel.email:
                self.email = self.personnel.email
        self.normaliser_texte()
        super().save(*args, **kwargs)


class Occupation(NormalisationTexteMixin, models.Model):
    champs_texte = ("observation",)
    place_parking = models.ForeignKey(
        PlaceParking,
        on_delete=models.PROTECT,
        related_name="occupations",
    )
    vehicule = models.ForeignKey(
        Vehicule,
        on_delete=models.PROTECT,
        related_name="occupations",
    )
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="occupations_enregistrees",
        help_text="Vigile / agent ayant enregistré le mouvement",
    )
    date_entree = models.DateTimeField(default=timezone.now)
    date_sortie = models.DateTimeField(null=True, blank=True)
    observation = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Occupation"
        verbose_name_plural = "Occupations"
        ordering = ["-date_entree"]

    @property
    def est_active(self):
        return self.date_sortie is None

    @property
    def duree(self):
        fin = self.date_sortie or timezone.now()
        return fin - self.date_entree

    def clean(self):
        place = self.place_parking
        vehicule = self.vehicule

        if self.date_sortie and self.date_sortie < self.date_entree:
            raise ValidationError("La date de sortie ne peut pas être antérieure à l'entrée.")

        # Nouvelle entrée uniquement
        if self.date_sortie is None:
            if place.statut == PlaceParking.STATUT_OCCUPEE:
                raise ValidationError("Cette place est déjà occupée.")

            deja_gare = Occupation.objects.filter(
                vehicule=vehicule,
                date_sortie__isnull=True,
            ).exclude(pk=self.pk).exists()
            if deja_gare:
                raise ValidationError("Ce véhicule est déjà garé sur une autre place.")

            if place.poste_affecte_id:
                postes_autorises = {vehicule.personnel.poste_obj_id}
                if vehicule.chauffeur_id:
                    postes_autorises.add(vehicule.chauffeur.poste_obj_id)
                if place.poste_affecte_id not in postes_autorises:
                    raise ValidationError(
                        f"Cette place est réservée au poste « {place.poste_affecte} »."
                    )

    def save(self, *args, **kwargs):
        self.normaliser_texte()
        super().save(*args, **kwargs)

        place = self.place_parking
        if self.date_sortie is None:
            place.statut = PlaceParking.STATUT_OCCUPEE
        else:
            # Vérifier s'il reste une autre occupation active sur cette place
            autre_active = place.occupations.filter(date_sortie__isnull=True).exclude(pk=self.pk).exists()
            if not autre_active:
                place.statut = PlaceParking.STATUT_LIBRE
        place.save(update_fields=["statut"])

    def __str__(self):
        return f"{self.vehicule} @ {self.place_parking} (entrée: {self.date_entree:%d/%m/%Y %H:%M})"