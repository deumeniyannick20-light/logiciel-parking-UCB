def utilisateur_connecte(request):
    """Expose le profil Utilisateur de la session courante dans les templates."""
    if not request.user.is_authenticated:
        return {"utilisateur_connecte": None}

    from .models import Utilisateur

    try:
        profil = (
            Utilisateur.objects.select_related("personnel__poste_obj")
            .get(user_id=request.user.pk)
        )
    except Utilisateur.DoesNotExist:
        profil = None

    return {"utilisateur_connecte": profil}


def menu_actif(request):
    """Identifie la rubrique du menu latéral selon l'URL courante."""
    path = request.path or "/"
    if path in ("/", ""):
        section = "home"
    elif path.startswith("/zones"):
        section = "zones"
    elif path.startswith("/parkings"):
        section = "parkings"
    elif path.startswith("/postes"):
        section = "postes"
    elif path.startswith("/personnels"):
        section = "personnels"
    elif path.startswith("/places-parking"):
        section = "places"
    elif path.startswith("/vehicules"):
        section = "vehicules"
    elif path.startswith("/utilisateurs"):
        section = "utilisateurs"
    elif path.startswith("/occupations"):
        section = "occupations"
    else:
        section = ""
    return {"menu_actif": section}
