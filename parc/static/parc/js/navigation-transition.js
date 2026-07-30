(function () {
  'use strict';

  var ORDRE_RUBRIQUES = [
    'home',
    'zones',
    'parkings',
    'postes',
    'personnels',
    'places',
    'vehicules',
    'utilisateurs',
    'occupations',
  ];

  var CLE_SESSION = 'ucb_menu_section';

  function indexRubrique(section) {
    return ORDRE_RUBRIQUES.indexOf(section || '');
  }

  function appliquerTransition() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return;
    }

    var actuelle = document.body.getAttribute('data-menu-actif') || '';
    var precedente = sessionStorage.getItem(CLE_SESSION) || '';

    if (actuelle && precedente && actuelle !== precedente) {
      var indexActuel = indexRubrique(actuelle);
      var indexPrecedent = indexRubrique(precedente);
      var contenu = document.getElementById('ucb-rubrique-contenu');

      if (contenu && indexActuel !== -1 && indexPrecedent !== -1) {
        if (indexActuel < indexPrecedent) {
          contenu.classList.add('ucb-rubrique-anim-montant');
        } else if (indexActuel > indexPrecedent) {
          contenu.classList.add('ucb-rubrique-anim-descendant');
        }
      }
    }

    if (actuelle) {
      sessionStorage.setItem(CLE_SESSION, actuelle);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', appliquerTransition);
  } else {
    appliquerTransition();
  }
})();
