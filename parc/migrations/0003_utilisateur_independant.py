# Generated manually — utilisateurs dissociés du personnel véhiculé

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def remplir_utilisateur_depuis_user(apps, schema_editor):
    Utilisateur = apps.get_model("parc", "Utilisateur")
    for utilisateur in Utilisateur.objects.select_related("user").all():
        user = utilisateur.user
        utilisateur.nom = user.last_name or user.username
        utilisateur.prenom = user.first_name or user.username
        utilisateur.identifiant = user.username
        utilisateur.email = user.email or ""
        utilisateur.save(update_fields=["nom", "prenom", "identifiant", "email"])


class Migration(migrations.Migration):

    dependencies = [
        ("parc", "0002_align_modele_metier"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="utilisateur",
            name="email",
            field=models.EmailField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="utilisateur",
            name="identifiant",
            field=models.CharField(
                help_text="Identifiant de connexion à l'application",
                max_length=150,
                null=True,
                unique=True,
                verbose_name="Compte utilisateur",
            ),
        ),
        migrations.AddField(
            model_name="utilisateur",
            name="nom",
            field=models.CharField(default="", max_length=50),
        ),
        migrations.AddField(
            model_name="utilisateur",
            name="prenom",
            field=models.CharField(default="", max_length=50),
        ),
        migrations.AddField(
            model_name="utilisateur",
            name="personnel",
            field=models.ForeignKey(
                blank=True,
                help_text="Optionnel : si cet utilisateur est aussi un employé véhiculé déjà enregistré.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="comptes_utilisateur",
                to="parc.personnel",
                verbose_name="Personnel véhiculé lié",
            ),
        ),
        migrations.RunPython(remplir_utilisateur_depuis_user, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="utilisateur",
            name="identifiant",
            field=models.CharField(
                help_text="Identifiant de connexion à l'application",
                max_length=150,
                unique=True,
                verbose_name="Compte utilisateur",
            ),
        ),
        migrations.AlterModelOptions(
            name="utilisateur",
            options={
                "ordering": ["nom", "prenom"],
                "verbose_name": "Utilisateur",
                "verbose_name_plural": "Utilisateurs",
            },
        ),
        migrations.AlterField(
            model_name="utilisateur",
            name="role",
            field=models.CharField(
                choices=[
                    ("vigile", "Vigile"),
                    ("it", "Service IT / Administrateur"),
                    ("direction", "Direction générale"),
                ],
                default="vigile",
                max_length=20,
            ),
        ),
    ]
