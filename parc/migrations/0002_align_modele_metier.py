# Generated manually for parking-ucb model alignment

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def purge_invalid_rows(apps, schema_editor):
    Occupation = apps.get_model("parc", "Occupation")
    Vehicule = apps.get_model("parc", "Vehicule")
    Personnel = apps.get_model("parc", "Personnel")
    Parking = apps.get_model("parc", "Parking")

    Occupation.objects.filter(vehicule_id__isnull=True).delete()
    Vehicule.objects.filter(personnel_id__isnull=True).delete()
    Personnel.objects.filter(poste_obj_id__isnull=True).delete()
    Parking.objects.filter(zone_id__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("parc", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(purge_invalid_rows, migrations.RunPython.noop),
        migrations.AddField(
            model_name="poste",
            name="est_direction",
            field=models.BooleanField(
                default=False,
                help_text="Cocher pour les postes de direction (DG, DGA, DRH...)",
            ),
        ),
        migrations.AddField(
            model_name="parking",
            name="type_parking",
            field=models.CharField(
                choices=[
                    ("universel", "Universel (tous employés véhiculés)"),
                    ("reserve", "Réservé (cadres supérieurs / direction)"),
                ],
                default="universel",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="utilisateur",
            name="role",
            field=models.CharField(
                choices=[
                    ("vigile", "Vigile"),
                    ("it", "Service IT"),
                    ("direction", "Direction générale"),
                ],
                default="vigile",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="occupation",
            name="observation",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="vehicule",
            name="chauffeur",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="vehicules_conduits",
                to="parc.personnel",
            ),
        ),
        migrations.RemoveField(
            model_name="utilisateur",
            name="poste",
        ),
        migrations.RemoveField(
            model_name="placeparking",
            name="type_place",
        ),
        migrations.RemoveField(
            model_name="occupation",
            name="est_active",
        ),
        migrations.AlterField(
            model_name="occupation",
            name="date_entree",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="occupation",
            name="place_parking",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="occupations",
                to="parc.placeparking",
            ),
        ),
        migrations.AlterField(
            model_name="occupation",
            name="utilisateur",
            field=models.ForeignKey(
                blank=True,
                help_text="Vigile / agent ayant enregistré le mouvement",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="occupations_enregistrees",
                to="parc.utilisateur",
            ),
        ),
        migrations.AlterField(
            model_name="occupation",
            name="vehicule",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="occupations",
                to="parc.vehicule",
            ),
        ),
        migrations.AlterField(
            model_name="parking",
            name="zone",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="parkings",
                to="parc.zone",
            ),
        ),
        migrations.AlterField(
            model_name="personnel",
            name="poste_obj",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="personnels",
                to="parc.poste",
            ),
        ),
        migrations.AlterField(
            model_name="vehicule",
            name="personnel",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="vehicules",
                to="parc.personnel",
            ),
        ),
    ]
