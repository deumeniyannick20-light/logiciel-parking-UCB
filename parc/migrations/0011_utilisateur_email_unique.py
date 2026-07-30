from django.db import migrations, models


def remplir_emails_manquants(apps, schema_editor):
    Utilisateur = apps.get_model("parc", "Utilisateur")
    for utilisateur in Utilisateur.objects.filter(email=""):
        utilisateur.email = utilisateur.identifiant
        utilisateur.save(update_fields=["email"])


class Migration(migrations.Migration):

    dependencies = [
        ("parc", "0010_synchroniser_casse_noms_postes"),
    ]

    operations = [
        migrations.RunPython(remplir_emails_manquants, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="utilisateur",
            name="email",
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
