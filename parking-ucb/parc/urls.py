from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

#urlpatterns = [
    path("accounts/login/", auth_views.LoginView.as_view(template_name="parc/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page='login'), name="logout"),
    path("", views.vehicule_liste, name="vehicule_liste"),
    # path("vehicules/", views.vehicule_liste, name="vehicule_liste"),
    path("vehicules/creer/", views.vehicule_creer, name="vehicule_creer"),
    path("vehicules/<int:pk>/modifier/", views.vehicule_modifier, name="vehicule_modifier"),
    path("vehicules/<int:pk>/supprimer/", views.vehicule_supprimer, name="vehicule_supprimer"),
]



urlpatterns = [
   path("accounts/login/", auth_views.LoginView.as_view(template_name="parc/login.html"), name="login"),
   path("accounts/logout/", auth_views.LogoutView.as_view(next_page='login'), name="logout"),
   path("", views.home, name="home"),
   path("vehicules/", views.vehicule_liste, name="vehicule_liste"),
   path("vehicules/creer/", views.vehicule_creer, name="vehicule_creer"),
   path("vehicules/<int:pk>/modifier/", views.vehicule_modifier, name="vehicule_modifier"),
   path("vehicules/<int:pk>/supprimer/", views.vehicule_supprimer, name="vehicule_supprimer"),
   path("personnels/", views.personnel_liste, name="personnel_liste"),
   path("personnels/creer/", views.personnel_creer, name="personnel_creer"),
   path("personnels/<int:pk>/modifier/", views.personnel_modifier, name="personnel_modifier"),
   path("personnels/<int:pk>/supprimer/", views.personnel_supprimer, name="personnel_supprimer"),
 ]



urlpatterns = [
    path("accounts/login/", auth_views.LoginView.as_view(template_name="parc/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page='login'), name="logout"),
    path("", views.home, name="home"),
    path("vehicules/", views.vehicule_liste, name="vehicule_liste"),
    path("vehicules/creer/", views.vehicule_creer, name="vehicule_creer"),
    path("vehicules/<int:pk>/modifier/", views.vehicule_modifier, name="vehicule_modifier"),
    path("vehicules/<int:pk>/supprimer/", views.vehicule_supprimer, name="vehicule_supprimer"),
    path("personnels/", views.personnel_liste, name="personnel_liste"),
    path("personnels/creer/", views.personnel_creer, name="personnel_creer"),
    path("personnels/<int:pk>/modifier/", views.personnel_modifier, name="personnel_modifier"),
    path("personnels/<int:pk>/supprimer/", views.personnel_supprimer, name="personnel_supprimer"),
    path("zones/", views.zone_liste, name="zone_liste"),
    path("zones/creer/", views.zone_creer, name="zone_creer"),
    path("zones/<int:pk>/modifier/", views.zone_modifier, name="zone_modifier"),
    path("zones/<int:pk>/supprimer/", views.zone_supprimer, name="zone_supprimer"),
]