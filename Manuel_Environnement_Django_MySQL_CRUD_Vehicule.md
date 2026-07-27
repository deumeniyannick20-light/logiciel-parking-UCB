# Manuel de mise en place — Environnement Django + MySQL (XAMPP)

> Guide pas à pas pour un étudiant débutant en génie logiciel.  
> Objectif : installer l’environnement, créer une base MySQL, connecter Django, puis réaliser un **CRUD Véhicule** (création détaillée).

---

## Table des matières

1. [Prérequis](#1-prérequis)
2. [Installation de XAMPP](#2-installation-de-xampp)
3. [Création de la base de données MySQL](#3-création-de-la-base-de-données-mysql)
4. [Installation de Python et Django](#4-installation-de-python-et-django)
5. [Création du projet Django](#5-création-du-projet-django)
6. [Connexion Django ↔ MySQL](#6-connexion-django--mysql)
7. [CRUD Véhicule — créer un véhicule (Model / View / Controller)](#7-crud-véhicule--créer-un-véhicule)
8. [Compléter le CRUD (liste, modification, suppression)](#8-compléter-le-crud)
9. [Checklist finale](#9-checklist-finale)
10. [Erreurs fréquentes](#10-erreurs-fréquentes)

---

## 1. Prérequis

Avant de commencer, tu dois avoir :

| Élément | Pourquoi |
|---------|----------|
| Windows (ou Mac/Linux) | Machine de développement |
| Connexion Internet | Télécharger les outils |
| Droits d’administrateur | Installer XAMPP et Python |

**Vocabulaire utile**

| Terme | Signification simple |
|-------|----------------------|
| **Backend** | Partie serveur (Django) qui gère la logique et la base |
| **Base de données** | Endroit où on stocke les données (véhicules, places…) |
| **CRUD** | Create, Read, Update, Delete (Créer, Lire, Modifier, Supprimer) |
| **Migration** | Fichier qui crée/modifie les tables SQL à partir des modèles Django |

> **Note Django (MTV)** : Django n’utilise pas exactement MVC, mais **MTV** :
> - **Model** = modèle de données (équivalent Model)
> - **Template** = page HTML (équivalent View / affichage)
> - **View** = logique métier (équivalent Controller)
>
> Dans ce manuel, on dira parfois « controller » pour parler de la **view Django**, afin de coller à ton cours.

---

## 2. Installation de XAMPP

XAMPP fournit **Apache** (serveur web) et **MySQL / MariaDB** (base de données) + **phpMyAdmin** (interface pour gérer la base).

### Étape 2.1 — Télécharger XAMPP

1. Va sur : [https://www.apachefriends.org](https://www.apachefriends.org)
2. Télécharge la version **Windows**
3. Lance l’installateur (`.exe`)

### Étape 2.2 — Installer

1. Clique sur **Next**
2. Laisse coché au minimum : **Apache**, **MySQL**, **phpMyAdmin**
3. Choisis un dossier d’installation (ex. `C:\xampp`)
4. Termine l’installation

### Étape 2.3 — Démarrer MySQL

1. Ouvre **XAMPP Control Panel**
2. Clique sur **Start** à côté de **Apache**
3. Clique sur **Start** à côté de **MySQL**
4. Les pastilles doivent passer au **vert**

### Étape 2.4 — Vérifier phpMyAdmin

1. Ouvre ton navigateur
2. Va sur : [http://localhost/phpmyadmin](http://localhost/phpmyadmin)
3. Tu dois voir l’interface phpMyAdmin

✅ Si tu vois phpMyAdmin, XAMPP est prêt.

---

## 3. Création de la base de données MySQL

### Étape 3.1 — Créer la base

1. Dans phpMyAdmin, clique sur **Nouvelle base de données** (ou **New**)
2. Nom : `parking_ucb`
3. Interclassement (collation) : `utf8mb4_general_ci`
4. Clique sur **Créer**

### Étape 3.2 — (Optionnel) Créer un utilisateur dédié

Pour débuter, tu peux utiliser l’utilisateur par défaut :

| Paramètre | Valeur |
|-----------|--------|
| Host | `127.0.0.1` ou `localhost` |
| Port | `3306` |
| Utilisateur | `root` |
| Mot de passe | *(vide sous XAMPP par défaut)* |

> En production on ne laisse jamais un mot de passe vide. Pour un TP local, c’est acceptable.

✅ Base `parking_ucb` créée.

---

## 4. Installation de Python et Django

### Étape 4.1 — Installer Python

1. Télécharge Python 3.11+ : [https://www.python.org/downloads](https://www.python.org/downloads)
2. Lance l’installateur
3. **Important** : coche **Add Python to PATH**
4. Clique sur **Install Now**

Vérifie dans un terminal (PowerShell ou CMD) :

```bash
python --version
```

Tu dois voir quelque chose comme `Python 3.12.x`.

### Étape 4.2 — Créer un dossier projet

```bash
mkdir C:\projets\parking-ucb
cd C:\projets\parking-ucb
```

### Étape 4.3 — Créer un environnement virtuel

L’environnement virtuel isole les librairies du projet.

```bash
python -m venv venv
```

Activer l’environnement :

**PowerShell**

```powershell
.\venv\Scripts\Activate.ps1
```

**CMD**

```cmd
venv\Scripts\activate.bat
```

Quand c’est activé, tu vois `(venv)` devant la ligne de commande.

### Étape 4.4 — Installer Django et le connecteur MySQL

```bash
pip install django mysqlclient
```

> Si `mysqlclient` échoue sous Windows, utilise à la place :
>
> ```bash
> pip install django PyMySQL
> ```
>
> Puis ajoute dans `manage.py` (ou `__init__.py` du projet) :
>
> ```python
> import pymysql
> pymysql.install_as_MySQLdb()
> ```

Vérifie Django :

```bash
django-admin --version
```

✅ Django est installé.

---

## 5. Création du projet Django

### Étape 5.1 — Créer le projet

Toujours dans `C:\projets\parking-ucb` avec `(venv)` activé :

```bash
django-admin startproject config .
```

> Le point `.` signifie : créer le projet dans le dossier courant.

Structure obtenue :

```text
parking-ucb/
├── config/
│   ├── __init__.py
│   ├── settings.py      ← configuration
│   ├── urls.py          ← routes principales
│   └── ...
├── manage.py
└── venv/
```

### Étape 5.2 — Créer l’application `parc`

```bash
python manage.py startapp parc
```

Structure de l’app :

```text
parc/
├── models.py      ← Model (données)
├── views.py       ← Controller (logique)
├── admin.py
├── apps.py
└── ...
```

### Étape 5.3 — Déclarer l’application

Ouvre `config/settings.py` et ajoute `"parc"` dans `INSTALLED_APPS` :

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "parc",  # ← ton application
]
```

✅ Projet et application créés.

---

## 6. Connexion Django ↔ MySQL

### Étape 6.1 — Configurer la base dans `settings.py`

Remplace le bloc `DATABASES` (SQLite par défaut) par :

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "parking_ucb",
        "USER": "root",
        "PASSWORD": "",          # vide sous XAMPP par défaut
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}
```

### Étape 6.2 — Vérifier que MySQL tourne

Dans XAMPP Control Panel, **MySQL** doit être **Start** (vert).

### Étape 6.3 — Appliquer les migrations Django

```bash
python manage.py migrate
```

Django crée ses tables système (`auth_user`, etc.) dans `parking_ucb`.

Tu peux vérifier dans phpMyAdmin : base `parking_ucb` → tables présentes.

### Étape 6.4 — Créer un superutilisateur (admin)

```bash
python manage.py createsuperuser
```

Saisis un login, un email, un mot de passe.

### Étape 6.5 — Lancer le serveur

```bash
python manage.py runserver
```

Ouvre : [http://127.0.0.1:8000](http://127.0.0.1:8000)  
Admin : [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

✅ Django est connecté à MySQL.

---

## 7. CRUD Véhicule — créer un véhicule

On va créer un véhicule **étape par étape** :

1. **Model** → table en base  
2. **Formulaire** → saisie utilisateur  
3. **View (controller)** → logique  
4. **Template (vue)** → page HTML  
5. **URL** → adresse de la page  

---

### 7.1 — Model (`parc/models.py`)

Le **model** décrit les colonnes de la table `Véhicule`.

```python
from django.db import models


class Vehicule(models.Model):
    immatriculation = models.CharField(max_length=20, unique=True)
    marque = models.CharField(max_length=50)
    modele = models.CharField(max_length=50)
    couleur = models.CharField(max_length=30, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Véhicule"
        verbose_name_plural = "Véhicules"
        ordering = ["immatriculation"]

    def __str__(self):
        return f"{self.immatriculation} - {self.marque} {self.modele}"
```

**Explication débutant**

| Champ | Rôle |
|-------|------|
| `immatriculation` | Identifiant unique du véhicule |
| `marque` / `modele` | Infos du véhicule |
| `couleur` | Optionnel (`blank=True`) |
| `actif` | Soft delete possible plus tard |
| `__str__` | Texte affiché dans l’admin / listes |

---

### 7.2 — Créer la table en base (migrations)

```bash
python manage.py makemigrations parc
python manage.py migrate
```

Dans phpMyAdmin, tu dois voir la table `parc_vehicule`.

---

### 7.3 — Formulaire (`parc/forms.py`)

Crée le fichier `parc/forms.py` :

```python
from django import forms
from .models import Vehicule


class VehiculeForm(forms.ModelForm):
    class Meta:
        model = Vehicule
        fields = ["immatriculation", "marque", "modele", "couleur", "actif"]
        labels = {
            "immatriculation": "Immatriculation",
            "marque": "Marque",
            "modele": "Modèle",
            "couleur": "Couleur",
            "actif": "Actif",
        }
        widgets = {
            "immatriculation": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: CE 123 AB"}),
            "marque": forms.TextInput(attrs={"class": "form-control"}),
            "modele": forms.TextInput(attrs={"class": "form-control"}),
            "couleur": forms.TextInput(attrs={"class": "form-control"}),
        }
```

Le formulaire lit/écrit directement sur le **model**.

---

### 7.4 — View / Controller (`parc/views.py`)

La **view Django** joue le rôle de **controller** : elle reçoit la requête, traite, renvoie une page.

```python
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import VehiculeForm
from .models import Vehicule


def vehicule_creer(request):
    """
    CREATE — Créer un véhicule
    GET  : affiche le formulaire vide
    POST : valide et enregistre en base
    """
    if request.method == "POST":
        form = VehiculeForm(request.POST)
        if form.is_valid():
            form.save()  # INSERT dans MySQL
            messages.success(request, "Véhicule créé avec succès.")
            return redirect("vehicule_liste")
    else:
        form = VehiculeForm()

    return render(request, "parc/vehicule_form.html", {"form": form, "titre": "Ajouter un véhicule"})
```

**Déroulement (comme un controller)**

```text
1. L'utilisateur ouvre /vehicules/creer/
2. Si GET  → afficher formulaire vide
3. Si POST → récupérer les données
4. Valider le formulaire
5. Sauvegarder dans MySQL (model.save)
6. Rediriger vers la liste
```

---

### 7.5 — Template / Vue (`parc/templates/parc/vehicule_form.html`)

Crée les dossiers :

```text
parc/
└── templates/
    └── parc/
        └── vehicule_form.html
```

Contenu de `vehicule_form.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{{ titre }}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 520px; margin: 40px auto; }
    label { display: block; margin-top: 12px; font-weight: bold; }
    input[type="text"], input[type="checkbox"] { margin-top: 4px; }
    .form-control { width: 100%; padding: 8px; box-sizing: border-box; }
    button { margin-top: 16px; padding: 10px 16px; cursor: pointer; }
    .errors { color: #b00020; }
  </style>
</head>
<body>
  <h1>{{ titre }}</h1>

  <form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Enregistrer</button>
  </form>

  <p><a href="{% url 'vehicule_liste' %}">← Retour à la liste</a></p>
</body>
</html>
```

> `{% csrf_token %}` est **obligatoire** dans tout formulaire Django (sécurité).

---

### 7.6 — URLs (routes)

Crée `parc/urls.py` :

```python
from django.urls import path
from . import views

urlpatterns = [
    path("vehicules/creer/", views.vehicule_creer, name="vehicule_creer"),
]
```

Branche dans `config/urls.py` :

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("parc.urls")),
]
```

---

### 7.7 — Tester la création

1. Lance le serveur : `python manage.py runserver`
2. Ouvre : [http://127.0.0.1:8000/vehicules/creer/](http://127.0.0.1:8000/vehicules/creer/)
3. Remplis :
   - Immatriculation : `CE 123 AB`
   - Marque : `Toyota`
   - Modèle : `Corolla`
   - Couleur : `Gris`
4. Clique sur **Enregistrer**
5. Vérifie dans phpMyAdmin → table `parc_vehicule`

✅ **Create** fonctionne.

---

### Récapitulatif Model / View / Controller

| Couche cours | Fichier Django | Rôle |
|--------------|----------------|------|
| **Model** | `parc/models.py` | Structure des données + table MySQL |
| **Controller** | `parc/views.py` | Traite la requête, valide, sauvegarde |
| **View** | `templates/...html` | Affiche le formulaire à l’utilisateur |
| **Route** | `urls.py` | Relie l’URL à la view |

```text
Navigateur
    │
    ▼
 URL (/vehicules/creer/)
    │
    ▼
 View / Controller (views.py)
    │
    ├── lit/écrit ──► Model (models.py) ──► MySQL
    │
    └── renvoie ──► Template HTML (vue)
```

---

## 8. Compléter le CRUD

Ajoute dans `parc/views.py` :

```python
from django.shortcuts import get_object_or_404


def vehicule_liste(request):
    """READ — Liste tous les véhicules"""
    vehicules = Vehicule.objects.all()
    return render(request, "parc/vehicule_liste.html", {"vehicules": vehicules})


def vehicule_modifier(request, pk):
    """UPDATE — Modifier un véhicule"""
    vehicule = get_object_or_404(Vehicule, pk=pk)
    if request.method == "POST":
        form = VehiculeForm(request.POST, instance=vehicule)
        if form.is_valid():
            form.save()
            messages.success(request, "Véhicule modifié.")
            return redirect("vehicule_liste")
    else:
        form = VehiculeForm(instance=vehicule)
    return render(request, "parc/vehicule_form.html", {"form": form, "titre": "Modifier le véhicule"})


def vehicule_supprimer(request, pk):
    """DELETE — Supprimer un véhicule"""
    vehicule = get_object_or_404(Vehicule, pk=pk)
    if request.method == "POST":
        vehicule.delete()
        messages.success(request, "Véhicule supprimé.")
        return redirect("vehicule_liste")
    return render(request, "parc/vehicule_confirm_delete.html", {"vehicule": vehicule})
```

Mets à jour `parc/urls.py` :

```python
urlpatterns = [
    path("vehicules/", views.vehicule_liste, name="vehicule_liste"),
    path("vehicules/creer/", views.vehicule_creer, name="vehicule_creer"),
    path("vehicules/<int:pk>/modifier/", views.vehicule_modifier, name="vehicule_modifier"),
    path("vehicules/<int:pk>/supprimer/", views.vehicule_supprimer, name="vehicule_supprimer"),
]
```

### Template liste — `parc/templates/parc/vehicule_liste.html`

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Liste des véhicules</title>
</head>
<body>
  <h1>Véhicules</h1>
  <p><a href="{% url 'vehicule_creer' %}">+ Ajouter</a></p>

  <table border="1" cellpadding="8">
    <tr>
      <th>Immatriculation</th>
      <th>Marque</th>
      <th>Modèle</th>
      <th>Couleur</th>
      <th>Actions</th>
    </tr>
    {% for v in vehicules %}
    <tr>
      <td>{{ v.immatriculation }}</td>
      <td>{{ v.marque }}</td>
      <td>{{ v.modele }}</td>
      <td>{{ v.couleur }}</td>
      <td>
        <a href="{% url 'vehicule_modifier' v.pk %}">Modifier</a> |
        <a href="{% url 'vehicule_supprimer' v.pk %}">Supprimer</a>
      </td>
    </tr>
    {% empty %}
    <tr><td colspan="5">Aucun véhicule.</td></tr>
    {% endfor %}
  </table>
</body>
</html>
```

### Template suppression — `parc/templates/parc/vehicule_confirm_delete.html`

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Supprimer</title>
</head>
<body>
  <h1>Supprimer le véhicule ?</h1>
  <p>{{ vehicule }}</p>
  <form method="post">
    {% csrf_token %}
    <button type="submit">Oui, supprimer</button>
    <a href="{% url 'vehicule_liste' %}">Annuler</a>
  </form>
</body>
</html>
```

### (Bonus) Admin Django

Dans `parc/admin.py` :

```python
from django.contrib import admin
from .models import Vehicule

admin.site.register(Vehicule)
```

Tu pourras aussi gérer les véhicules via `/admin/`.

---

## 9. Checklist finale

- [ ] XAMPP installé, Apache + MySQL démarrés
- [ ] Base `parking_ucb` créée dans phpMyAdmin
- [ ] Python installé + PATH configuré
- [ ] Environnement virtuel `venv` créé et activé
- [ ] Django + connecteur MySQL installés
- [ ] Projet `config` + app `parc` créés
- [ ] `DATABASES` configuré vers MySQL
- [ ] `migrate` exécuté sans erreur
- [ ] Model `Vehicule` migré
- [ ] Formulaire + view + template + URL de création OK
- [ ] Liste / modifier / supprimer fonctionnels
- [ ] Test manuel dans le navigateur + vérif phpMyAdmin

---

## 10. Erreurs fréquentes

| Erreur | Cause probable | Solution |
|--------|----------------|----------|
| `Can't connect to MySQL` | MySQL XAMPP arrêté | Start MySQL dans XAMPP |
| `No module named 'MySQLdb'` | Connecteur manquant | `pip install mysqlclient` ou PyMySQL |
| `Access denied for user 'root'` | Mot de passe incorrect | Vérifie `PASSWORD` dans `settings.py` |
| Page 404 | URL non déclarée | Vérifie `parc/urls.py` et `include` |
| `CSRF verification failed` | Token manquant | Ajoute `{% csrf_token %}` dans le form |
| Template not found | Mauvais chemin | `parc/templates/parc/...` |
| `UNIQUE constraint` | Immatriculation déjà existante | Change l’immatriculation |

---

## Commandes utiles (aide-mémoire)

```bash
# Activer l'environnement
.\venv\Scripts\Activate.ps1

# Installer les dépendances
pip install django mysqlclient

# Migrations
python manage.py makemigrations
python manage.py migrate

# Lancer le serveur
python manage.py runserver

# Créer un admin
python manage.py createsuperuser
```

---

## Prochaine étape (projet parking UCB)

Une fois le CRUD Véhicule maîtrisé, tu pourras ajouter dans le même esprit :

1. Model `Personnel`
2. Model `Zone` / `Parking` / `PlaceParking` / `Poste`
3. Model `Occupation` (entrée / sortie)
4. Pages pour enregistrer une entrée et une sortie

Référence UML : `Diagrammes_UML_Gestion_Parking_UCB.md`
