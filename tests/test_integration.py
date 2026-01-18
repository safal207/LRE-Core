import unittest
import sys
import os

# To test the integration with submodules without installing them as packages,
# we add their paths to sys.path.
# This mimics the environment where these packages would be installed.

# Path to LPI's python package (which provides 'lri' package)
lpi_pkg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/lpi/packages/python-lri'))

# Path to LRI reference implementation (which provides 'dmp' module)
lri_ref_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/lri/lri-reference'))

if os.path.exists(lpi_pkg_path) and lpi_pkg_path not in sys.path:
    sys.path.append(lpi_pkg_path)

if os.path.exists(lri_ref_path) and lri_ref_path not in sys.path:
    sys.path.append(lri_ref_path)

# Try imports
try:
    from lri import LRI
except ImportError:
    LRI = None

try:
    import dmp
except ImportError:
    dmp = None

from src.lre_dp import LRE_DP
from src.execution.registry import ActionRegistry

class TestLRECoreIntegration(unittest.TestCase):
    def setUp(self):
        # Check if submodules are present
        base_dir = os.path.dirname(os.path.abspath(__file__))
        submodules = ['../src/lpi', '../src/lri', '../src/dml', '../src/ltp']

        missing = []
        for sm in submodules:
            path = os.path.join(base_dir, sm)
            if not os.path.exists(path):
                missing.append(sm)
            # For LTP, since we can't fully initialize it due to broken URL, we might check differently
            # but structurally it should exist.

        if missing:
             # We only warn/skip for LTP if it's the only one missing, as it is known broken
             if missing == ['../src/ltp']:
                 print("Warning: LTP submodule missing (expected due to 404)")
             else:
                 self.skipTest(f"Submodules missing: {missing}. Run 'git submodule update --init --recursive'")

        if LRI is None:
             self.skipTest("LPI/LRI package could not be imported. Check submodule state.")

        # Instantiate dependencies
        self.lpi = LRI()

        # Mock LRI Routing service
        self.lri_mock = "LRI_Routing_Service"

        # Mock Action Registry
        self.registry = ActionRegistry()

        # We initialize LRE_DP
        self.lre_dp = LRE_DP(lpi=self.lpi, lri=self.lri_mock, registry=self.registry)

        self.dmp = dmp

    def test_dmp_record_decision(self):
        """
        Test DMP record decision.
        """
        if self.dmp is None:
            self.skipTest("DMP module not found")

        action = {"type": "emergency_shutdown", "target": "node_1"}

        try:
            record = self.dmp.record_decision("agent_007", action, intention="test_integration")
            self.assertIsNotNone(record)
            self.assertEqual(record["action"], action)
            self.assertEqual(record["subject_id"], "agent_007")

        except ImportError as e:
            self.skipTest(f"DMP dependencies missing: {e}")
        except Exception as e:
            self.fail(f"DMP record_decision failed: {e}")

    def test_lre_dp_execution(self):
        """
        Test LRE-DP execute decision.
        """
        # Register a mock handler
        async def mock_handler(ctx):
            return {"status": "success", "executed": True}

        self.registry.register("test_action", mock_handler)

        action = {
            "action": "test_action",
            "agent_id": "test_agent",
            "payload": {}
        }

        # LRE_DP.execute_decision is async
        import asyncio
        res = asyncio.run(self.lre_dp.execute_decision(action))

        self.assertEqual(res["status"], "executed")
        self.assertTrue(res["result"]["executed"])

    def test_fetch_history_integration(self):
        """
        Test real fetch_history action integration.
        """
        import asyncio
        from src.core.events import Events

        # We need to make sure stdlib is loaded to have the action registered
        from src.execution.registry import set_default_registry
        set_default_registry(self.registry)
        import src.execution.stdlib

        # Load stdlib into our test registry
        # The stdlib uses the default registry, so we should use that or make sure it's wired.
        # For this test, let's just register the real fetch_history handler into our test registry.
        from src.execution.stdlib import fetch_history
        self.registry.register(Events.FETCH_HISTORY, fetch_history)

        action = {
            "action": Events.FETCH_HISTORY,
            "agent_id": "test_agent",
            "payload": {"limit": 5}
        }

        res = asyncio.run(self.lre_dp.execute_decision(action))

        self.assertEqual(res["status"], "executed")
        self.assertEqual(res["result"]["type"], Events.HISTORY_RESULT)
        self.assertIn("events", res["result"]["payload"])
        self.assertIn("count", res["result"]["payload"])

    def test_dependencies_present(self):
        """
        Verify LPI and LRI dependencies are correctly assigned.
        """
        self.assertIsNotNone(self.lre_dp.lpi)
        self.assertIsNotNone(self.lre_dp.lri)
        # Verify LPI is the LRI class instance (LPI Handler)
        self.assertEqual(self.lre_dp.lpi.__class__.__name__, "LRI")

if __name__ == '__main__':
    unittest.main()
