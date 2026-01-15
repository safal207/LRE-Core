import unittest
import asyncio
import sys
from unittest.mock import MagicMock, patch
from src.execution.registry import ActionRegistry, action, set_default_registry

# Set default registry immediately to avoid import errors in stdlib
_test_registry = ActionRegistry()
set_default_registry(_test_registry)

# Import stdlib to register actions to _test_registry
from src.execution.stdlib import system_ping, echo_payload
from src.decision.context import DecisionContext
from src.lre_dp import LRE_DP
from src.runtime import LRERuntime

class TestActionRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ActionRegistry()
        set_default_registry(self.registry)

    def test_register_and_get(self):
        async def handler(ctx):
            return {"status": "ok"}

        self.registry.register("test_action", handler)
        self.assertEqual(self.registry.get_handler("test_action"), handler)
        self.assertTrue(self.registry.has_action("test_action"))
        self.assertIn("test_action", self.registry.list_actions())

    def test_decorator_registration(self):
        @action("decorated_action")
        async def handler(ctx):
            return {"status": "decorated"}

        self.assertTrue(self.registry.has_action("decorated_action"))

    def test_decorator_explicit_registry(self):
        other_registry = ActionRegistry()
        @action("explicit_action", registry=other_registry)
        async def handler(ctx):
            pass

        self.assertTrue(other_registry.has_action("explicit_action"))
        self.assertFalse(self.registry.has_action("explicit_action"))

class TestStdLib(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.registry = ActionRegistry()
        set_default_registry(self.registry)
        # Register actions manually for this test case since they are already imported
        self.registry.register("system_ping", system_ping)
        self.registry.register("echo_payload", echo_payload)

    async def test_system_ping(self):
        handler = self.registry.get_handler("system_ping")
        self.assertIsNotNone(handler)

        ctx = DecisionContext({"action": "system_ping", "agent_id": "test", "payload": {}})
        result = await handler(ctx)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "pong")
        self.assertIn("timestamp", result)

    async def test_echo_payload(self):
        handler = self.registry.get_handler("echo_payload")
        ctx = DecisionContext({"action": "echo_payload", "agent_id": "test", "payload": {"foo": "bar"}})
        result = await handler(ctx)

        self.assertEqual(result["payload"], {"foo": "bar"})

class TestIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_lre_dp_execution(self):
        registry = ActionRegistry()

        async def mock_handler(ctx):
            return {"status": "handled"}

        registry.register("test_action", mock_handler)

        lre_dp = LRE_DP(lpi=MagicMock(), lri=MagicMock(), registry=registry)

        # Case 1: passing dict directly
        result = await lre_dp.execute_decision({"action": "test_action"})
        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["result"]["status"], "handled")

        # Case 2: Unknown action
        result = await lre_dp.execute_decision({"action": "unknown"})
        self.assertEqual(result["status"], "rejected")
        self.assertIn("Unknown action", result["reason"])

    async def test_runtime_initialization(self):
        runtime = LRERuntime()

        # Force reload of stdlib to ensure decorators run against runtime.registry
        if 'src.execution.stdlib' in sys.modules:
            del sys.modules['src.execution.stdlib']

        # Mock _init_protocols to avoid real imports
        with patch.object(runtime, '_init_protocols', new_callable=MagicMock) as mock_init_proto:
            async def side_effect():
                # Manually set mocks that _init_protocols would set
                runtime.lre_dp = MagicMock()
                # pipeline is created after _init_protocols in initialize(), so we don't mock it here

            mock_init_proto.side_effect = side_effect

            await runtime.initialize()

            self.assertIsNotNone(runtime.registry)
            # Check if actions were registered
            self.assertTrue(len(runtime.registry.list_actions()) > 0)
            self.assertTrue(runtime.registry.has_action("system_ping"))

if __name__ == "__main__":
    unittest.main()
