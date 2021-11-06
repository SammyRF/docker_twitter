from django.test import TestCase
from utils.test_helpers import TestHelpers
from utils.gatekeeper.models import GateKeeper


class GateKeeperTests(TestCase):

    def setUp(self):
        TestHelpers.clear_cache()

    def test_gatekeeper(self):
        gk = GateKeeper.get('gk_name')
        self.assertEqual(gk, {'percent': 0, 'description': ''})
        self.assertEqual(GateKeeper.is_switch_on('gk_name'), False)
        self.assertEqual(GateKeeper.uid_in_gk(1, 'gk_name'), False)

        GateKeeper.set('gk_name', 'percent', 20)
        self.assertEqual(GateKeeper.is_switch_on('gk_name'), False)
        self.assertEqual(GateKeeper.uid_in_gk(1, 'gk_name'), True)

        GateKeeper.set('gk_name', 'percent', 100)
        self.assertEqual(GateKeeper.is_switch_on('gk_name'), True)
        self.assertEqual(GateKeeper.uid_in_gk(1, 'gk_name'), True)