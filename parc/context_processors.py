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
