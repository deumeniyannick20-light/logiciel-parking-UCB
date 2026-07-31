from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils import timezone

from parc.occupation_liste_groupee import (
    grouper_occupations_par_jour_et_vehicule,
    libelle_jour,
)


def _occ(pk, vehicule_id, vehicule_label, date_entree, date_sortie=None):
    return SimpleNamespace(
        pk=pk,
        vehicule_id=vehicule_id,
        vehicule=vehicule_label,
        date_entree=date_entree,
        date_sortie=date_sortie,
    )


class OccupationListeGroupeeTests(SimpleTestCase):
    def test_libelle_jour_francais(self):
        self.assertEqual(
            libelle_jour(datetime(2026, 7, 30).date()),
            "Jeudi 30 juillet 2026",
        )

    @patch("parc.occupation_liste_groupee.timezone.localtime")
    def test_regroupe_par_jour_et_vehicule(self, localtime):
        entree1 = timezone.make_aware(datetime(2026, 7, 30, 15, 58))
        sortie1 = timezone.make_aware(datetime(2026, 7, 30, 18, 26))
        entree2 = timezone.make_aware(datetime(2026, 7, 30, 20, 35))
        entree3 = timezone.make_aware(datetime(2026, 7, 29, 9, 0))

        occupations = [
            _occ(1, 10, "LT145", entree1, sortie1),
            _occ(2, 10, "LT145", entree2, None),
            _occ(3, 20, "AB123", entree3, None),
        ]
        localtime.side_effect = lambda dt: dt

        blocs = grouper_occupations_par_jour_et_vehicule(occupations)

        self.assertEqual(len(blocs), 2)
        self.assertEqual(blocs[0]["libelle"], "Jeudi 30 juillet 2026")
        self.assertEqual(len(blocs[0]["lignes"]), 1)
        self.assertEqual(blocs[0]["lignes"][0]["vehicule"], "LT145")
        self.assertEqual(len(blocs[0]["lignes"][0]["mouvements"]), 2)
        self.assertEqual(blocs[0]["lignes"][0]["mouvements"][0].pk, 1)
        self.assertEqual(blocs[0]["lignes"][0]["mouvements"][1].pk, 2)

        self.assertEqual(blocs[1]["libelle"], "Mercredi 29 juillet 2026")
        self.assertEqual(len(blocs[1]["lignes"]), 1)
        self.assertEqual(blocs[1]["lignes"][0]["vehicule"], "AB123")
