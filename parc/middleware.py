from urllib.parse import quote

from django.conf import settings
from django.shortcuts import redirect

from .place_alerte import alertes_actives, url_autorisee
from .vehicule_alerte import alertes_vehicule_actives, url_autorisee_vehicule


class ConnexionObligatoireMiddleware:
    """Bloque l'accès à l'application sans authentification préalable."""

    chemins_publics = (
        "/accounts/login/",
        "/accounts/logout/",
        "/accounts/mot-de-passe/oublie/",
        "/accounts/mot-de-passe/oublie/envoye/",
        "/accounts/mot-de-passe/reinitialiser/",
        "/accounts/mot-de-passe/reinitialise/",
        "/admin/",
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


class PersonnelVehiculeAlerteMiddleware:
    """
    Force l'enregistrement d'un véhicule pour le personnel affecté
    à un poste disposant d'une place réservée.
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

        if alertes_actives(request):
            return self.get_response(request)

        alertes = alertes_vehicule_actives(request)
        if alertes and not url_autorisee_vehicule(request.path, alertes):
            return redirect("vehicule_liste")

        return self.get_response(request)
