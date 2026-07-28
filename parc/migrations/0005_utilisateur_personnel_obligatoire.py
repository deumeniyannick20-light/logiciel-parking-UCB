# Generated manually — utilisateur obligatoirement lié à un personnel

import django.db.models.deletion
from django.db import migrations, models


def supprimer_utilisateurs_sans_personnel(apps, schema_editor):
    Utilisateur = apps.get_model("parc", "Utilisateur")
    Utilisateur.objects.filter(personnel_id__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("parc", "0004_roles_application"),
    ]

    operations = [
        migrations.RunPython(supprimer_utilisateurs_sans_personnel, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="utilisateur",
            name="personnel",
            field=models.OneToOneField(
                help_text="L'utilisateur doit être un membre du personnel véhiculé déjà enregistré.",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="compte_utilisateur",
                to="parc.personnel",
                verbose_name="Personnel véhiculé",
            ),
        ),
    ]
