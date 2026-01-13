import asyncio
import uuid
import time
import logging
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)

class DecisionContext:
    """
    Async context manager for decision execution.
    Tracks trace_id, timing, and errors.
    """
    def __init__(self, decision_input: Dict[str, Any]):
        self.decision_input = decision_input
        self.trace_id = str(uuid.uuid4())
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.metadata: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.status = "pending"
        self.result: Optional[Dict[str, Any]] = None

    async def __aenter__(self):
        self.start_time = time.perf_counter()
        logger.info(f"Starting decision execution trace_id={self.trace_id}")
        self.add_metadata("agent_id", self.decision_input.get("agent_id"))
        self.add_metadata("action", self.decision_input.get("action"))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        latency = self.get_latency_ms()

        if exc_type:
            logger.error(f"Decision execution failed trace_id={self.trace_id}: {exc_val}", exc_info=(exc_type, exc_val, exc_tb))
            self.mark_failed(exc_val)
            # We swallow the exception to prevent crashing the runtime, unless it's a critical system error?
            # The requirements say "Catches exceptions without crashing runtime".
            # So we swallow it here.
            return True

        logger.info(f"Finished decision execution trace_id={self.trace_id} latency={latency:.2f}ms status={self.status}")
        return False

    def get_trace_id(self) -> str:
        return self.trace_id

    def add_metadata(self, key: str, value: Any):
        self.metadata[key] = value

    def mark_failed(self, error: Exception):
        self.status = "failed"
        self.errors.append(str(error))

    def set_result(self, result: Dict[str, Any], status: str = "executed"):
        self.result = result
        self.status = status

    def get_latency_ms(self) -> float:
        if self.end_time == 0.0:
            # If called while running, return current duration
            return (time.perf_counter() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000

    def get_summary(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "trace_id": self.trace_id,
            "decision": self.decision_input,
            "result": self.result,
            "latency_ms": self.get_latency_ms(),
            "errors": self.errors,
            "metadata": self.metadata
        }
