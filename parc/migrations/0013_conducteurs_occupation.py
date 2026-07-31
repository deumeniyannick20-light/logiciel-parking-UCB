from django.db import migrations, models
import django.db.models.deletion


def migrer_chauffeurs_et_conducteurs(apps, schema_editor):
    Vehicule = apps.get_model("parc", "Vehicule")
    Occupation = apps.get_model("parc", "Occupation")

    for vehicule in Vehicule.objects.all():
        chauffeur_id = getattr(vehicule, "chauffeur_id", None)
        if chauffeur_id and chauffeur_id != vehicule.personnel_id:
            vehicule.chauffeurs.add(chauffeur_id)

    for occupation in Occupation.objects.select_related("vehicule").all():
        vehicule = occupation.vehicule
        conducteur_id = vehicule.personnel_id
        if not conducteur_id:
            conducteur_id = (
                vehicule.chauffeurs.order_by("pk").values_list("pk", flat=True).first()
            )
        if conducteur_id:
            occupation.conducteur_entree_id = conducteur_id
            if occupation.date_sortie:
                occupation.conducteur_sortie_id = conducteur_id
            occupation.save(update_fields=["conducteur_entree_id", "conducteur_sortie_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("parc", "0012_synchroniser_places_parkings_universels"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicule",
            name="chauffeurs",
            field=models.ManyToManyField(
                blank=True,
                related_name="vehicules_conduits",
                to="parc.personnel",
                verbose_name="Chauffeurs",
            ),
        ),
        migrations.AddField(
            model_name="occupation",
            name="conducteur_entree",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="occupations_entree",
                to="parc.personnel",
                verbose_name="Conducteur à l'entrée",
            ),
        ),
        migrations.AddField(
            model_name="occupation",
            name="conducteur_sortie",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="occupations_sortie",
                to="parc.personnel",
                verbose_name="Conducteur à la sortie",
            ),
        ),
        migrations.RunPython(migrer_chauffeurs_et_conducteurs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="occupation",
            name="conducteur_entree",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="occupations_entree",
                to="parc.personnel",
                verbose_name="Conducteur à l'entrée",
            ),
        ),
        migrations.AlterField(
            model_name="vehicule",
            name="personnel",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="vehicules",
                to="parc.personnel",
                verbose_name="Titulaire",
            ),
        ),
        migrations.RemoveField(
            model_name="vehicule",
            name="chauffeur",
        ),
    ]
