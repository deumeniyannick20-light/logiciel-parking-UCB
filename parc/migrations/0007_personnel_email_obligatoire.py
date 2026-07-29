from django.db import migrations, models


def remplir_emails_personnel_vides(apps, schema_editor):
    Personnel = apps.get_model("parc", "Personnel")
    for personnel in Personnel.objects.filter(email=""):
        base = f"{personnel.nom}.{personnel.prenom}".lower().replace(" ", ".")
        email = f"{base}@ucb.local"
        suffixe = 1
        while Personnel.objects.filter(email=email).exclude(pk=personnel.pk).exists():
            suffixe += 1
            email = f"{base}{suffixe}@ucb.local"
        personnel.email = email
        personnel.save(update_fields=["email"])


class Migration(migrations.Migration):

    dependencies = [
        ("parc", "0006_alter_utilisateur_email_alter_utilisateur_nom_and_more"),
    ]

    operations = [
        migrations.RunPython(remplir_emails_personnel_vides, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="personnel",
            name="email",
            field=models.EmailField(max_length=254),
        ),
    ]
