import unittest
import asyncio
import tempfile
import json
from pathlib import Path
from src.persistence.engine import PersistenceEngine
from src.decision.context import DecisionContext

class TestPersistence(unittest.TestCase):
    def setUp(self):
        # Use temporary DB for tests
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.temp_db.name
        self.temp_db.close()

    def tearDown(self):
        # Clean up
        Path(self.db_path).unlink(missing_ok=True)

    def test_persistence_init(self):
        """Test database initialization."""
        async def run():
            engine = PersistenceEngine(self.db_path)
            await engine.initialize()

            # Check file exists
            self.assertTrue(Path(self.db_path).exists())

            await engine.close()

        asyncio.run(run())

    def test_log_decision(self):
        """Test logging a decision."""
        async def run():
            engine = PersistenceEngine(self.db_path)
            await engine.initialize()

            # Create decision context
            decision = {"action": "test", "agent_id": "agent_001", "payload": {}}
            ctx = DecisionContext(decision)
            async with ctx:
                 pass
            ctx.set_result({"status": "success"}, status="executed")

            # Log it
            await engine.log_decision(ctx)

            # Verify it's in DB
            history = await engine.get_agent_history("agent_001")
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["action"], "test")
            self.assertEqual(history[0]["agent_id"], "agent_001")

            await engine.close()

        asyncio.run(run())

    def test_query_filters(self):
        """Test history queries with filters."""
        async def run():
            engine = PersistenceEngine(self.db_path)
            await engine.initialize()

            # Log multiple decisions
            for i in range(5):
                decision = {"action": f"action_{i}", "agent_id": "agent_001", "payload": {}}
                ctx = DecisionContext(decision)
                async with ctx:
                    pass
                status = "executed" if i % 2 == 0 else "failed"
                ctx.set_result({}, status=status)
                await engine.log_decision(ctx)

            # Query all
            all_history = await engine.get_agent_history("agent_001", limit=10)
            self.assertEqual(len(all_history), 5)

            # Query only executed
            executed = await engine.get_agent_history("agent_001", status="executed")
            self.assertEqual(len(executed), 3)

            # Query only failed
            failed = await engine.get_agent_history("agent_001", status="failed")
            self.assertEqual(len(failed), 2)

            await engine.close()

        asyncio.run(run())

    def test_persistence_across_restarts(self):
        """Test that data survives runtime restarts."""
        async def run():
            # First session
            engine1 = PersistenceEngine(self.db_path)
            await engine1.initialize()

            decision = {"action": "test", "agent_id": "agent_001", "payload": {}}
            ctx = DecisionContext(decision)
            async with ctx:
                pass
            ctx.set_result({}, status="executed")
            await engine1.log_decision(ctx)
            await engine1.close()

            # Second session (new engine instance)
            engine2 = PersistenceEngine(self.db_path)
            await engine2.initialize()

            history = await engine2.get_agent_history("agent_001")
            self.assertEqual(len(history), 1)

            await engine2.close()

        asyncio.run(run())

    def test_error_logging(self):
        """Test that failed actions log errors."""
        async def run():
            engine = PersistenceEngine(self.db_path)
            await engine.initialize()

            decision = {"action": "fail_test", "agent_id": "agent_001", "payload": {}}
            ctx = DecisionContext(decision)
            try:
                async with ctx:
                    raise ValueError("Something went wrong")
            except:
                pass # context handles marking failed

            await engine.log_decision(ctx)

            history = await engine.get_agent_history("agent_001")
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["status"], "failed")
            self.assertIn("Something went wrong", history[0]["error_msg"])

            await engine.close()

        asyncio.run(run())

if __name__ == '__main__':
    unittest.main()
