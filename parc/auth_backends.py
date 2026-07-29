from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import Utilisateur


class EmailAuthBackend(ModelBackend):
    """Connexion réservée aux comptes Utilisateur (email + mot de passe enregistrés)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = (kwargs.get("email") or username or "").strip().lower()
        if not email or not password:
            return None

        try:
            utilisateur = Utilisateur.objects.select_related("user").get(
                Q(email__iexact=email) | Q(identifiant__iexact=email),
                actif=True,
            )
        except Utilisateur.DoesNotExist:
            return None

        user = utilisateur.user
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def user_can_authenticate(self, user):
        if not super().user_can_authenticate(user):
            return False
        if not hasattr(user, "profil_utilisateur"):
            return False
        return user.profil_utilisateur.actif

    def get_user(self, user_id):
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        if self.user_can_authenticate(user):
            return user
        return None
