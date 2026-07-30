from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from parc.models import Personnel, Poste, Utilisateur


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthentificationEmailTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.poste = Poste.objects.create(nom="Informatique")
        self.personnel = Personnel.objects.create(
            nom="Test",
            prenom="User",
            poste_obj=self.poste,
            email="test.user@ucb.local",
        )
        self.user = User.objects.create_user(
            username="test.user@ucb.local",
            email="test.user@ucb.local",
            password="Motdepasse123!",
        )
        self.utilisateur = Utilisateur.objects.create(
            nom="Test",
            prenom="User",
            identifiant="test.user@ucb.local",
            email="test.user@ucb.local",
            personnel=self.personnel,
            user=self.user,
            role=Utilisateur.ROLE_OPERATEUR,
            actif=True,
        )

    def test_connexion_email_valide(self):
        response = self.client.post(
            reverse("login"),
            {"username": "test.user@ucb.local", "password": "Motdepasse123!"},
        )
        self.assertRedirects(response, "/")

    def test_connexion_mot_de_passe_invalide(self):
        response = self.client.post(
            reverse("login"),
            {"username": "test.user@ucb.local", "password": "mauvais"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "incorrect")

    def test_reinitialisation_mot_de_passe_envoie_email(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "test.user@ucb.local"},
        )
        self.assertRedirects(response, "/accounts/mot-de-passe/oublie/envoye/")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("test.user@ucb.local", mail.outbox[0].to)

    def test_changement_mot_de_passe_utilisateur_connecte(self):
        self.client.login(username="test.user@ucb.local", password="Motdepasse123!")
        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "Motdepasse123!",
                "new_password1": "NouveauMotdepasse456!",
                "new_password2": "NouveauMotdepasse456!",
            },
        )
        self.assertRedirects(response, "/")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NouveauMotdepasse456!"))

    def test_acces_utilisateurs_reserve_administrateur(self):
        response = self.client.get(reverse("utilisateur_liste"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('utilisateur_liste')}")

        self.client.login(username="test.user@ucb.local", password="Motdepasse123!")
        response = self.client.get(reverse("utilisateur_liste"))
        self.assertRedirects(response, reverse("home"))

        self.utilisateur.role = Utilisateur.ROLE_ADMINISTRATEUR
        self.utilisateur.save(update_fields=["role"])
        response = self.client.get(reverse("utilisateur_liste"))
        self.assertEqual(response.status_code, 200)
