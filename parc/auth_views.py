from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import redirect

from .forms import ChangementMotDePasseForm


def deconnexion(request):
    """Déconnecte l'utilisateur et redirige vers la page de connexion."""
    logout(request)
    return redirect("login")


class ChangementMotDePasseView(PasswordChangeView):
    template_name = "parc/password_change.html"
    form_class = ChangementMotDePasseForm
    success_url = "/"

    def form_valid(self, form):
        messages.success(self.request, "Votre mot de passe a été modifié avec succès.")
        return super().form_valid(form)
