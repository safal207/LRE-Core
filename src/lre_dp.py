from typing import Optional, Any, Union, Dict
from src.execution.registry import ActionRegistry
import logging

logger = logging.getLogger(__name__)

class LRE_DP:
    """
    Liminal Runtime Environment - Decision Protocol
    Executes decisions based on inputs via LPI + LRI.
    """
    def __init__(self, lpi: Any, lri: Any, registry: Optional[ActionRegistry] = None):
        self.lpi = lpi
        self.lri = lri
        # Backward compatibility: use provided registry or create a new one
        self.registry = registry if registry is not None else ActionRegistry()
        self.state = {}

    async def execute_decision(self, decision_data: Union[dict, Any]) -> Dict[str, Any]:
        """
        Execute decision using registered action handlers.
        """
        # Extract decision context
        if hasattr(decision_data, "decision_input"):
            context = decision_data
            decision_dict = decision_data.decision_input
        elif isinstance(decision_data, dict):
            # For backward compatibility, wrap dict in context
            from src.decision.context import DecisionContext
            context = DecisionContext(decision_data)
            decision_dict = decision_data
        else:
            return {"status": "rejected", "error": "Invalid decision data type"}

        action_name = decision_dict.get("action")

        if not action_name:
            return {"status": "rejected", "reason": "Missing 'action' field"}

        # Lookup handler in registry
        handler = self.registry.get_handler(action_name)

        if not handler:
            logger.warning(f"Unknown action: {action_name}")
            return {
                "status": "rejected",
                "reason": f"Unknown action: {action_name}",
                "available_actions": self.registry.list_actions()
            }

        # Execute handler with error handling
        try:
            result = await handler(context)

            # Update state for backward compatibility
            self.update_state(decision_dict)

            return {
                "status": "executed",
                "result": result
            }
        except Exception as e:
            logger.error(f"Action '{action_name}' failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "action": action_name,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def update_state(self, new_state: dict):
        """
        Updates the internal state.
        """
        # print(f"[LRE-DP] Updating state with: {new_state}")
        self.state.update(new_state)
