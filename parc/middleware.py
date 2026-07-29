from urllib.parse import quote

from django.conf import settings
from django.shortcuts import redirect

from .place_alerte import alertes_actives, url_autorisee


class ConnexionObligatoireMiddleware:
    """Bloque l'accès à l'application sans authentification préalable."""

    chemins_publics = (
        "/accounts/login/",
        "/accounts/logout/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        path = request.path
        static_url = getattr(settings, "STATIC_URL", "/static/")
        if path.startswith(static_url):
            return self.get_response(request)

        if any(path.startswith(chemin) for chemin in self.chemins_publics):
            return self.get_response(request)

        login_url = settings.LOGIN_URL
        separateur = "&" if "?" in login_url else "?"
        return redirect(f"{login_url}{separateur}next={quote(path)}")


class PlaceReserveeAlerteMiddleware:
    """
    Force la résolution des places réservées sans poste :
    seules la liste des places et la modification des places en alerte sont accessibles.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        path = request.path
        static_url = getattr(settings, "STATIC_URL", "/static/")
        if path.startswith(static_url):
            return self.get_response(request)

        alertes = alertes_actives(request)
        if alertes and not url_autorisee(request.path, alertes):
            return redirect("placeparking_liste")

        return self.get_response(request)
