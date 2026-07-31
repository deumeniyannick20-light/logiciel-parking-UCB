(function () {
  'use strict';

  var champNom = document.getElementById('id_nom');
  var champPrenom = document.getElementById('id_prenom');
  var champPoste = document.getElementById('id_poste_obj');
  var champEmail = document.getElementById('id_email');
  if (!champNom || !champPrenom || !champPoste || !champEmail) return;
  if (champEmail.form && champEmail.form.dataset.personnelModification === '1') return;

  var emailModifieManuellement = Boolean(champEmail.value.trim());
  var derniereProposition = '';

  function fragmentEmail(valeur) {
    return valeur
      .trim()
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]/g, '');
  }

  function forcerMinuscules(champ) {
    var valeur = champ.value;
    var minuscule = valeur.toLowerCase();
    if (valeur !== minuscule) {
      champ.value = minuscule;
    }
    return minuscule.trim();
  }

  function proposerEmail() {
    if (emailModifieManuellement) return;

    var nom = fragmentEmail(champNom.value);
    var prenom = fragmentEmail(champPrenom.value);
    var poste = champPoste.value;

    if (!nom || !prenom || !poste) return;

    var proposition = (nom + '.' + prenom + '@ucb.local').toLowerCase();
    derniereProposition = proposition;
    champEmail.value = proposition;
  }

  champEmail.addEventListener('input', function () {
    var valeur = forcerMinuscules(champEmail);
    if (!valeur) {
      emailModifieManuellement = false;
      proposerEmail();
      return;
    }
    emailModifieManuellement = valeur !== derniereProposition;
  });

  champNom.addEventListener('input', proposerEmail);
  champNom.addEventListener('change', proposerEmail);
  champPrenom.addEventListener('input', proposerEmail);
  champPrenom.addEventListener('change', proposerEmail);
  champPoste.addEventListener('change', proposerEmail);

  var formulaire = champNom.closest('form');
  if (formulaire) {
    formulaire.addEventListener('ucb-formulaire-restaure', function () {
      emailModifieManuellement = Boolean(champEmail.value.trim());
      proposerEmail();
    });
  }

  function demarrer() {
    if (champEmail.value.trim()) {
      forcerMinuscules(champEmail);
    }
    if (!emailModifieManuellement) {
      proposerEmail();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', demarrer);
  } else {
    demarrer();
  }
})();
