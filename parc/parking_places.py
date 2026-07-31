"""Synchronisation des places de parking pour les parkings universels."""

from django.db import transaction

from .models import Parking, PlaceParking


def synchroniser_places_universel(parking):
    """
    Aligne le nombre de places enregistrées sur capacite_total pour un parking universel.
    Les places existantes sont conservées ; seules les places manquantes sont créées.
    """
    if parking.type_parking != Parking.TYPE_UNIVERSEL:
        return 0

    cible = parking.capacite_total
    if cible < 1:
        return 0

    places_existantes = list(parking.places.all())
    nombre_actuel = len(places_existantes)
    if nombre_actuel >= cible:
        return 0

    numeros_pris = {place.numero for place in places_existantes}
    a_creer = cible - nombre_actuel
    prochain_numero = nombre_actuel + 1
    crees = 0

    with transaction.atomic():
        while crees < a_creer:
            numero = str(prochain_numero)
            while numero in numeros_pris:
                prochain_numero += 1
                numero = str(prochain_numero)
            PlaceParking.objects.create(
                parking=parking,
                numero=numero,
                statut=PlaceParking.STATUT_LIBRE,
                actif=True,
            )
            numeros_pris.add(numero)
            crees += 1
            prochain_numero += 1

    return crees
