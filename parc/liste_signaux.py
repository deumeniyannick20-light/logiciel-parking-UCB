"""Compteurs et indicateurs visuels des listes (flèche après ajout/suppression)."""

SIGNAL_AJOUT = "up"
SIGNAL_SUPPRESSION = "down"


def _cle_session(rubrique):
    return f"liste_signal_{rubrique}"


def signaler_ajout(request, rubrique):
    request.session[_cle_session(rubrique)] = SIGNAL_AJOUT


def signaler_suppression(request, rubrique):
    request.session[_cle_session(rubrique)] = SIGNAL_SUPPRESSION


def contexte_liste(request, rubrique, queryset):
    return {
        "liste_total": queryset.count(),
        "liste_signal": request.session.pop(_cle_session(rubrique), None),
    }


def redirect_liste(request, url_name, rubrique, variation=None):
    from django.shortcuts import redirect

    if variation == "ajout":
        signaler_ajout(request, rubrique)
    elif variation == "suppression":
        signaler_suppression(request, rubrique)
    return redirect(url_name)
