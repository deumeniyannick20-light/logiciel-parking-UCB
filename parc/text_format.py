"""Normalisation de la casse des champs texte."""

CHAMPS_MAJUSCULES = frozenset({"nom", "immatriculation"})

CHAMPS_NUMERIQUES = frozenset({
    "superficie",
    "nombre_employes",
    "capacite_total",
    "numero",
    "telephone",
})

CHAMPS_EXCLUS = frozenset({"email", "identifiant"}) | CHAMPS_NUMERIQUES


def en_majuscules(value):
    if not value:
        return value
    return str(value).strip().upper()


def premiere_lettre_majuscule(value):
    if not value:
        return value
    texte = str(value).strip()
    return texte[0].upper() + texte[1:] if texte else texte


def majuscule_mots(value):
    if not value:
        return value
    return " ".join(mot.capitalize() for mot in str(value).strip().split())


def formater_nom_poste(nom, est_direction=False):
    if not nom:
        return nom
    if est_direction:
        return en_majuscules(nom)
    return majuscule_mots(nom)


def formater_champ(nom_champ, value):
    if value is None or nom_champ in CHAMPS_EXCLUS:
        return value
    if not isinstance(value, str):
        return value
    if nom_champ in CHAMPS_MAJUSCULES:
        return en_majuscules(value)
    if value.strip():
        return premiere_lettre_majuscule(value)
    return value


def formater_instance_texte(instance, noms_champs):
    """Normalise les champs texte d'un modèle avant enregistrement."""
    for nom_champ in noms_champs:
        valeur = getattr(instance, nom_champ, None)
        if valeur is not None:
            setattr(instance, nom_champ, formater_champ(nom_champ, valeur))
