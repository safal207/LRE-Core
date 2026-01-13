from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class DecisionIntent:
    """Structured representation of a decision."""
    action: str
    agent_id: str
    payload: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict) -> 'DecisionIntent':
        """Parse from raw dict."""
        return cls(
            action=data.get("action", ""),
            agent_id=data.get("agent_id", ""),
            payload=data.get("payload", {})
        )

class DecisionParser:
    """Validates and parses decision inputs."""

    def parse(self, raw_dict: dict) -> DecisionIntent:
        """Parse and validate decision input."""
        required_fields = ["action", "agent_id", "payload"]

        for field in required_fields:
            if field not in raw_dict:
                raise ValueError(f"Missing required field: {field}")

        if not isinstance(raw_dict["action"], str):
            raise ValueError("Field 'action' must be a string")

        if not isinstance(raw_dict["agent_id"], str):
            raise ValueError("Field 'agent_id' must be a string")

        return DecisionIntent.from_dict(raw_dict)

    def validate(self, raw_dict: dict) -> bool:
        """Quick validation without full parsing."""
        try:
            self.parse(raw_dict)
            return True
        except ValueError:
            return False
