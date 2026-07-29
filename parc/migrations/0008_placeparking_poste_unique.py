from collections import defaultdict

from django.db import migrations, models


def dedoublonner_postes_places(apps, schema_editor):
    PlaceParking = apps.get_model("parc", "PlaceParking")
    Parking = apps.get_model("parc", "Parking")

    reserve_ids = set(
        Parking.objects.filter(type_parking="reserve").values_list("pk", flat=True)
    )
    par_poste = defaultdict(list)
    for place in PlaceParking.objects.filter(
        poste_affecte_id__isnull=False,
        parking_id__in=reserve_ids,
    ).order_by("pk"):
        par_poste[place.poste_affecte_id].append(place)

    for places in par_poste.values():
        if len(places) <= 1:
            continue
        for place in places[1:]:
            place.poste_affecte_id = None
            place.save(update_fields=["poste_affecte_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("parc", "0007_personnel_email_obligatoire"),
    ]

    operations = [
        migrations.RunPython(dedoublonner_postes_places, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="placeparking",
            constraint=models.UniqueConstraint(
                condition=models.Q(("poste_affecte__isnull", False)),
                fields=("poste_affecte",),
                name="parc_placeparking_poste_unique",
            ),
        ),
    ]
