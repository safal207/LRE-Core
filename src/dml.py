from .lre_dp import LRE_DP
from .lpi import LPI

class DML:
    """
    Decision Markup Language Protocol
    """
    def __init__(self, lre_dp: LRE_DP, lpi: LPI):
        self.lre_dp = lre_dp
        self.lpi = lpi

    def propose_action(self, action_data: dict):
        """
        Proposes an action to be executed by LRE-DP.
        """
        print(f"[DML] Proposing action: {action_data}")
        # Interaction: DML.propose_action() -> LRE-DP.execute_decision()
        self.lre_dp.execute_decision(action_data)
