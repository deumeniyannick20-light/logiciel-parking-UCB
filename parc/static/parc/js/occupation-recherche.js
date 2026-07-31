(function () {
  'use strict';

  var COULEURS = {
    blue: '#4d7cfe',
    red: '#dc2626',
    teal: '#2dd4bf',
    grid: 'rgba(255,255,255,0.04)',
    muted: '#7c849a',
  };

  var scene = null;
  var dashboardMain = null;
  var etapePicker = null;
  var etapeDashboard = null;
  var listePanel = null;
  var listeUl = null;
  var vehicules = [];
  var vehiculeActif = null;
  var periodeActuelle = 'jour';
  var donneesVehicule = null;
  var charts = {};
  var filtreHistoriqueTimer = null;

  function $(id) {
    return document.getElementById(id);
  }

  function normaliser(texte) {
    return (texte || '')
      .toString()
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();
  }

  function ouvrirScene() {
    if (!scene) return;
    scene.hidden = false;
    scene.setAttribute('aria-hidden', 'false');
    document.body.classList.add('occupation-recherche-ouvert');
    if (dashboardMain) {
      dashboardMain.setAttribute('aria-hidden', 'true');
    }
    afficherEtapePicker();
    chargerVehicules();
    scene.scrollTop = 0;
  }

  function fermerScene() {
    if (!scene) return;
    scene.hidden = true;
    scene.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('occupation-recherche-ouvert');
    if (dashboardMain) {
      dashboardMain.removeAttribute('aria-hidden');
    }
    detruireGraphiques();
    vehiculeActif = null;
    donneesVehicule = null;
  }

  function afficherEtapePicker() {
    if (etapePicker) etapePicker.hidden = false;
    if (etapeDashboard) etapeDashboard.hidden = true;
    if (listePanel) listePanel.hidden = true;
    var trigger = $('occ-recherche-vehicule-trigger');
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
  }

  function afficherEtapeDashboard() {
    if (etapePicker) etapePicker.hidden = true;
    if (etapeDashboard) etapeDashboard.hidden = false;
  }

  function chargerVehicules() {
    fetch('/api/vehicules/recherche/', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        vehicules = data.vehicules || [];
        rendreListeVehicules(vehicules);
      })
      .catch(function () {
        vehicules = [];
        rendreListeVehicules([]);
      });
  }

  function rendreListeVehicules(liste) {
    if (!listeUl) return;
    listeUl.innerHTML = '';
    var filtre = $('occ-recherche-filtre-vehicules');
    var q = filtre ? normaliser(filtre.value) : '';
    var resultats = liste.filter(function (v) {
      if (!q) return true;
      var texte = normaliser(v.label + ' ' + v.immatriculation + ' ' + v.marque + ' ' + v.modele);
      return texte.indexOf(q) !== -1;
    });

    var vide = $('occ-recherche-liste-vide');
    if (vide) vide.hidden = resultats.length > 0;

    resultats.forEach(function (v) {
      var li = document.createElement('li');
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'occ-recherche-vehicule-item';
      btn.setAttribute('role', 'option');
      btn.dataset.id = String(v.id);
      btn.innerHTML =
        '<span class="occ-recherche-vehicule-item__label">' + escapeHtml(v.label) + '</span>' +
        (v.present
          ? '<span class="badge badge-success occ-recherche-vehicule-item__badge">Sur site</span>'
          : '<span class="badge badge-secondary occ-recherche-vehicule-item__badge">Absent</span>');
      btn.addEventListener('click', function () {
        selectionnerVehicule(v);
      });
      li.appendChild(btn);
      listeUl.appendChild(li);
    });
  }

  function escapeHtml(texte) {
    var div = document.createElement('div');
    div.textContent = texte;
    return div.innerHTML;
  }

  function selectionnerVehicule(vehicule) {
    vehiculeActif = vehicule;
    var placeholder = $('occ-recherche-vehicule-placeholder');
    if (placeholder) placeholder.textContent = vehicule.label;
    var trigger = $('occ-recherche-vehicule-trigger');
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
    if (listePanel) listePanel.hidden = true;
    afficherEtapeDashboard();
    var titre = $('occ-vehicule-titre');
    if (titre) titre.textContent = vehicule.label;
    var sousTitre = $('occ-vehicule-sous-titre');
    if (sousTitre) {
      sousTitre.textContent = vehicule.marque + ' ' + vehicule.modele +
        (vehicule.present ? ' — actuellement sur le site' : '');
    }
    chargerDashboardVehicule();
  }

  function urlDashboardVehicule() {
    if (!vehiculeActif) return '';
    var url = '/api/dashboard/vehicule/' + vehiculeActif.id + '/?periode=' + encodeURIComponent(periodeActuelle);
    var filtre = $('occ-historique-filtre');
    if (filtre && filtre.value.trim()) {
      url += '&q=' + encodeURIComponent(filtre.value.trim());
    }
    return url;
  }

  function chargerDashboardVehicule() {
    if (!vehiculeActif) return;
    fetch(urlDashboardVehicule(), { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        donneesVehicule = data;
        rendreEtatActuel(data.etat_actuel);
        rendreKpi(data.kpi);
        rendrePeriodeLibelle(data.periode_libelle);
        rendreHistorique(data.historique);
        rendreGraphiques(data);
      });
  }

  function rendreEtatActuel(etat) {
    var badge = $('occ-vehicule-etat-badge');
    var texte = $('occ-vehicule-etat-texte');
    var details = $('occ-vehicule-etat-details');
    if (!badge || !texte || !details) return;

    if (etat.present) {
      badge.className = 'occ-vehicule-etat__badge occ-vehicule-etat__badge--present';
      texte.textContent = 'Présent sur le site';
      details.innerHTML =
        '<div class="occ-vehicule-etat__ligne"><strong>Place :</strong> ' + escapeHtml(etat.place || '—') + '</div>' +
        '<div class="occ-vehicule-etat__ligne"><strong>Conducteur :</strong> ' + escapeHtml(etat.conducteur || '—') + '</div>' +
        '<div class="occ-vehicule-etat__ligne"><strong>Depuis :</strong> ' + escapeHtml(etat.depuis_label || '—') +
        ' <span class="text-muted">(' + escapeHtml(etat.duree || '') + ')</span></div>';
    } else {
      badge.className = 'occ-vehicule-etat__badge occ-vehicule-etat__badge--absent';
      texte.textContent = 'Absent du site';
      details.innerHTML = '<p class="mb-0 text-muted">Ce véhicule n\'a pas d\'occupation en cours.</p>';
    }
  }

  function rendreKpi(kpi) {
    if (!kpi) return;
    document.querySelectorAll('[data-occ-count]').forEach(function (el) {
      var cle = el.getAttribute('data-occ-count');
      if (kpi[cle] !== undefined) {
        el.textContent = String(kpi[cle]);
      }
    });
    document.querySelectorAll('[data-occ-text]').forEach(function (el) {
      var cle = el.getAttribute('data-occ-text');
      if (kpi[cle] !== undefined) {
        el.textContent = kpi[cle];
      }
    });
  }

  function rendrePeriodeLibelle(libelle) {
    var el = $('occ-vehicule-periode-libelle');
    if (el) el.textContent = libelle || '';
  }

  function rendreHistorique(lignes) {
    var tbody = $('occ-historique-tbody');
    var vide = $('occ-historique-vide');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!lignes || !lignes.length) {
      if (vide) vide.hidden = false;
      return;
    }
    if (vide) vide.hidden = true;
    lignes.forEach(function (ligne) {
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + escapeHtml(ligne.place) + '</td>' +
        '<td>' + escapeHtml(ligne.conducteur_entree) + '</td>' +
        '<td>' + escapeHtml(ligne.conducteur_sortie) + '</td>' +
        '<td class="text-nowrap">' + escapeHtml(ligne.date_entree_label) + '</td>' +
        '<td class="text-nowrap">' + (ligne.en_cours
          ? '<span class="badge badge-warning">En cours</span>'
          : escapeHtml(ligne.date_sortie_label || '—')) + '</td>' +
        '<td>' + escapeHtml(ligne.duree_label) + '</td>';
      tbody.appendChild(tr);
    });
  }

  function detruireGraphiques() {
    Object.keys(charts).forEach(function (cle) {
      if (charts[cle]) {
        charts[cle].destroy();
        charts[cle] = null;
      }
    });
  }

  function rendreGraphiques(data) {
    if (typeof Chart === 'undefined') return;
    detruireGraphiques();

    var flux = data.flux;
    var canvasFlux = $('occ-vehicule-flux-chart');
    if (canvasFlux && flux) {
      charts.flux = new Chart(canvasFlux, {
        type: 'line',
        data: {
          labels: flux.labels,
          datasets: [
            {
              label: 'Entrées',
              data: flux.entrees,
              borderColor: COULEURS.blue,
              backgroundColor: 'rgba(77, 124, 254, 0.12)',
              borderWidth: 2.5,
              fill: true,
              tension: 0.4,
              pointRadius: 3,
              pointBackgroundColor: COULEURS.blue,
            },
            {
              label: 'Sorties',
              data: flux.sorties,
              borderColor: COULEURS.red,
              backgroundColor: 'rgba(220, 38, 38, 0.15)',
              borderWidth: 2.5,
              fill: true,
              tension: 0.4,
              pointRadius: 3,
              pointBackgroundColor: COULEURS.red,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: { legend: { display: false } },
          scales: {
            x: {
              ticks: { color: COULEURS.muted, maxTicksLimit: 10, font: { size: 11 } },
              grid: { color: COULEURS.grid },
              border: { display: false },
            },
            y: {
              ticks: { color: COULEURS.muted, stepSize: 1, font: { size: 11 } },
              grid: { color: COULEURS.grid },
              border: { display: false },
              beginAtZero: true,
            },
          },
        },
      });
    }

    var presence = data.presence;
    var canvasPresence = $('occ-vehicule-presence-chart');
    if (canvasPresence && presence) {
      charts.presence = new Chart(canvasPresence, {
        type: 'bar',
        data: {
          labels: presence.map(function (p) { return p.label; }),
          datasets: [{
            label: 'Minutes sur site',
            data: presence.map(function (p) { return p.minutes; }),
            backgroundColor: 'rgba(45, 212, 191, 0.55)',
            borderColor: COULEURS.teal,
            borderWidth: 1,
            borderRadius: 4,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: {
              ticks: { color: COULEURS.muted, maxTicksLimit: 10, font: { size: 11 } },
              grid: { display: false },
              border: { display: false },
            },
            y: {
              ticks: { color: COULEURS.muted, font: { size: 11 } },
              grid: { color: COULEURS.grid },
              border: { display: false },
              beginAtZero: true,
            },
          },
        },
      });
    }
  }

  function changerPeriode(periode) {
    periodeActuelle = periode;
    document.querySelectorAll('.occ-vehicule-periode').forEach(function (btn) {
      var actif = btn.dataset.periode === periode;
      btn.classList.toggle('active', actif);
      btn.setAttribute('aria-selected', actif ? 'true' : 'false');
    });
    if (vehiculeActif) {
      chargerDashboardVehicule();
    }
  }

  function basculerListeVehicules() {
    if (!listePanel) return;
    var ouvert = listePanel.hidden;
    listePanel.hidden = !ouvert;
    var trigger = $('occ-recherche-vehicule-trigger');
    if (trigger) trigger.setAttribute('aria-expanded', ouvert ? 'true' : 'false');
    if (ouvert) {
      var input = $('occ-recherche-filtre-vehicules');
      if (input) {
        input.value = '';
        input.focus();
      }
      rendreListeVehicules(vehicules);
    }
  }

  function initialiser() {
    scene = $('occupation-recherche-scene');
    dashboardMain = $('fin-dashboard-main');
    etapePicker = $('occ-recherche-etape-picker');
    etapeDashboard = $('occ-recherche-etape-dashboard');
    listePanel = $('occ-recherche-liste-vehicules');
    listeUl = $('occ-recherche-liste-vehicules-ul');

    if (!scene) return;

    var ouvrir = $('ucb-recherche-ouvrir');
    if (ouvrir) {
      ouvrir.addEventListener('click', ouvrirScene);
    }

    ['occ-recherche-fermer', 'occ-recherche-fermer-dashboard'].forEach(function (id) {
      var btn = $(id);
      if (btn) btn.addEventListener('click', fermerScene);
    });

    var retour = $('occ-recherche-retour-vehicules');
    if (retour) {
      retour.addEventListener('click', function () {
        afficherEtapePicker();
        detruireGraphiques();
      });
    }

    var trigger = $('occ-recherche-vehicule-trigger');
    if (trigger) {
      trigger.addEventListener('click', basculerListeVehicules);
    }

    var filtreVehicules = $('occ-recherche-filtre-vehicules');
    if (filtreVehicules) {
      filtreVehicules.addEventListener('input', function () {
        rendreListeVehicules(vehicules);
      });
    }

    document.querySelectorAll('.occ-vehicule-periode').forEach(function (btn) {
      btn.addEventListener('click', function () {
        changerPeriode(btn.dataset.periode);
      });
    });

    var filtreHistorique = $('occ-historique-filtre');
    if (filtreHistorique) {
      filtreHistorique.addEventListener('input', function () {
        clearTimeout(filtreHistoriqueTimer);
        filtreHistoriqueTimer = setTimeout(function () {
          if (vehiculeActif) chargerDashboardVehicule();
        }, 350);
      });
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && scene && !scene.hidden) {
        fermerScene();
      }
    });
  }

  document.addEventListener('DOMContentLoaded', initialiser);
})();
