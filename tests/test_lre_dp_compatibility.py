import unittest
from src.lre_dp import LRE_DP
from src.execution.registry import ActionRegistry

class TestLREDPCompatibility(unittest.TestCase):
    def test_init_without_registry(self):
        """Verify that LRE_DP can be initialized without a registry (backward compatibility)."""
        lpi = object()
        lri = object()

        # This should not raise TypeError
        dp = LRE_DP(lpi=lpi, lri=lri)

        self.assertIsNotNone(dp.registry)
        self.assertIsInstance(dp.registry, ActionRegistry)
        self.assertEqual(dp.lpi, lpi)
        self.assertEqual(dp.lri, lri)

if __name__ == '__main__':
    unittest.main()
