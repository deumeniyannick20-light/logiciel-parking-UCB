(function () {
  'use strict';

  var donnees = {};
  var charts = {};
  var chartExpand = null;
  var carteActive = null;

  var COULEURS = {
    blue: '#4d7cfe',
    gold: '#f0b429',
    teal: '#2dd4bf',
    purple: '#a78bfa',
    danger: '#ff5c75',
    grid: 'rgba(255,255,255,0.04)',
    muted: '#7c849a',
  };

  function lireDonnees() {
    var bloc = document.getElementById('dashboard-data');
    if (!bloc || !bloc.textContent) return {};
    try {
      return JSON.parse(bloc.textContent);
    } catch (e) {
      console.error('Dashboard : JSON invalide', e);
      return {};
    }
  }

  function serieDepuisFlux(cle) {
    var flux = donnees.flux_24h;
    if (!flux || !flux.labels) return [];
    return flux.labels.map(function (label, i) {
      return { label: label, valeur: flux[cle][i] || 0 };
    });
  }

  function creerSparkline(canvasId, serie, couleur) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === 'undefined' || !serie || !serie.length) return;
    if (charts[canvasId]) charts[canvasId].destroy();
    charts[canvasId] = new Chart(canvas, {
      type: 'line',
      data: {
        labels: serie.map(function (p) { return p.label; }),
        datasets: [{
          data: serie.map(function (p) { return p.valeur; }),
          borderColor: couleur || COULEURS.blue,
          backgroundColor: 'transparent',
          borderWidth: 2,
          fill: false,
          tension: 0.45,
          pointRadius: 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: { x: { display: false }, y: { display: false } },
        animation: { duration: 1000 },
      },
    });
  }

  function creerDonut(canvasId, pct, alerte, grand) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === 'undefined') return;
    if (charts[canvasId]) charts[canvasId].destroy();
    var couleur = alerte ? COULEURS.danger : COULEURS.blue;
    var reste = Math.max(100 - pct, 0);
    charts[canvasId] = new Chart(canvas, {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [pct, reste],
          backgroundColor: [couleur, 'rgba(255,255,255,0.06)'],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: grand ? '78%' : '72%',
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        animation: { animateRotate: true, duration: 1200 },
      },
      plugins: grand ? [] : [{
        id: 'centreTexte',
        beforeDraw: function (chart) {
          var ctx = chart.ctx;
          ctx.save();
          ctx.font = 'bold 10px Inter, sans-serif';
          ctx.fillStyle = '#eef1f8';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(Math.round(pct) + '%', chart.width / 2, chart.height / 2);
          ctx.restore();
        },
      }],
    });
  }

  function creerGraphFlux() {
    var canvas = document.getElementById('dash-flux-chart');
    var flux = donnees.flux_24h;
    if (!canvas || !flux || typeof Chart === 'undefined') return;
    if (charts.flux) charts.flux.destroy();
    charts.flux = new Chart(canvas, {
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
            pointRadius: 0,
            pointHoverRadius: 5,
          },
          {
            label: 'Sorties',
            data: flux.sorties,
            borderColor: COULEURS.gold,
            backgroundColor: 'rgba(240, 180, 41, 0.08)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 5,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 1400, easing: 'easeOutQuart' },
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#161b28',
            titleColor: '#eef1f8',
            bodyColor: COULEURS.muted,
            borderColor: 'rgba(255,255,255,0.08)',
            borderWidth: 1,
            padding: 12,
          },
        },
        scales: {
          x: {
            ticks: { color: COULEURS.muted, maxTicksLimit: 8, font: { size: 11 } },
            grid: { color: COULEURS.grid, drawBorder: false },
          },
          y: {
            ticks: { color: COULEURS.muted, stepSize: 1, font: { size: 11 } },
            grid: { color: COULEURS.grid, drawBorder: false },
            beginAtZero: true,
          },
        },
      },
    });
  }

  function creerGraphPresence() {
    var canvas = document.getElementById('dash-main-chart');
    var serie = donnees.vehicules && donnees.vehicules.sparkline_24h;
    if (!canvas || !serie) return;
    if (charts.main) charts.main.destroy();
    charts.main = new Chart(canvas, {
      type: 'line',
      data: {
        labels: serie.map(function (p) { return p.label; }),
        datasets: [{
          label: 'Présents',
          data: serie.map(function (p) { return p.valeur; }),
          borderColor: COULEURS.blue,
          backgroundColor: 'rgba(77, 124, 254, 0.15)',
          borderWidth: 2,
          fill: true,
          tension: 0.38,
          pointRadius: 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { display: false },
          y: { display: false, beginAtZero: true },
        },
      },
    });
  }

  function initialiserGraphiques() {
    if (donnees.vehicules && donnees.vehicules.sparkline_24h) {
      creerSparkline('spark-vehicules', donnees.vehicules.sparkline_24h, COULEURS.blue);
      creerSparkline('spark-vehicules-detail', donnees.vehicules.sparkline_24h, COULEURS.blue);
    }
    if (donnees.occupation_globale && donnees.occupation_globale.sparkline_24h) {
      creerSparkline('spark-libres', donnees.occupation_globale.sparkline_24h, COULEURS.teal);
    }
    creerSparkline('spark-entrees', serieDepuisFlux('entrees'), COULEURS.gold);
    creerSparkline('spark-sorties', serieDepuisFlux('sorties'), COULEURS.purple);

    if (donnees.occupation_globale) {
      creerDonut(
        'dash-occupation-donut',
        donnees.occupation_globale.pct,
        donnees.occupation_globale.alerte,
        true
      );
    }

    (donnees.parkings_universels || []).forEach(function (p) {
      var couleur = p.alerte ? COULEURS.danger : COULEURS.teal;
      creerSparkline('spark-parking-' + p.id, p.sparkline_24h, couleur);
      creerDonut('donut-parking-' + p.id, p.pct_occupe, p.alerte, false);
    });

    creerGraphFlux();
    creerGraphPresence();
  }

  function moisCourant() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
  }

  function urlApi(carte) {
    return carte.dataset.type === 'vehicules'
      ? '/api/dashboard/vehicules/'
      : '/api/dashboard/parking/' + carte.dataset.id + '/';
  }

  function titreCarte(carte) {
    if (carte.dataset.type === 'vehicules') {
      return 'Présence véhiculée — historique mensuel';
    }
    var p = (donnees.parkings_universels || []).find(function (x) {
      return String(x.id) === carte.dataset.id;
    });
    return p ? 'Parking ' + p.nom + ' — historique mensuel' : 'Parking universel';
  }

  function afficherEvenements(evenements) {
    var conteneur = document.getElementById('dash-expand-events');
    if (!conteneur) return;
    if (!evenements || !evenements.length) {
      conteneur.innerHTML = '<p class="text-muted mb-0">Aucun mouvement sur ce point.</p>';
      return;
    }
    conteneur.innerHTML = evenements.map(function (ev) {
      var cls = ev.type === 'entree' ? 'dash-event-entree' : 'dash-event-sortie';
      var lib = ev.type === 'entree' ? 'Entrée' : 'Sortie';
      return '<div class="dash-event-item"><strong class="' + cls + '">' + lib + '</strong> — ' +
        ev.vehicule + ' — ' + ev.place +
        ' <span class="text-muted">(' + new Date(ev.instant).toLocaleString('fr-FR') + ')</span></div>';
    }).join('');
  }

  function dessinerGraphEtendu(serie, label) {
    var canvas = document.getElementById('dash-expand-chart');
    if (!canvas || !serie || typeof Chart === 'undefined') return;
    if (chartExpand) chartExpand.destroy();
    chartExpand = new Chart(canvas, {
      type: 'line',
      data: {
        labels: serie.map(function (p) { return p.label; }),
        datasets: [{
          label: label,
          data: serie.map(function (p) { return p.valeur; }),
          borderColor: COULEURS.blue,
          backgroundColor: 'rgba(77, 124, 254, 0.15)',
          borderWidth: 2.5,
          fill: true,
          tension: 0.35,
          pointRadius: 3,
          pointHoverRadius: 7,
          pointBackgroundColor: COULEURS.blue,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 1200 },
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { color: COULEURS.muted } },
          tooltip: {
            backgroundColor: '#161b28',
            callbacks: {
              afterBody: function (items) {
                var point = serie[items[0].dataIndex];
                if (!point.evenements || !point.evenements.length) return 'Aucun mouvement';
                return point.evenements.slice(0, 4).map(function (ev) {
                  return (ev.type === 'entree' ? '↑ Entrée' : '↓ Sortie') + ' : ' + ev.vehicule;
                });
              },
            },
          },
        },
        scales: {
          x: { ticks: { color: COULEURS.muted }, grid: { color: COULEURS.grid } },
          y: { ticks: { color: COULEURS.muted }, grid: { color: COULEURS.grid }, beginAtZero: true },
        },
        onClick: function (evt, elements) {
          if (!elements.length) return;
          afficherEvenements(serie[elements[0].index].evenements || []);
        },
      },
    });
  }

  function chargerMensuel() {
    if (!carteActive) return;
    var sel = document.getElementById('dash-month-select');
    var mois = sel ? sel.value : moisCourant();
    fetch(urlApi(carteActive) + '?mois=' + encodeURIComponent(mois), {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    })
      .then(function (r) { return r.json(); })
      .then(function (payload) {
        var serie = payload.mensuel ? payload.mensuel.serie : payload.sparkline_24h;
        var lib = payload.mensuel ? 'Pic journalier — ' + payload.mensuel.libelle_mois : '24 dernières heures';
        dessinerGraphEtendu(serie, lib);
        afficherEvenements([]);
      })
      .catch(function (e) { console.error('Dashboard API', e); });
  }

  function ouvrirPanneau(carte) {
    carteActive = carte;
    var overlay = document.getElementById('dash-expand-overlay');
    var titre = document.getElementById('dash-expand-title');
    var sel = document.getElementById('dash-month-select');
    if (!overlay || !titre) return;
    titre.textContent = titreCarte(carte);
    if (sel) sel.value = moisCourant();
    overlay.classList.add('visible');
    document.body.style.overflow = 'hidden';
    chargerMensuel();
  }

  function fermerPanneau() {
    var overlay = document.getElementById('dash-expand-overlay');
    if (overlay) overlay.classList.remove('visible');
    document.body.style.overflow = '';
    carteActive = null;
  }

  function lierInteractions() {
    document.querySelectorAll('[data-type="vehicules"], [data-type="parking"]').forEach(function (carte) {
      if (!carte.classList.contains('fin-parking-card') &&
          !carte.classList.contains('fin-metric--clickable')) return;
      carte.addEventListener('click', function () { ouvrirPanneau(carte); });
      carte.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          ouvrirPanneau(carte);
        }
      });
    });
    var fermer = document.getElementById('dash-expand-close');
    var overlay = document.getElementById('dash-expand-overlay');
    var sel = document.getElementById('dash-month-select');
    if (fermer) fermer.addEventListener('click', fermerPanneau);
    if (overlay) {
      overlay.addEventListener('click', function (e) {
        if (e.target === overlay) fermerPanneau();
      });
    }
    if (sel) sel.addEventListener('change', chargerMensuel);
  }

  function demarrer() {
    donnees = lireDonnees();
    lierInteractions();
    if (typeof Chart === 'undefined') {
      console.error('Chart.js non chargé');
      return;
    }
    initialiserGraphiques();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', demarrer);
  } else {
    demarrer();
  }
})();
