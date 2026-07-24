from django.db import models
from django.conf import settings


class Zone(models.Model):
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


class Poste(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Parking(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    adresse = models.CharField(max_length=255, blank=True)
    capacite_total = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    # 🔗 RELATION : Un parking appartient à une Zone
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="parkings", null=True, blank=True)

    class Meta:
        verbose_name = "Parking"
        verbose_name_plural = "Parkings"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class PlaceParking(models.Model):
    parking = models.ForeignKey(Parking, on_delete=models.CASCADE, related_name="places")
    numero = models.CharField(max_length=20)
    statut = models.CharField(
        max_length=20,
        choices=[("libre", "Libre"), ("occupee", "Occupée")],
        default="libre"
    )
    type_place = models.CharField(max_length=50, blank=True)
    actif = models.BooleanField(default=True)

    # 🔗 RELATION : Une place peut être réservée/affectée à un Poste
    poste_affecte = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, blank=True, related_name="places_affectees")

    class Meta:
        verbose_name = "Place de parking"
        verbose_name_plural = "Places de parking"
        unique_together = ("parking", "numero")
        ordering = ["parking__nom", "numero"]

    def __str__(self):
        return f"{self.parking.nom} - Place N°{self.numero}"


class Personnel(models.Model):
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    # On utilise poste_obj au lieu de poste pour éviter le bug de renommage MySQL
    poste_obj = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, blank=True, related_name="personnels")
    email = models.EmailField(blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Personnel"
        verbose_name_plural = "Personnel"
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.nom} {self.prenom}"


class Vehicule(models.Model):
    immatriculation = models.CharField(max_length=20, unique=True)
    marque = models.CharField(max_length=50)
    modele = models.CharField(max_length=50)
    couleur = models.CharField(max_length=30, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    # 🔗 RELATION : Un véhicule appartient à un membre du Personnel
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name="vehicules", null=True, blank=True)

    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ["immatriculation"]

    def __str__(self):
        return f"{self.immatriculation} - {self.marque} {self.modele}"


class Utilisateur(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profil_utilisateur"
    )
    poste = models.ForeignKey(
        Poste,
        on_delete=models.PROTECT,
        related_name="utilisateurs",
        null=True,
        blank=True
    )
    telephone = models.CharField(max_length=20, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["user__username"]

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Occupation(models.Model):
    place_parking = models.ForeignKey(
        PlaceParking,
        on_delete=models.CASCADE,
        related_name="occupations"
    )
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="occupations",
        null=True,
        blank=True
    )
    # 🔗 RELATION : Liaison directe au véhicule garé
    vehicule = models.ForeignKey(
        Vehicule,
        on_delete=models.CASCADE,
        related_name="occupations",
        null=True,
        blank=True
    )
    date_entree = models.DateTimeField(auto_now_add=True)
    date_sortie = models.DateTimeField(null=True, blank=True)
    est_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Occupation"
        verbose_name_plural = "Occupations"
        ordering = ["-date_entree"]

    def __str__(self):
        return f"{self.place_parking} -> {self.vehicule or self.utilisateur}"