# Generated manually — rôles application : administrateur / opérateur

from django.db import migrations, models


def convertir_anciens_roles(apps, schema_editor):
    Utilisateur = apps.get_model("parc", "Utilisateur")
    mapping = {
        "vigile": "operateur",
        "it": "administrateur",
        "direction": "administrateur",
    }
    for utilisateur in Utilisateur.objects.all():
        if utilisateur.role in mapping:
            utilisateur.role = mapping[utilisateur.role]
            utilisateur.save(update_fields=["role"])


class Migration(migrations.Migration):

    dependencies = [
        ("parc", "0003_utilisateur_independant"),
    ]

    operations = [
        migrations.RunPython(convertir_anciens_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="utilisateur",
            name="role",
            field=models.CharField(
                choices=[
                    ("administrateur", "Administrateur"),
                    ("operateur", "Opérateur"),
                ],
                default="operateur",
                max_length=20,
            ),
        ),
    ]
