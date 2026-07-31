(function () {
  'use strict';

  var blocConducteurs = document.getElementById('conducteurs-vehicules-data');
  var blocPlaces = document.getElementById('places-conducteurs-data');
  var selectVehicule = document.getElementById('id_vehicule');
  var selectConducteur = document.getElementById('id_conducteur_entree');
  var selectPlace = document.getElementById('id_place_parking');
  if (!selectVehicule || !selectConducteur) return;

  var carteConducteurs = {};
  var cartePlaces = { places_universelles: [], conducteurs: {} };

  if (blocConducteurs) {
    try {
      carteConducteurs = JSON.parse(blocConducteurs.textContent || '{}');
    } catch (e) {
      console.error('Conducteurs véhicules : JSON invalide', e);
    }
  }

  if (blocPlaces) {
    try {
      cartePlaces = JSON.parse(blocPlaces.textContent || '{}');
    } catch (e) {
      console.error('Places conducteurs : JSON invalide', e);
    }
  }

  function ajouterOption(select, valeur, libelle, selectionnee) {
    var option = document.createElement('option');
    option.value = valeur;
    option.textContent = libelle;
    if (selectionnee) {
      option.selected = true;
    }
    select.appendChild(option);
  }

  function majPlaces(placeSouhaitee) {
    if (!selectPlace) return;

    var valeurInitiale = placeSouhaitee != null ? placeSouhaitee : selectPlace.value;
    var conducteurId = selectConducteur.value;
    selectPlace.innerHTML = '';
    selectPlace.classList.remove('ucb-champ-desactive');
    selectPlace.removeAttribute('aria-readonly');

    if (!conducteurId) {
      ajouterOption(
        selectPlace,
        '',
        "— Sélectionnez d'abord le conducteur —",
        true
      );
      selectPlace.classList.add('ucb-champ-desactive');
      selectPlace.setAttribute('aria-readonly', 'true');
      return;
    }

    var info = (cartePlaces.conducteurs || {})[conducteurId];
    if (!info) {
      ajouterOption(selectPlace, '', '— Conducteur inconnu —', true);
      selectPlace.classList.add('ucb-champ-desactive');
      selectPlace.setAttribute('aria-readonly', 'true');
      return;
    }

    if (info.mode === 'reserve' && info.place) {
      var libelleReserve = info.place.label;
      if (!info.place.libre) {
        libelleReserve += ' (occupée)';
      }
      ajouterOption(selectPlace, String(info.place.id), libelleReserve, true);
      selectPlace.classList.add('ucb-champ-desactive');
      selectPlace.setAttribute('aria-readonly', 'true');
      return;
    }

    var universelles = cartePlaces.places_universelles || [];
    if (!universelles.length) {
      ajouterOption(selectPlace, '', '— Aucune place universelle libre —', true);
      selectPlace.classList.add('ucb-champ-desactive');
      selectPlace.setAttribute('aria-readonly', 'true');
      return;
    }

    ajouterOption(selectPlace, '', '— Sélectionner une place —', false);
    universelles.forEach(function (place) {
      var selectionnee = valeurInitiale && String(place.id) === String(valeurInitiale);
      ajouterOption(selectPlace, String(place.id), place.label, selectionnee);
    });

    if (valeurInitiale && universelles.some(function (place) {
      return String(place.id) === String(valeurInitiale);
    })) {
      selectPlace.value = valeurInitiale;
    }
  }

  function majConducteurs() {
    var valeurInitialeConducteur = selectConducteur.value;
    var valeurInitialePlace = selectPlace ? selectPlace.value : '';
    var options = carteConducteurs[selectVehicule.value] || [];

    selectConducteur.innerHTML = '';
    ajouterOption(
      selectConducteur,
      '',
      options.length
        ? '— Sélectionner le conducteur —'
        : "— Sélectionnez d'abord un véhicule —",
      false
    );

    options.forEach(function (item) {
      ajouterOption(selectConducteur, String(item.id), item.label, false);
    });

    if (valeurInitialeConducteur && options.some(function (item) {
      return String(item.id) === String(valeurInitialeConducteur);
    })) {
      selectConducteur.value = valeurInitialeConducteur;
    }

    majPlaces(valeurInitialePlace);
  }

  function synchroniserFormulaireEntree() {
    majConducteurs();
  }

  selectVehicule.addEventListener('change', majConducteurs);
  selectConducteur.addEventListener('change', majPlaces);

  var formulaire = selectVehicule.closest('form');
  if (formulaire) {
    formulaire.addEventListener('ucb-formulaire-restaure', synchroniserFormulaireEntree);
  }

  function demarrer() {
    synchroniserFormulaireEntree();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', demarrer);
  } else {
    demarrer();
  }
})();
