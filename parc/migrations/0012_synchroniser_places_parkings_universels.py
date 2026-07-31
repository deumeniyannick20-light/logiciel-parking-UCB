from django.db import migrations


def synchroniser_parkings_universels_existants(apps, schema_editor):
    Parking = apps.get_model("parc", "Parking")
    PlaceParking = apps.get_model("parc", "PlaceParking")

    for parking in Parking.objects.filter(type_parking="universel"):
        cible = parking.capacite_total
        if cible < 1:
            continue

        places = list(PlaceParking.objects.filter(parking_id=parking.pk))
        nombre_actuel = len(places)
        if nombre_actuel >= cible:
            continue

        numeros_pris = {place.numero for place in places}
        a_creer = cible - nombre_actuel
        prochain_numero = nombre_actuel + 1
        crees = 0

        while crees < a_creer:
            numero = str(prochain_numero)
            while numero in numeros_pris:
                prochain_numero += 1
                numero = str(prochain_numero)
            PlaceParking.objects.create(
                parking_id=parking.pk,
                numero=numero,
                statut="libre",
                actif=True,
            )
            numeros_pris.add(numero)
            crees += 1
            prochain_numero += 1


class Migration(migrations.Migration):

    dependencies = [
        ("parc", "0011_utilisateur_email_unique"),
    ]

    operations = [
        migrations.RunPython(
            synchroniser_parkings_universels_existants,
            migrations.RunPython.noop,
        ),
    ]
