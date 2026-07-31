from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from .forms import (
    ConnexionEmailForm,
    NouveauMotDePasseForm,
    ReinitialisationMotDePasseForm,
)
from .auth_views import ChangementMotDePasseView, deconnexion

urlpatterns = [
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="parc/login.html",
            authentication_form=ConnexionEmailForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("accounts/logout/", deconnexion, name="logout"),
    path(
        "accounts/mot-de-passe/oublie/",
        auth_views.PasswordResetView.as_view(
            template_name="parc/auth/password_reset_form.html",
            email_template_name="parc/auth/email/reinitialisation.txt",
            subject_template_name="parc/auth/email/reinitialisation_sujet.txt",
            form_class=ReinitialisationMotDePasseForm,
            success_url="/accounts/mot-de-passe/oublie/envoye/",
        ),
        name="password_reset",
    ),
    path(
        "accounts/mot-de-passe/oublie/envoye/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="parc/auth/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "accounts/mot-de-passe/reinitialiser/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="parc/auth/password_reset_confirm.html",
            form_class=NouveauMotDePasseForm,
            success_url="/accounts/mot-de-passe/reinitialise/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/mot-de-passe/reinitialise/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="parc/auth/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path(
        "accounts/mot-de-passe/changer/",
        ChangementMotDePasseView.as_view(),
        name="password_change",
    ),

    path("", views.home, name="home"),

    path("api/dashboard/vehicules/", views.api_dashboard_vehicules, name="api_dashboard_vehicules"),
    path("api/dashboard/parking/<int:pk>/", views.api_dashboard_parking, name="api_dashboard_parking"),
    path("api/dashboard/vehicule/<int:pk>/", views.api_dashboard_vehicule, name="api_dashboard_vehicule"),
    path("api/vehicules/recherche/", views.api_vehicules_recherche, name="api_vehicules_recherche"),
    path("api/parkings/<int:pk>/places/", views.api_parking_places, name="api_parking_places"),

    path("vehicules/", views.vehicule_liste, name="vehicule_liste"),
    path("vehicules/creer/", views.vehicule_creer, name="vehicule_creer"),
    path("vehicules/<int:pk>/modifier/", views.vehicule_modifier, name="vehicule_modifier"),
    path("vehicules/<int:pk>/supprimer/", views.vehicule_supprimer, name="vehicule_supprimer"),

    path("personnels/", views.personnel_liste, name="personnel_liste"),
    path("personnels/creer/", views.personnel_creer, name="personnel_creer"),
    path("personnels/<int:pk>/modifier/", views.personnel_modifier, name="personnel_modifier"),
    path("personnels/<int:pk>/supprimer/", views.personnel_supprimer, name="personnel_supprimer"),
    path(
        "personnels/<int:pk>/annuler-creation/",
        views.personnel_annuler_alerte_vehicule,
        name="personnel_annuler_alerte_vehicule",
    ),

    path("zones/", views.zone_liste, name="zone_liste"),
    path("zones/creer/", views.zone_creer, name="zone_creer"),
    path("zones/<int:pk>/modifier/", views.zone_modifier, name="zone_modifier"),
    path("zones/<int:pk>/supprimer/", views.zone_supprimer, name="zone_supprimer"),

    path("postes/", views.poste_liste, name="poste_liste"),
    path("postes/creer/", views.poste_creer, name="poste_creer"),
    path("postes/<int:pk>/modifier/", views.poste_modifier, name="poste_modifier"),
    path("postes/<int:pk>/supprimer/", views.poste_supprimer, name="poste_supprimer"),

    path("parkings/", views.parking_liste, name="parking_liste"),
    path("parkings/creer/", views.parking_creer, name="parking_creer"),
    path("parkings/<int:pk>/modifier/", views.parking_modifier, name="parking_modifier"),
    path("parkings/<int:pk>/supprimer/", views.parking_supprimer, name="parking_supprimer"),

    path("places-parking/", views.placeparking_liste, name="placeparking_liste"),
    path("places-parking/creer/", views.placeparking_creer, name="placeparking_creer"),
    path("places-parking/<int:pk>/modifier/", views.placeparking_modifier, name="placeparking_modifier"),
    path("places-parking/<int:pk>/supprimer/", views.placeparking_supprimer, name="placeparking_supprimer"),

    path("utilisateurs/", views.utilisateur_liste, name="utilisateur_liste"),
    path("utilisateurs/creer/", views.utilisateur_creer, name="utilisateur_creer"),
    path("utilisateurs/<int:pk>/modifier/", views.utilisateur_modifier, name="utilisateur_modifier"),
    path("utilisateurs/<int:pk>/supprimer/", views.utilisateur_supprimer, name="utilisateur_supprimer"),

    path("occupations/", views.occupation_liste, name="occupation_liste"),
    path("occupations/creer/", views.occupation_creer, name="occupation_creer"),
    path("occupations/<int:pk>/sortie/", views.occupation_sortie, name="occupation_sortie"),
    path("occupations/<int:pk>/modifier/", views.occupation_modifier, name="occupation_modifier"),
    path("occupations/<int:pk>/supprimer/", views.occupation_supprimer, name="occupation_supprimer"),
]
