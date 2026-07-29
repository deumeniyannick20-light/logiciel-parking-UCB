from urllib.parse import quote

from django.conf import settings
from django.shortcuts import redirect


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
