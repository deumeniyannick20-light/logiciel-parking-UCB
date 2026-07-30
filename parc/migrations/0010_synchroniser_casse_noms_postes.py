from django.db import migrations

from parc.text_format import formater_nom_poste


def synchroniser_casse_postes(apps, schema_editor):
    Poste = apps.get_model("parc", "Poste")
    PlaceParking = apps.get_model("parc", "PlaceParking")

    for poste in Poste.objects.all().iterator():
        a_place_reservee = PlaceParking.objects.filter(
            poste_affecte_id=poste.pk,
            parking__type_parking="reserve",
        ).exists()
        nouveau_nom = formater_nom_poste(poste.nom, a_place_reservee)
        if nouveau_nom != poste.nom:
            Poste.objects.filter(pk=poste.pk).update(nom=nouveau_nom)


class Migration(migrations.Migration):

    dependencies = [
        ("parc", "0009_parking_capacite_min_1"),
    ]

    operations = [
        migrations.RunPython(synchroniser_casse_postes, migrations.RunPython.noop),
    ]
