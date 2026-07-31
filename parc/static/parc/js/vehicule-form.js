(function () {
  'use strict';

  var selectTitulaire = document.getElementById('id_personnel');
  var listeChauffeurs = document.getElementById('id_chauffeurs');
  if (!selectTitulaire || !listeChauffeurs) return;

  var labelChauffeurs = document.querySelector('label[for="id_chauffeurs"]');
  var aideChauffeurs = document.getElementById('id_chauffeurs_helptext');
  if (aideChauffeurs) {
    aideChauffeurs.remove();
  }

  var aucunWrap = document.createElement('div');
  aucunWrap.className = 'ucb-chauffeur-aucun-option';
  aucunWrap.hidden = true;
  aucunWrap.innerHTML =
    '<label class="ucb-chauffeur-aucun-label">' +
    '<input type="checkbox" id="ucb-chauffeur-aucun" class="mr-2">' +
    '— Aucun chauffeur —</label>';
  listeChauffeurs.parentNode.insertBefore(aucunWrap, listeChauffeurs);

  var cbAucun = document.getElementById('ucb-chauffeur-aucun');

  function getCheckboxesChauffeurs() {
    return listeChauffeurs.querySelectorAll('input[type="checkbox"][name="chauffeurs"]');
  }

  function chauffeursActifsSelectionnes() {
    var selection = false;
    Array.prototype.forEach.call(getCheckboxesChauffeurs(), function (cb) {
      if (!cb.disabled && cb.checked) {
        selection = true;
      }
    });
    return selection;
  }

  function majAucunChauffeur() {
    if (!selectTitulaire.value) {
      aucunWrap.hidden = true;
      cbAucun.checked = false;
      return;
    }
    aucunWrap.hidden = false;
    cbAucun.checked = !chauffeursActifsSelectionnes();
  }

  function majChauffeurs() {
    var titulaireId = selectTitulaire.value;

    Array.prototype.forEach.call(getCheckboxesChauffeurs(), function (cb) {
      var item = cb.closest('#id_chauffeurs > div');
      if (titulaireId && cb.value === titulaireId) {
        cb.disabled = true;
        cb.checked = false;
        if (item) item.hidden = true;
      } else {
        cb.disabled = false;
        if (item) item.hidden = false;
      }
    });

    if (labelChauffeurs) {
      if (titulaireId) {
        labelChauffeurs.textContent = 'Chauffeurs (optionnel)';
      } else {
        labelChauffeurs.innerHTML =
          'Chauffeurs&nbsp;<span class="champ-obligatoire" aria-hidden="true">*</span>';
      }
    }

    majAucunChauffeur();
  }

  cbAucun.addEventListener('change', function () {
    if (!cbAucun.checked) {
      return;
    }
    Array.prototype.forEach.call(getCheckboxesChauffeurs(), function (cb) {
      cb.checked = false;
    });
  });

  listeChauffeurs.addEventListener('change', function (e) {
    var cible = e.target;
    if (!cible || cible.type !== 'checkbox' || cible.name !== 'chauffeurs') {
      return;
    }
    if (cible.checked) {
      cbAucun.checked = false;
    } else {
      majAucunChauffeur();
    }
  });

  selectTitulaire.addEventListener('change', majChauffeurs);

  var formulaire = selectTitulaire.closest('form');
  if (formulaire) {
    formulaire.addEventListener('ucb-formulaire-restaure', majChauffeurs);
  }

  function demarrer() {
    majChauffeurs();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', demarrer);
  } else {
    demarrer();
  }
})();
