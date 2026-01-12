import unittest
from src.dml import DML
from src.lre_dp import LRE_DP
from src.lpi import LPI
from src.lri import LRI

class TestLRECoreIntegration(unittest.TestCase):
    def setUp(self):
        # Initialize dependencies
        self.lpi = LPI()
        self.lre_dp = LRE_DP(self.lpi)
        self.dml = DML(self.lre_dp, self.lpi)
        self.lri = LRI(self.dml)

    def test_dml_propose_action_triggers_lre_dp_execute(self):
        """
        Test DML.propose_action() -> LRE-DP.execute_decision()
        """
        action = {"type": "emergency_shutdown", "target": "node_1"}

        # We can use unittest.mock to verify calls, but for now we rely on the implementation logic
        # and checking state update if possible, or just successful execution.

        # Mocking to verify call
        from unittest.mock import MagicMock
        self.lre_dp.execute_decision = MagicMock()

        self.dml.propose_action(action)

        self.lre_dp.execute_decision.assert_called_once_with(action)

    def test_lpi_query_presence(self):
        """
        Test LPI.query_presence()
        """
        result = self.lpi.query_presence("agent_007")
        self.assertTrue(result)

    def test_lre_dp_update_state(self):
        """
        Test LRE-DP.update_state()
        """
        new_state = {"status": "active"}
        self.lre_dp.update_state(new_state)
        self.assertEqual(self.lre_dp.state["status"], "active")

    def test_lri_update_route(self):
        """
        Test LRI.update_route()
        """
        route = {"path": "/home", "metric": 10}
        # Just ensure it runs without error for now as it returns void
        self.lri.update_route(route)

if __name__ == '__main__':
    unittest.main()
