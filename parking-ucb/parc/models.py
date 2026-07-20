from django.db import models


class Vehicule(models.Model):
    immatriculation = models.CharField(max_length=20, unique=True)
    marque = models.CharField(max_length=50)
    modele = models.CharField(max_length=50)
    couleur = models.CharField(max_length=30, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ["immatriculation"]

    def __str__(self):
        return f"{self.immatriculation} - {self.marque} {self.modele}"


class Personnel(models.Model):
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    poste = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Personnel"
        verbose_name_plural = "Personnel"
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.poste})"


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