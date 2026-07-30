(function () {
  'use strict';

  function normaliser(texte) {
    return (texte || '')
      .toString()
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function sousSuite(texte, motif) {
    if (!motif) return true;
    var position = 0;
    for (var i = 0; i < motif.length; i++) {
      var index = texte.indexOf(motif.charAt(i), position);
      if (index === -1) return false;
      position = index + 1;
    }
    return true;
  }

  function texteLigne(ligne) {
    var cellules = ligne.querySelectorAll('td');
    var morceaux = [];
    cellules.forEach(function (cellule) {
      if (cellule.querySelector('.btn')) return;
      var texte = (cellule.textContent || '').replace(/\s+/g, ' ').trim();
      if (texte) morceaux.push(texte);
    });
    var extra = ligne.getAttribute('data-recherche-extra') || '';
    if (extra) morceaux.push(extra);
    return morceaux.join(' ');
  }

  function libelleLigne(ligne) {
    var premiere = ligne.querySelector('td');
    return premiere ? premiere.textContent.replace(/\s+/g, ' ').trim() : texteLigne(ligne);
  }

  function scoreCorrespondance(texte, requete) {
    var source = normaliser(texte);
    var q = normaliser(requete);
    if (!q) return 1;
    if (source.includes(q)) return 1000 - source.indexOf(q);
    var mots = q.split(' ').filter(Boolean);
    var score = 0;
    for (var i = 0; i < mots.length; i++) {
      var mot = mots[i];
      if (source.includes(mot)) {
        score += 120;
        continue;
      }
      if (sousSuite(source, mot)) {
        score += 60;
        continue;
      }
      return 0;
    }
    return score;
  }

  function correspond(texte, requete) {
    return scoreCorrespondance(texte, requete) > 0;
  }

  function initialiserBloc(bloc) {
    var table = bloc.querySelector('table');
    var barre = bloc.querySelector('[data-ucb-liste-recherche-bar]');
    if (!table || !barre) return;

    var loupe = barre.querySelector('.ucb-liste-recherche-loupe');
    var panel = barre.querySelector('.ucb-liste-recherche-panel');
    var input = barre.querySelector('.ucb-liste-recherche-input');
    var fermer = barre.querySelector('.ucb-liste-recherche-fermer');
    var suggestions = barre.querySelector('.ucb-liste-recherche-suggestions');
    var messageVide = barre.querySelector('.ucb-liste-recherche-vide');
    var lignes = Array.prototype.slice.call(table.querySelectorAll('tbody tr'));

    if (!lignes.length) {
      barre.hidden = true;
      return;
    }

    function ouvrir() {
      panel.classList.remove('ucb-liste-recherche-panel--ferme');
      input.focus();
    }

    function fermerPanel() {
      panel.classList.add('ucb-liste-recherche-panel--ferme');
      input.value = '';
      filtrer('');
    }

    function surligner(ligne) {
      lignes.forEach(function (tr) {
        tr.classList.remove('ucb-liste-recherche-cible');
      });
      ligne.classList.add('ucb-liste-recherche-cible');
      ligne.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function filtrer(requete) {
      var resultats = [];
      lignes.forEach(function (ligne) {
        var texte = texteLigne(ligne);
        var score = scoreCorrespondance(texte, requete);
        if (!normaliser(requete) || score > 0) {
          ligne.hidden = false;
          if (normaliser(requete)) {
            resultats.push({ ligne: ligne, score: score, libelle: libelleLigne(ligne) });
          }
        } else {
          ligne.hidden = true;
          ligne.classList.remove('ucb-liste-recherche-cible');
        }
      });

      resultats.sort(function (a, b) {
        return b.score - a.score || a.libelle.localeCompare(b.libelle, 'fr');
      });

      suggestions.innerHTML = '';
      var afficherSuggestions = normaliser(requete).length > 0;
      suggestions.hidden = !afficherSuggestions || !resultats.length;
      messageVide.hidden = !afficherSuggestions || resultats.length > 0;

      if (afficherSuggestions) {
        resultats.slice(0, 8).forEach(function (item) {
          var li = document.createElement('li');
          var bouton = document.createElement('button');
          bouton.type = 'button';
          bouton.className = 'ucb-liste-recherche-suggestion';
          bouton.textContent = item.libelle;
          bouton.addEventListener('click', function () {
            input.value = item.libelle;
            filtrer(item.libelle);
            surligner(item.ligne);
          });
          li.appendChild(bouton);
          suggestions.appendChild(li);
        });
      }
    }

    loupe.addEventListener('click', function () {
      if (panel.classList.contains('ucb-liste-recherche-panel--ferme')) {
        ouvrir();
      } else {
        fermerPanel();
      }
    });

    fermer.addEventListener('click', fermerPanel);

    input.addEventListener('input', function () {
      filtrer(input.value);
    });

    input.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        fermerPanel();
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.ucb-liste-avec-recherche').forEach(initialiserBloc);
  });
})();
