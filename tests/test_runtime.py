import unittest
import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.runtime import LRERuntime
from src.decision.context import DecisionContext
from src.event_bus import EventBus

class TestLRERuntime(unittest.TestCase):
    def setUp(self):
        self.runtime = LRERuntime()
        # We start with empty mocks, but they will be overwritten by initialize()
        # So we need to control what initialize() does or replace them after.

    def test_runtime_initialization(self):
        async def run_test():
            # Mock _init_protocols to avoid loading real modules or failing imports during test
            with patch.object(self.runtime, '_init_protocols', new=AsyncMock()) as mock_init_proto, \
                 patch('src.runtime.PersistenceEngine') as MockPersistence:

                # Setup mock persistence
                mock_persistence_instance = MockPersistence.return_value
                mock_persistence_instance.initialize = AsyncMock()
                mock_persistence_instance._on_decision_event = AsyncMock()
                mock_persistence_instance.close = AsyncMock()

                await self.runtime.initialize()
                self.assertIsNotNone(self.runtime.pipeline)
                self.assertTrue(self.runtime._running)

        asyncio.run(run_test())

    def test_decision_pipeline_happy_path(self):
        async def run_test():
            # We want to use our mocks for protocols
            self.runtime.lpi = MagicMock()
            self.runtime.lri = MagicMock()
            self.runtime.lre_dp = MagicMock()
            self.runtime.dml = MagicMock()

            # Setup behavior
            self.runtime.lpi.query_presence.return_value = True
            self.runtime.lri.calculate_route.return_value = "direct"
            self.runtime.lre_dp.execute_decision.return_value = {"status": "executed"}

            # Patch _init_protocols to NOT overwrite our mocks
            with patch.object(self.runtime, '_init_protocols', new=AsyncMock()), \
                 patch('src.runtime.PersistenceEngine') as MockPersistence:

                mock_persistence_instance = MockPersistence.return_value
                mock_persistence_instance.initialize = AsyncMock()
                mock_persistence_instance._on_decision_event = AsyncMock()
                mock_persistence_instance.close = AsyncMock()

                await self.runtime.initialize()
                # Re-inject our mocks into pipeline because initialize() creates a new pipeline with current self.lpi etc.
                # Since we set self.lpi BEFORE initialize, and patched _init_protocols to do nothing,
                # initialize() will use our self.lpi to create the pipeline.
                pass

            decision = {
                "action": "test_action",
                "agent_id": "agent_001",
                "payload": "data"
            }

            result = await self.runtime.process_decision(decision)

            self.assertEqual(result["status"], "executed")
            self.assertIn("trace_id", result)
            self.assertEqual(result["decision"], decision)

        asyncio.run(run_test())

    def test_decision_pipeline_agent_offline(self):
        async def run_test():
            self.runtime.lpi = MagicMock()
            self.runtime.lri = MagicMock()
            self.runtime.lre_dp = MagicMock()

            self.runtime.lpi.query_presence.return_value = False

            with patch.object(self.runtime, '_init_protocols', new=AsyncMock()), \
                 patch('src.runtime.PersistenceEngine') as MockPersistence:

                mock_persistence_instance = MockPersistence.return_value
                mock_persistence_instance.initialize = AsyncMock()
                mock_persistence_instance._on_decision_event = AsyncMock()
                mock_persistence_instance.close = AsyncMock()

                await self.runtime.initialize()

            decision = {
                "action": "test_action",
                "agent_id": "agent_offline",
                "payload": "data"
            }

            result = await self.runtime.process_decision(decision)

            self.assertEqual(result["status"], "deferred")
            self.assertEqual(result["metadata"]["reason"], "agent_offline")

        asyncio.run(run_test())

    def test_decision_pipeline_invalid_input(self):
        async def run_test():
            with patch.object(self.runtime, '_init_protocols', new=AsyncMock()), \
                 patch('src.runtime.PersistenceEngine') as MockPersistence:

                mock_persistence_instance = MockPersistence.return_value
                mock_persistence_instance.initialize = AsyncMock()
                mock_persistence_instance._on_decision_event = AsyncMock()
                mock_persistence_instance.close = AsyncMock()

                await self.runtime.initialize()

            # Missing agent_id
            decision = {
                "action": "test_action",
                "payload": "data"
            }

            result = await self.runtime.process_decision(decision)

            self.assertEqual(result["status"], "rejected")
            self.assertIn("Invalid input format", result["errors"])

        asyncio.run(run_test())

    def test_event_bus_publish_subscribe(self):
        async def run_test():
            bus = EventBus()
            received = []

            async def handler(topic, data):
                received.append((topic, data))

            await bus.subscribe("decision.*", handler)
            await bus.publish("decision.received", {"id": 1})

            self.assertEqual(len(received), 1)
            self.assertEqual(received[0][0], "decision.received")
            self.assertEqual(received[0][1], {"id": 1})

        asyncio.run(run_test())

    def test_decision_context_timing(self):
        async def run_test():
            decision = {"agent_id": "1", "action": "test", "payload": {}}
            async with DecisionContext(decision) as ctx:
                await asyncio.sleep(0.01)

            self.assertGreater(ctx.get_latency_ms(), 0)
            self.assertIsNotNone(ctx.get_trace_id())

        asyncio.run(run_test())

    def test_graceful_shutdown(self):
        async def run_test():
            with patch.object(self.runtime, '_init_protocols', new=AsyncMock()), \
                 patch('src.runtime.PersistenceEngine') as MockPersistence:

                mock_persistence_instance = MockPersistence.return_value
                mock_persistence_instance.initialize = AsyncMock()
                mock_persistence_instance._on_decision_event = AsyncMock()
                mock_persistence_instance.close = AsyncMock()

                await self.runtime.initialize()

            await self.runtime.shutdown()
            self.assertFalse(self.runtime._running)

            # Verify close called
            self.runtime.persistence.close.assert_called_once()

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
