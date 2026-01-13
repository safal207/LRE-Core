import asyncio
import logging
import sys
import importlib
from pathlib import Path
from typing import Optional, Dict, Any

from src.event_bus import EventBus
from src.decision.pipeline import DecisionPipeline
from src.execution.registry import ActionRegistry, set_default_registry

logger = logging.getLogger(__name__)

class LRERuntime:
    """
    Core Runtime Orchestrator for LRE-Core.
    Binds LPI, LRI, DML, and LRE-DP together.
    """
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.event_bus = EventBus()
        self.registry = ActionRegistry()  # ← NEW
        self.lpi = None
        self.lri = None
        self.dml = None
        self.lre_dp = None
        self.pipeline = None
        self._running = False

    async def initialize(self):
        """
        Initialize the runtime, setup paths, and load submodules.
        """
        logger.info("Initializing LRERuntime...")

        # Dynamic sys.path setup
        src_path = Path(__file__).parent
        # Add possible submodule paths
        paths_to_add = [
            src_path / "lpi",
            src_path / "lpi/packages/python-lri", # As per memory
            src_path / "lri",
            src_path / "lri/lri-reference",
            src_path / "dml",
            src_path / "ltp",
        ]

        for p in paths_to_add:
            s_p = str(p)
            if s_p not in sys.path:
                sys.path.insert(0, s_p)
                logger.debug(f"Added {s_p} to sys.path")

        # NEW: Set default registry and load stdlib
        set_default_registry(self.registry)
        import src.execution.stdlib  # Importing triggers @action decorators
        logger.info(f"Loaded {len(self.registry.list_actions())} standard actions")

        # Import and instantiate protocol handlers
        await self._init_protocols()

        # Initialize Pipeline
        self.pipeline = DecisionPipeline(self.lpi, self.lri, self.lre_dp, self.event_bus)

        # Wire up Event Bus (Internal subscriptions if any)
        # For now, just logging or basic stuff could be added

        self._running = True
        logger.info("LRERuntime initialized successfully")

    async def _init_protocols(self):
        """
        Attempt to import and instantiate protocols.
        Handle missing submodules/imports gracefully.
        """
        # LPI
        try:
            # Trying to import LPI. Since file structure is complex,
            # we look for what's available.
            # If src/lpi is a package, we import it.
            import lpi # type: ignore
            self.lpi = lpi # Placeholder if lpi module has a class or is the interface
            # If LPI is a class inside a package, we might need specific import
            # For now, we assume we can instantiate something or use the module as handler
            logger.info("Loaded LPI protocol")
        except ImportError as e:
            logger.warning(f"Failed to import LPI: {e}. Using Mock.")
            self.lpi = self._create_mock("LPI")

        # LRI
        try:
            # As per memory: src/lpi/packages/python-lri has LRI class?
            # Or src/lri/lri-reference/dmp.py?
            # Let's try importing 'lri' assuming it's in python-lri
            from lri import LRI # type: ignore
            self.lri = LRI()
            logger.info("Loaded LRI protocol")
        except ImportError as e:
            logger.warning(f"Failed to import LRI: {e}. Using Mock.")
            self.lri = self._create_mock("LRI")

        # DML
        try:
            import dml # type: ignore
            self.dml = dml
            logger.info("Loaded DML protocol")
        except ImportError as e:
            logger.warning(f"Failed to import DML: {e}. Using Mock.")
            self.dml = self._create_mock("DML")

        # LRE-DP
        try:
            from src.lre_dp import LRE_DP
            # LRE-DP needs LPI, LRI and Registry
            self.lre_dp = LRE_DP(self.lpi, self.lri, self.registry)
            logger.info("Loaded LRE-DP protocol")
        except ImportError as e:
            logger.warning(f"Failed to import LRE_DP: {e}. Using Mock.")
            self.lre_dp = self._create_mock("LRE_DP")
        except Exception as e:
            logger.warning(f"Failed to instantiate LRE_DP: {e}. Using Mock.")
            self.lre_dp = self._create_mock("LRE_DP")

    def _create_mock(self, name: str):
        class MockProtocol:
            def __getattr__(self, item):
                # Return a callable that does nothing but log
                def method(*args, **kwargs):
                    logger.debug(f"Mock {name}.{item} called with {args} {kwargs}")
                    # Return basic values for critical path methods
                    if item == "query_presence":
                        return True # Always online
                    if item == "calculate_route":
                        return "direct" # Default route
                    if item == "execute_decision":
                        return {"status": "executed (mock)"}
                    return None
                return method
        return MockProtocol()

    async def process_decision(self, dml_input: dict) -> dict:
        """
        Process a single decision through the pipeline.
        """
        if not self.pipeline:
            return {"status": "failed", "error": "Runtime not initialized"}

        return await self.pipeline.execute(dml_input)

    async def loop(self):
        """
        Main event loop placeholder.
        """
        while self._running:
            await asyncio.sleep(1)

    async def shutdown(self):
        """
        Graceful teardown.
        """
        logger.info("Shutting down LRERuntime...")
        self._running = False
        # Cleanup tasks if any
        logger.info("Shutdown complete")
