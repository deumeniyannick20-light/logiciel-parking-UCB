(function () {
  'use strict';

  function basculerVisibilite(bouton) {
    var conteneur = bouton.closest('.ucb-password-field');
    if (!conteneur) return;
    var input = conteneur.querySelector('input');
    if (!input) return;

    var visible = input.type === 'text';
    input.type = visible ? 'password' : 'text';
    bouton.classList.toggle('ucb-password-visible', !visible);
    bouton.setAttribute(
      'aria-label',
      visible ? 'Afficher le mot de passe' : 'Masquer le mot de passe'
    );
    bouton.setAttribute(
      'title',
      visible ? 'Afficher le mot de passe' : 'Masquer le mot de passe'
    );
  }

  document.addEventListener('click', function (event) {
    var bouton = event.target.closest('.ucb-password-toggle');
    if (!bouton) return;
    event.preventDefault();
    basculerVisibilite(bouton);
  });
})();
