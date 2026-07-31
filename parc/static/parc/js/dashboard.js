(function () {
  'use strict';

  var donnees = {};
  var charts = {};
  var chartExpand = null;
  var carteActive = null;

  var COULEURS = {
    blue: '#4d7cfe',
    gold: '#f0b429',
    red: '#dc2626',
    teal: '#2dd4bf',
    purple: '#a78bfa',
    danger: '#dc2626',
    grid: 'rgba(255,255,255,0.04)',
    muted: '#7c849a',
  };

  function lireDonnees() {
    var bloc = document.getElementById('dashboard-data');
    if (!bloc || !bloc.textContent) return {};
    try {
      var donnees = JSON.parse(bloc.textContent);
      if (typeof donnees === 'string') {
        donnees = JSON.parse(donnees);
      }
      return donnees;
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

  /** Facteur de lenteur demandé (+15 % de durée). */
  var FACTEUR_LENTEUR_CARDIOGRAMME = 1.15;
  var DUREE_COMPTEUR_MS = 1400;

  function formaterCompteur(valeur, decimals) {
    if (decimals > 0) {
      return valeur.toFixed(decimals);
    }
    return String(Math.round(valeur));
  }

  function easingCompteur(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function animaterCompteursDashboard() {
    var reduireMouvement = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var compteurs = document.querySelectorAll('[data-ucb-count]');
    var barres = document.querySelectorAll('[data-ucb-barre]');

    if (reduireMouvement) {
      compteurs.forEach(function (el) {
        var cible = parseFloat(el.getAttribute('data-ucb-count'));
        var decimals = parseInt(el.getAttribute('data-ucb-decimals') || '0', 10);
        var prefix = el.getAttribute('data-ucb-prefix') || '';
        var suffix = el.getAttribute('data-ucb-suffix') || '';
        if (!isNaN(cible)) {
          el.textContent = prefix + formaterCompteur(cible, decimals) + suffix;
        }
      });
      barres.forEach(function (barre) {
        var largeur = parseFloat(barre.getAttribute('data-ucb-barre'));
        if (!isNaN(largeur)) {
          barre.style.width = largeur + '%';
        }
      });
      return;
    }

    var debutGlobal = performance.now();

    compteurs.forEach(function (el, index) {
      var cible = parseFloat(el.getAttribute('data-ucb-count'));
      if (isNaN(cible)) {
        return;
      }
      var decimals = parseInt(el.getAttribute('data-ucb-decimals') || '0', 10);
      var prefix = el.getAttribute('data-ucb-prefix') || '';
      var suffix = el.getAttribute('data-ucb-suffix') || '';
      var delai = parseInt(el.getAttribute('data-ucb-delay') || String(index * 55), 10);

      function tick(now) {
        var elapsed = now - debutGlobal - delai;
        if (elapsed < 0) {
          requestAnimationFrame(tick);
          return;
        }
        var progress = Math.min(1, elapsed / DUREE_COMPTEUR_MS);
        var valeur = cible * easingCompteur(progress);
        el.textContent = prefix + formaterCompteur(valeur, decimals) + suffix;
        if (progress < 1) {
          requestAnimationFrame(tick);
        } else {
          el.textContent = prefix + formaterCompteur(cible, decimals) + suffix;
        }
      }

      el.textContent = prefix + formaterCompteur(0, decimals) + suffix;
      requestAnimationFrame(tick);
    });

    barres.forEach(function (barre, index) {
      var largeurCible = parseFloat(barre.getAttribute('data-ucb-barre'));
      if (isNaN(largeurCible)) {
        return;
      }
      var delai = index * 55;

      function tickBarre(now) {
        var elapsed = now - debutGlobal - delai;
        if (elapsed < 0) {
          requestAnimationFrame(tickBarre);
          return;
        }
        var progress = Math.min(1, elapsed / DUREE_COMPTEUR_MS);
        barre.style.width = (largeurCible * easingCompteur(progress)) + '%';
        if (progress < 1) {
          requestAnimationFrame(tickBarre);
        } else {
          barre.style.width = largeurCible + '%';
        }
      }

      barre.style.width = '0%';
      requestAnimationFrame(tickBarre);
    });
  }

  /**
   * Révélation gauche → droite à vitesse linéaire constante (style cardiogramme).
   * Le tracé complet est dessiné puis masqué progressivement pour un rendu fluide.
   */
  var cardiogrammeClipPlugin = {
    id: 'ucbCardiogrammeClip',
    defaults: {
      active: true,
      duration: 1000,
    },
    beforeInit: function (chart, _args, options) {
      chart.$ucbClip = {
        progress: options.active ? 0 : 1,
        started: false,
        rafId: null,
        startTime: null,
        clipping: false,
      };
    },
    beforeDatasetsDraw: function (chart) {
      var clip = chart.$ucbClip;
      if (!clip || clip.progress >= 1) {
        return;
      }
      var area = chart.chartArea;
      if (!area || area.width <= 0) {
        return;
      }
      var ctx = chart.ctx;
      ctx.save();
      ctx.beginPath();
      ctx.rect(
        area.left,
        area.top,
        area.width * clip.progress,
        area.height
      );
      ctx.clip();
      clip.clipping = true;
    },
    afterDatasetsDraw: function (chart) {
      var clip = chart.$ucbClip;
      if (clip && clip.clipping) {
        chart.ctx.restore();
        clip.clipping = false;
      }
    },
    afterLayout: function (chart, _args, options) {
      var clip = chart.$ucbClip;
      if (!options.active || !clip || clip.started || clip.progress >= 1) {
        return;
      }
      if (!chart.chartArea || chart.chartArea.width <= 0) {
        return;
      }
      clip.started = true;
      demarrerAnimationCardiogramme(chart, options.duration);
    },
    destroy: function (chart) {
      var clip = chart.$ucbClip;
      if (clip && clip.rafId) {
        cancelAnimationFrame(clip.rafId);
      }
    },
  };

  function demarrerAnimationCardiogramme(chart, dureeMs) {
    var clip = chart.$ucbClip;
    if (!clip) {
      return;
    }
    if (clip.rafId) {
      cancelAnimationFrame(clip.rafId);
    }
    clip.startTime = performance.now();
    clip.progress = 0;

    function tick(now) {
      if (!chart.$ucbClip) {
        return;
      }
      var elapsed = now - clip.startTime;
      clip.progress = Math.min(1, elapsed / dureeMs);
      chart.draw();
      if (clip.progress < 1) {
        clip.rafId = requestAnimationFrame(tick);
      } else {
        clip.progress = 1;
        clip.rafId = null;
        chart.draw();
      }
    }

    clip.rafId = requestAnimationFrame(tick);
  }

  function dureeCardiogramme(dureeBaseMs) {
    return Math.round(dureeBaseMs * FACTEUR_LENTEUR_CARDIOGRAMME);
  }

  function optionsAnimationCardiogramme(dureeBaseMs) {
    return {
      animation: false,
      transitions: {
        active: { animation: { duration: 0 } },
        resize: { animation: { duration: 0 } },
        show: { animations: { colors: false, x: false, y: false } },
        hide: { animations: { colors: false, x: false, y: false } },
      },
      plugins: {
        ucbCardiogrammeClip: {
          active: true,
          duration: dureeCardiogramme(dureeBaseMs),
        },
      },
    };
  }

  function optionsGraphiqueCardiogramme(specifique, dureeBaseMs) {
    var cardio = optionsAnimationCardiogramme(dureeBaseMs);
    var plugins = Object.assign({}, cardio.plugins, (specifique.plugins || {}));
    return Object.assign({}, cardio, specifique, { plugins: plugins });
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
      options: optionsGraphiqueCardiogramme({
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: { x: { display: false }, y: { display: false } },
      }, 900),
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

    function rayonPoint(context) {
      var idx = context.dataIndex;
      var points = flux.points;
      if (!points || !points[idx]) {
        return 0;
      }
      var valeur = context.datasetIndex === 0
        ? points[idx].entrees
        : points[idx].sorties;
      return valeur > 0 ? 4 : 0;
    }

    function rayonSurvol(context) {
      return rayonPoint(context) > 0 ? 7 : 0;
    }

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
            pointRadius: rayonPoint,
            pointHoverRadius: rayonSurvol,
            pointBackgroundColor: COULEURS.blue,
            pointBorderColor: COULEURS.blue,
          },
          {
            label: 'Sorties',
            data: flux.sorties,
            borderColor: COULEURS.red,
            backgroundColor: 'rgba(220, 38, 38, 0.18)',
            pointBackgroundColor: COULEURS.red,
            pointBorderColor: COULEURS.red,
            pointHoverBackgroundColor: '#ef4444',
            pointHoverBorderColor: COULEURS.red,
            borderWidth: 2.5,
            fill: true,
            tension: 0.4,
            pointRadius: rayonPoint,
            pointHoverRadius: rayonSurvol,
          },
        ],
      },
      options: optionsGraphiqueCardiogramme({
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        onClick: function (_evt, elements) {
          if (!elements.length) {
            return;
          }
          var element = elements[0];
          afficherDetailFlux(element.index, element.datasetIndex);
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#161b28',
            titleColor: '#eef1f8',
            bodyColor: COULEURS.muted,
            borderColor: 'rgba(255,255,255,0.08)',
            borderWidth: 1,
            padding: 12,
            callbacks: {
              title: function (items) {
                if (!items.length || !flux.points) {
                  return '';
                }
                return flux.points[items[0].dataIndex].label;
              },
              afterBody: function (items) {
                if (!items.length || !flux.points) {
                  return '';
                }
                var point = flux.points[items[0].dataIndex];
                if (!point.evenements.length) {
                  return 'Aucun mouvement';
                }
                return point.evenements.slice(0, 4).map(function (ev) {
                  var heure = ev.label || '';
                  return (ev.type === 'entree' ? '↑' : '↓') + ' ' + heure +
                    ' — ' + ev.immatriculation + ' — ' + ev.marque + ' — ' + ev.conducteur;
                });
              },
            },
          },
        },
        scales: {
          x: {
            ticks: { color: COULEURS.muted, maxTicksLimit: 8, font: { size: 11 } },
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
      }, 1600),
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
      options: optionsGraphiqueCardiogramme({
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { display: false },
          y: { display: false, beginAtZero: true },
        },
      }, 1200),
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
    creerSparkline('spark-sorties', serieDepuisFlux('sorties'), COULEURS.red);

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

  function formaterEvenementMouvement(ev) {
    var cls = ev.type === 'entree' ? 'dash-event-entree' : 'dash-event-sortie';
    var lib = ev.type === 'entree' ? 'Entrée' : 'Sortie';
    var immat = ev.immatriculation || '';
    var marque = ev.marque || '';
    var conducteur = ev.conducteur || '—';
    var horodatage = ev.label || (ev.instant
      ? new Date(ev.instant).toLocaleString('fr-FR', { hour: '2-digit', minute: '2-digit' })
      : '');
    return '<div class="dash-event-item fin-flux-detail__item">' +
      '<div class="fin-flux-detail__ligne">' +
      '<strong class="' + cls + '">' + lib + '</strong>' +
      (horodatage ? ' <span class="fin-flux-detail__heure">' + horodatage + '</span>' : '') +
      '</div>' +
      '<div class="fin-flux-detail__meta">' +
      '<span><strong>Immat.</strong> ' + immat + '</span>' +
      '<span><strong>Marque</strong> ' + marque + (ev.modele ? ' ' + ev.modele : '') + '</span>' +
      '<span><strong>Conducteur</strong> ' + conducteur + '</span>' +
      '</div></div>';
  }

  function afficherDetailFlux(index, datasetIndex) {
    var conteneur = document.getElementById('dash-flux-detail');
    var flux = donnees.flux_24h;
    if (!conteneur || !flux || !flux.points || !flux.points[index]) {
      return;
    }
    var point = flux.points[index];
    var typeAttendu = datasetIndex === 0 ? 'entree' : 'sortie';
    var evenements = (point.evenements || []).filter(function (ev) {
      return ev.type === typeAttendu;
    });
    if (!evenements.length) {
      conteneur.innerHTML = '<p class="fin-flux-detail__vide mb-0">Aucun mouvement à ' + point.label + '.</p>';
      return;
    }
    conteneur.innerHTML = '<p class="fin-flux-detail__titre">Mouvements autour de <strong>' + point.label + '</strong></p>' +
      evenements.map(formaterEvenementMouvement).join('');
  }

  function afficherEvenements(evenements) {
    var conteneur = document.getElementById('dash-expand-events');
    if (!conteneur) return;
    if (!evenements || !evenements.length) {
      conteneur.innerHTML = '<p class="text-muted mb-0">Aucun mouvement sur ce point.</p>';
      return;
    }
    conteneur.innerHTML = evenements.map(formaterEvenementMouvement).join('');
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
      options: optionsGraphiqueCardiogramme({
        responsive: true,
        maintainAspectRatio: false,
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
      }, 1400),
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
    document.body.classList.add('dash-expand-ouvert');
    overlay.scrollTop = 0;
    chargerMensuel();
    window.setTimeout(function () {
      if (chartExpand) chartExpand.resize();
    }, 80);
  }

  function fermerPanneau() {
    var overlay = document.getElementById('dash-expand-overlay');
    if (overlay) overlay.classList.remove('visible');
    document.body.classList.remove('dash-expand-ouvert');
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
    document.addEventListener('keydown', function (e) {
      var overlay = document.getElementById('dash-expand-overlay');
      if (e.key === 'Escape' && overlay && overlay.classList.contains('visible')) {
        fermerPanneau();
      }
    });
  }

  function demarrer() {
    donnees = lireDonnees();
    animaterCompteursDashboard();
    lierInteractions();
    if (typeof Chart === 'undefined') {
      console.error('Chart.js non chargé');
      return;
    }
    if (!Chart.registry.plugins.get('ucbCardiogrammeClip')) {
      Chart.register(cardiogrammeClipPlugin);
    }
    initialiserGraphiques();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', demarrer);
  } else {
    demarrer();
  }
})();
