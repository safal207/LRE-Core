import sys
import os

# Ensure we can import lri from submodules if not installed
# This is a runtime patch to ensure the module works when run from source
# In production, these packages should be installed.
current_dir = os.path.dirname(os.path.abspath(__file__))
lpi_pkg_path = os.path.join(current_dir, 'lpi/packages/python-lri')
if os.path.exists(lpi_pkg_path) and lpi_pkg_path not in sys.path:
    sys.path.append(lpi_pkg_path)

try:
    from lri import LRI as LPI_Protocol # Alias for semantic clarity
except ImportError:
    # Fallback or mock if submodule is missing/broken
    class LPI_Protocol:
        pass

class LRE_DP:
    """
    Liminal Runtime Environment - Decision Protocol
    """
    def __init__(self, lpi: LPI_Protocol):
        self.lpi = lpi
        self.state = {}

    def execute_decision(self, decision_data: dict):
        """
        Executes a decision.
        """
        print(f"[LRE-DP] Executing decision: {decision_data}")
        self.update_state(decision_data)

    def update_state(self, new_state: dict):
        """
        Updates the internal state.
        """
        print(f"[LRE-DP] Updating state with: {new_state}")
        self.state.update(new_state)
