from .lpi import LPI

class LRE_DP:
    """
    Liminal Runtime Environment - Decision Protocol
    """
    def __init__(self, lpi: LPI):
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
