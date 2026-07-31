from datetime import datetime, timedelta

from django.test import SimpleTestCase
from django.utils import timezone

from parc.vehicule_dashboard_stats import (
    PERIODES_VALIDES,
    periode_depuis_preset,
    _formater_duree,
    _filtrer_historique_mot_cle,
)


class VehiculeDashboardStatsTests(SimpleTestCase):
    def test_periodes_valides(self):
        self.assertIn("jour", PERIODES_VALIDES)
        self.assertIn("annee", PERIODES_VALIDES)

    def test_periode_jour_commence_a_minuit(self):
        debut, fin = periode_depuis_preset("jour")
        self.assertEqual(debut.hour, 0)
        self.assertEqual(debut.minute, 0)
        self.assertLess(debut, fin)

    def test_formater_duree(self):
        self.assertEqual(_formater_duree(timedelta(hours=2, minutes=15)), "2 h 15 min")
        self.assertEqual(_formater_duree(timedelta(minutes=45)), "45 min")

    def test_filtre_historique_mot_cle(self):
        lignes = [
            {"recherche_texte": "parking simple dupont entree"},
            {"recherche_texte": "parking cadre martin sortie"},
        ]
        resultat = _filtrer_historique_mot_cle(lignes, "dupont")
        self.assertEqual(len(resultat), 1)
