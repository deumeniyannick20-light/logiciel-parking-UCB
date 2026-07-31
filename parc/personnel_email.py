"""Proposition d'email UCB pour le personnel."""

import re
import unicodedata


def fragment_email(valeur):
    if not valeur:
        return ""
    texte = unicodedata.normalize("NFD", str(valeur).strip().lower())
    texte = "".join(car for car in texte if unicodedata.category(car) != "Mn")
    return re.sub(r"[^a-z0-9]", "", texte)


def proposer_email_ucb(nom, prenom):
    fragment_nom = fragment_email(nom)
    fragment_prenom = fragment_email(prenom)
    if not fragment_nom or not fragment_prenom:
        return ""
    return f"{fragment_nom}.{fragment_prenom}@ucb.local".lower()
