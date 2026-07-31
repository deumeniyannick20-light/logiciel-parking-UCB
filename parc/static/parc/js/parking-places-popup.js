(function () {
  'use strict';

  var popup = document.getElementById('ucb-parking-places-popup');
  if (!popup) {
    return;
  }

  if (popup.parentElement !== document.body) {
    document.body.appendChild(popup);
  }

  var entete = document.getElementById('ucb-parking-places-popup-entete');
  var liste = document.getElementById('ucb-parking-places-popup-liste');
  var badgeActif = null;
  var cache = {};
  var positionActuelle = { left: 0, top: 0 };
  var deplacementActif = false;
  var offsetDeplacementX = 0;
  var offsetDeplacementY = 0;
  var timerAppuiLong = null;
  var pretADeplacer = false;
  var DELAI_APPUILONG_MS = 450;

  function echapperHtml(texte) {
    return String(texte)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function mesurerPopup() {
    var etaitCache = popup.hidden;
    var visibilite = popup.style.visibility;
    popup.hidden = false;
    popup.style.visibility = 'hidden';
    popup.style.left = '-9999px';
    popup.style.top = '0';
    var rect = popup.getBoundingClientRect();
    popup.style.visibility = visibilite || '';
    if (etaitCache) {
      popup.hidden = true;
    }
    return { largeur: rect.width, hauteur: rect.height };
  }

  function appliquerPosition(left, top) {
    var marge = 8;
    var largeur = popup.offsetWidth;
    var hauteur = popup.offsetHeight;
    if (!largeur || !hauteur) {
      var dimensions = mesurerPopup();
      largeur = dimensions.largeur;
      hauteur = dimensions.hauteur;
    }
    var maxLeft = Math.max(marge, window.innerWidth - largeur - marge);
    var maxTop = Math.max(marge, window.innerHeight - hauteur - marge);

    positionActuelle.left = Math.min(Math.max(marge, left), maxLeft);
    positionActuelle.top = Math.min(Math.max(marge, top), maxTop);
    popup.style.left = positionActuelle.left + 'px';
    popup.style.top = positionActuelle.top + 'px';
    popup.style.visibility = 'visible';
  }

  function positionnerAuClic(clientX, clientY) {
    popup.hidden = false;
    popup.setAttribute('aria-hidden', 'false');

    var dimensions = mesurerPopup();
    popup.hidden = false;
    var marge = 8;
    var left = clientX;
    var top = clientY;

    if (left + dimensions.largeur > window.innerWidth - marge) {
      left = clientX - dimensions.largeur;
    }
    if (top + dimensions.hauteur > window.innerHeight - marge) {
      top = clientY - dimensions.hauteur;
    }

    appliquerPosition(left, top);
  }

  function repositionnerPopup() {
    appliquerPosition(positionActuelle.left, positionActuelle.top);
  }

  function arreterDeplacement() {
    if (!deplacementActif) {
      return;
    }
    deplacementActif = false;
    document.removeEventListener('mousemove', onDeplacement);
    document.removeEventListener('mouseup', arreterDeplacement);
    popup.classList.remove('ucb-parking-places-popup--deplacement');
  }

  function onDeplacement(e) {
    appliquerPosition(e.clientX - offsetDeplacementX, e.clientY - offsetDeplacementY);
  }

  function demarrerDeplacement(e) {
    if (e.button !== 0) {
      return;
    }
    e.preventDefault();
    e.stopPropagation();

    var rect = popup.getBoundingClientRect();
    offsetDeplacementX = e.clientX - rect.left;
    offsetDeplacementY = e.clientY - rect.top;
    deplacementActif = true;
    popup.classList.add('ucb-parking-places-popup--deplacement');
    document.addEventListener('mousemove', onDeplacement);
    document.addEventListener('mouseup', arreterDeplacement);
    onDeplacement(e);
  }

  function annulerAppuiLong() {
    if (timerAppuiLong) {
      clearTimeout(timerAppuiLong);
      timerAppuiLong = null;
    }
  }

  function fermerPopup() {
    if (deplacementActif) {
      return;
    }
    annulerAppuiLong();
    popup.hidden = true;
    popup.setAttribute('aria-hidden', 'true');
    popup.classList.remove('ucb-parking-places-popup--deplacement');
    if (badgeActif) {
      badgeActif.setAttribute('aria-expanded', 'false');
      badgeActif = null;
    }
  }

  function afficherChargement(nomParking) {
    entete.textContent = nomParking;
    liste.innerHTML = '<li class="ucb-parking-places-popup__chargement">' +
      '<i class="fas fa-spinner fa-spin mr-2"></i>Chargement…</li>';
  }

  function afficherErreur(message) {
    liste.innerHTML = '<li class="ucb-parking-places-popup__vide text-danger">' +
      (message || 'Impossible de charger les places.') + '</li>';
  }

  function lignePlace(place, reserve) {
    var numero = 'Place N°' + echapperHtml(place.numero);
    var statutCls = place.statut === 'occupee' ? 'ucb-place-statut--occupee' : 'ucb-place-statut--libre';
    var details = '';

    if (reserve) {
      details = place.poste
        ? '<span class="ucb-parking-places-popup__poste">' + echapperHtml(place.poste) + '</span>'
        : '<span class="ucb-parking-places-popup__poste ucb-parking-places-popup__poste--vide">— Aucun poste —</span>';
    } else {
      details = '<span class="ucb-place-statut ' + statutCls + '">' +
        echapperHtml(place.statut_libelle) + '</span>';
    }

    return '<li class="ucb-parking-places-popup__item">' +
      '<span class="ucb-parking-places-popup__numero">' + numero + '</span>' +
      details +
      '</li>';
  }

  function afficherPlaces(payload) {
    var parking = payload.parking;
    var places = payload.places || [];
    var libelleType = parking.reserve ? 'Réservé' : 'Universel';
    entete.textContent = parking.nom + ' (' + libelleType + ')';

    if (!places.length) {
      liste.innerHTML = '<li class="ucb-parking-places-popup__vide">Aucune place active enregistrée.</li>';
      return;
    }

    liste.innerHTML = places.map(function (place) {
      return lignePlace(place, parking.reserve);
    }).join('');
  }

  function ouvrirPopup(badge, clientX, clientY) {
    var parkingId = badge.getAttribute('data-parking-id');
    var nomParking = badge.getAttribute('data-parking-nom') || 'Parking';

    if (badgeActif === badge && !popup.hidden && !deplacementActif) {
      fermerPopup();
      return;
    }

    if (badgeActif && badgeActif !== badge) {
      badgeActif.setAttribute('aria-expanded', 'false');
    }

    arreterDeplacement();
    badgeActif = badge;
    badge.setAttribute('aria-expanded', 'true');
    afficherChargement(nomParking);
    positionnerAuClic(clientX, clientY);

    function apresRendu() {
      if (badgeActif !== badge) {
        return;
      }
      repositionnerPopup();
    }

    if (cache[parkingId]) {
      afficherPlaces(cache[parkingId]);
      requestAnimationFrame(apresRendu);
      return;
    }

    fetch('/api/parkings/' + encodeURIComponent(parkingId) + '/places/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('HTTP ' + response.status);
        }
        return response.json();
      })
      .then(function (payload) {
        cache[parkingId] = payload;
        if (badgeActif !== badge) {
          return;
        }
        afficherPlaces(payload);
        requestAnimationFrame(apresRendu);
      })
      .catch(function () {
        if (badgeActif === badge) {
          afficherErreur();
          requestAnimationFrame(apresRendu);
        }
      });
  }

  document.addEventListener('click', function (e) {
    var badge = e.target.closest('.ucb-parking-places-badge');
    if (badge) {
      e.preventDefault();
      e.stopPropagation();
      ouvrirPopup(badge, e.clientX, e.clientY);
      return;
    }
    if (!popup.hidden && !e.target.closest('#ucb-parking-places-popup') && !deplacementActif) {
      fermerPopup();
    }
  });

  popup.addEventListener('mouseleave', function () {
    if (!deplacementActif) {
      fermerPopup();
    }
  });

  entete.addEventListener('dblclick', function (e) {
    e.preventDefault();
    e.stopPropagation();
    pretADeplacer = true;
  });

  entete.addEventListener('mousedown', function (e) {
    if (e.button !== 0) {
      return;
    }
    annulerAppuiLong();
    if (pretADeplacer) {
      pretADeplacer = false;
      demarrerDeplacement(e);
      return;
    }
    var evenement = e;
    timerAppuiLong = setTimeout(function () {
      timerAppuiLong = null;
      demarrerDeplacement(evenement);
    }, DELAI_APPUILONG_MS);
  });

  entete.addEventListener('mouseup', annulerAppuiLong);
  entete.addEventListener('mouseleave', annulerAppuiLong);

  window.addEventListener('resize', function () {
    if (!popup.hidden) {
      repositionnerPopup();
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !popup.hidden) {
      if (deplacementActif) {
        arreterDeplacement();
      } else {
        fermerPopup();
      }
    }
  });
})();
