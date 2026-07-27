# Diagrammes UML — Gestion des occupations de parking UCB

> Mini-projet : suivi de la **disponibilité** et de l’**occupation** des places de parking (entrée / sortie), zones, places **affectées à un poste** (DG, DGA, DRH…) et parking cadres.

---

## 1. Diagramme de cas d'utilisation

```mermaid
flowchart LR
  subgraph Acteurs
    G[Gestionnaire parking]
    A[Agent / Gardien]
    S[Superviseur]
  end

  subgraph Systeme["Système Gestion Parking UCB"]
    UC1((Gérer les zones))
    UC2((Gérer les parkings))
    UC3((Gérer les places))
    UC4((Affecter une place à un poste))
    UC5((Gérer le personnel))
    UC6((Gérer les véhicules))
    UC7((Enregistrer une entrée))
    UC8((Enregistrer une sortie))
    UC9((Consulter disponibilités))
    UC10((Consulter qui est garé où))
    UC11((Consulter historique occupations))
  end

  G --> UC1
  G --> UC2
  G --> UC3
  G --> UC4
  G --> UC5
  G --> UC6
  G --> UC9
  G --> UC10
  G --> UC11

  A --> UC7
  A --> UC8
  A --> UC9
  A --> UC10

  S --> UC9
  S --> UC10
  S --> UC11

  UC7 -.->|inclut| UC9
  UC4 -.->|étend| UC3
```

### Acteurs

| Acteur | Rôle |
|--------|------|
| **Gestionnaire parking** | Paramètre zones, parkings, places, postes, personnel et véhicules |
| **Agent / Gardien** | Enregistre les entrées et sorties sur le terrain |
| **Superviseur** | Consulte disponibilités, occupations en cours et historiques |

### Cas d'utilisation principaux

| CU | Description |
|----|-------------|
| Gérer zones / parkings / places | CRUD du référentiel spatial |
| Affecter une place à un poste | Lier une place à un poste (DG, DGA, DRH…) — pas de réservation |
| Gérer personnel / véhicules | Fiches employés (avec poste) et véhicules associés |
| Enregistrer entrée | Véhicule + place → statut **OCCUPE**, heure d'entrée |
| Enregistrer sortie | Clôturer l'occupation → statut **LIBRE**, heure de sortie |
| Consulter disponibilités | Places libres / occupées par parking ou zone |
| Consulter qui est garé où | Véhicule, propriétaire, place, depuis quelle heure |
| Consulter historique | Occupations passées (entrée / sortie) |

---

## 2. Diagramme de classes

```mermaid
classDiagram
  direction TB

  class Zone {
    -id: UUID
    -code: String
    -libelle: String
    -description: String
    -actif: Boolean
  }

  class Parking {
    -id: UUID
    -code: String
    -libelle: String
    -typeParking: TypeParking
    -capacite: Integer
    -actif: Boolean
  }

  class PlaceParking {
    -id: UUID
    -numero: String
    -statutOccupation: StatutOccupation
    -actif: Boolean
  }

  class Poste {
    -id: UUID
    -code: String
    -libelle: String
    -actif: Boolean
  }

  class TypeParking {
    <<enumeration>>
    STANDARD
    CADRE
    DIRECTION
  }

  class StatutOccupation {
    <<enumeration>>
    LIBRE
    OCCUPE
  }

  class Personnel {
    -id: UUID
    -matricule: String
    -nom: String
    -prenom: String
    -telephone: String
    -actif: Boolean
  }

  class Vehicule {
    -id: UUID
    -immatriculation: String
    -marque: String
    -modele: String
    -couleur: String
    -actif: Boolean
  }

  class Occupation {
    -id: UUID
    -heureEntree: DateTime
    -heureSortie: DateTime
    -dureeOccupation: Duration
    -observation: String
  }

  class Utilisateur {
    -id: UUID
    -login: String
    -motDePasseHash: String
    -role: RoleUtilisateur
    -actif: Boolean
  }

  class RoleUtilisateur {
    <<enumeration>>
    GESTIONNAIRE
    AGENT
    SUPERVISEUR
  }

  Zone "1" --> "*" Parking : contient
  Parking "1" --> "*" PlaceParking : dispose de
  Poste "0..1" --> "*" PlaceParking : affectée à
  Poste "1" --> "*" Personnel : occupe
  Personnel "1" --> "*" Vehicule : possède
  PlaceParking "1" --> "*" Occupation : historise
  Vehicule "1" --> "*" Occupation : occupe
  Utilisateur "1" --> "*" Occupation : enregistre
  Parking --> TypeParking
  PlaceParking --> StatutOccupation
  Utilisateur --> RoleUtilisateur
```

### Exemples de postes

| Code | Libellé |
|------|---------|
| DG | Directeur Général |
| DGA | Directeur Général Adjoint |
| DRH | Directeur des Ressources Humaines |
| … | Autres postes selon organigramme |

### Règles métier clés

1. Une **Zone** regroupe plusieurs **Parkings**.
2. Un **Parking** a un type : `STANDARD`, `CADRE` ou `DIRECTION`.
3. Le **statut d'occupation** d'une place est uniquement : `LIBRE` ou `OCCUPE`.
4. Une place **peut être affectée à un Poste** (DG, DGA, DRH…) — pas de mécanisme de réservation.
5. Un **Personnel** est rattaché à un **Poste** ; un **Véhicule** appartient à un Personnel.
6. Une **Occupation** lie Véhicule + Place + Agent : `heureEntree` à l'entrée, `heureSortie` à la sortie (`null` tant que le véhicule est garé).
7. À tout moment : **au plus une occupation ouverte** (`heureSortie` nulle) par place et par véhicule.
8. Contrôle optionnel à l'entrée : si la place a un poste, le personnel du véhicule devrait avoir le même poste.

---

## 3. Diagramme de séquence

Scénario complet : connexion → consultation → entrée → sortie.

```mermaid
sequenceDiagram
  actor Agent as Agent / Gestionnaire
  participant UI as Interface Web
  participant Auth as Authentification
  participant Sys as Système Parking

  Agent->>UI: Ouvre l'application
  UI-->>Agent: Affiche le formulaire de connexion
  Agent->>UI: Saisit son identifiant et son mot de passe
  UI->>Auth: Demande la vérification des identifiants
  alt Échec
    Auth-->>UI: Refuse l'accès
  else Succès
    Auth-->>UI: Valide la connexion
    UI-->>Agent: Affiche l'accueil
  end

  Agent->>UI: Consulte un parking ou une zone
  UI->>Sys: Demande l'état des places
  Sys-->>UI: Renvoie les places libres et occupées
  UI-->>Agent: Affiche les disponibilités

  Agent->>UI: Saisit l'immatriculation et la place
  UI->>Sys: Demande l'enregistrement de l'entrée
  Sys->>Sys: Vérifie que la place est libre
  Sys->>Sys: Enregistre l'heure d'entrée
  Sys->>Sys: Passe la place à occupé
  Sys-->>UI: Confirme l'enregistrement
  UI-->>Agent: Affiche la confirmation d'entrée

  Agent->>UI: Indique la place ou l'immatriculation
  UI->>Sys: Demande l'enregistrement de la sortie
  Sys->>Sys: Enregistre l'heure de sortie et calcule la durée
  Sys->>Sys: Passe la place à libre
  Sys-->>UI: Confirme avec la durée d'occupation
  UI-->>Agent: Affiche la confirmation de sortie

  Agent->>UI: Se déconnecte
  UI->>Auth: Ferme la session
  Auth-->>UI: Confirme la déconnexion
  UI-->>Agent: Retourne à l'écran de connexion
```

---

## 4. Diagrammes d'activité

### 4.1 Processus d'entrée véhicule

```mermaid
flowchart TD
  Start([Début]) --> Saisie[Saisir immatriculation et numéro de place]
  Saisie --> VerifVeh{Véhicule connu ?}
  VerifVeh -->|Non| CreerVeh[Créer fiche véhicule + lier personnel]
  VerifVeh -->|Oui| VerifPlace
  CreerVeh --> VerifPlace{Place existe et active ?}

  VerifPlace -->|Non| ErreurPlace[Refuser : place invalide]
  ErreurPlace --> FinErr([Fin])

  VerifPlace -->|Oui| Statut{Statut occupation}
  Statut -->|OCCUPE| RefusOcc[Refuser : déjà occupée]
  Statut -->|LIBRE| VerifPoste

  RefusOcc --> FinErr

  VerifPoste{Place affectée à un poste ?}
  VerifPoste -->|Oui| VerifMatch{Poste personnel = poste place ?}
  VerifPoste -->|Non| VerifVehOcc
  VerifMatch -->|Non| RefusPoste[Refuser ou alerter]
  VerifMatch -->|Oui| VerifVehOcc
  RefusPoste --> FinErr

  VerifVehOcc{Véhicule déjà garé ailleurs ?}
  VerifVehOcc -->|Oui| RefusDouble[Refuser]
  VerifVehOcc -->|Non| CreerOcc[Créer Occupation heureEntree]
  RefusDouble --> FinErr

  CreerOcc --> MajPlace[Passer place à OCCUPE]
  MajPlace --> Confirmer[Confirmer entrée + heure]
  Confirmer --> FinOk([Fin])
```

### 4.2 Processus de sortie véhicule

```mermaid
flowchart TD
  Start([Début]) --> Ident[Identifier place ou immatriculation]
  Ident --> Cherche{Occupation ouverte trouvée ?}
  Cherche -->|Non| Err[Refuser : aucune occupation]
  Err --> FinErr([Fin])

  Cherche -->|Oui| SaisieSortie[Enregistrer heure de sortie]
  SaisieSortie --> Calc[Calculer durée d'occupation]
  Calc --> StatutLibre[Statut occupation place = LIBRE]
  StatutLibre --> Confirm[Confirmer sortie]
  Confirm --> FinOk([Fin])
```

### 4.3 Suivi de disponibilité d'une place

```mermaid
flowchart TD
  Start([Début consultation]) --> Filtrer[Filtrer par Zone / Parking / Poste]
  Filtrer --> Charger[Charger places + occupations en cours]
  Charger --> Afficher[Afficher tableau de bord]

  Afficher --> Vue{Vue demandée}
  Vue -->|Disponibilité| Dispo[Compteurs : LIBRE / OCCUPE]
  Vue -->|Occupation live| Live[Place → Poste → Véhicule → Personnel → heure entrée]
  Vue -->|Historique| Hist[Liste occupations clôturées sur période]

  Dispo --> Fin([Fin])
  Live --> Fin
  Hist --> Fin
```

---

## 5. Synthèse du modèle de données (aperçu)

| Entité | Rôle |
|--------|------|
| `Zone` | Localisation géographique des parkings |
| `Parking` | Aire de stationnement (cadre, direction, standard) |
| `PlaceParking` | Emplacement unitaire ; éventuellement **affectée à un Poste** |
| `Poste` | Poste organisationnel (DG, DGA, DRH…) — pas de réservation |
| `Personnel` | Employé rattaché à un poste, propriétaire du véhicule |
| `Vehicule` | Immatriculation liée au personnel |
| `Occupation` | Mouvement entrée/sortie = cœur du suivi |
| `Utilisateur` | Agent / Gestionnaire / Superviseur |
