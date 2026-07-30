from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import Utilisateur


def administrateur_requis(view_func):
    """Restreint l'accès aux utilisateurs ayant le rôle administrateur."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        profil = getattr(request.user, "profil_utilisateur", None)
        if profil is None or profil.role != Utilisateur.ROLE_ADMINISTRATEUR:
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect("home")
        return view_func(request, *args, **kwargs)

    return _wrapped
