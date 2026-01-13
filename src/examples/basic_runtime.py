import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.runtime import LRERuntime

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

async def main():
    print("\n" + "="*60)
    print("🎯 LRE-Core Persistence Demo")
    print("="*60)

    # Initialize runtime
    runtime = LRERuntime()
    await runtime.initialize()

    agent_id = "agent_001"

    # Execute multiple actions
    print("\n📝 Executing actions...")

    actions = [
        {"action": "system_ping", "agent_id": agent_id, "payload": {}},
        {"action": "echo_payload", "agent_id": agent_id, "payload": {"test": "data"}},
        {"action": "log_message", "agent_id": agent_id, "payload": {"message": "Test log", "level": "info"}},
        {"action": "nonexistent_action", "agent_id": agent_id, "payload": {}},  # This will be rejected
    ]

    for decision in actions:
        result = await runtime.process_decision(decision)
        print(f"   {decision['action']}: {result['status']}")

    # Wait a moment for async logging to complete
    await asyncio.sleep(0.5)

    # Query history
    print(f"\n📊 Decision History for {agent_id}:")
    history = await runtime.persistence.get_agent_history(agent_id, limit=10)

    for record in history:
        print(f"\n   Trace ID: {record['trace_id']}")
        print(f"   Action: {record['action']}")
        print(f"   Status: {record['status']}")
        print(f"   Latency: {record['latency_ms']:.2f}ms")
        if record['error_msg']:
            print(f"   Error: {record['error_msg']}")

    # Show statistics
    print("\n📈 Overall Statistics:")
    stats = await runtime.persistence.get_statistics()
    print(f"   Total Decisions: {stats.get('total_decisions', 0)}")
    print(f"   Unique Agents: {stats.get('unique_agents', 0)}")
    print(f"   Executed: {stats.get('executed_count', 0)}")
    print(f"   Failed: {stats.get('failed_count', 0)}")

    avg_latency = stats.get('avg_latency_ms')
    if avg_latency is not None:
        print(f"   Avg Latency: {avg_latency:.2f}ms")
    else:
        print(f"   Avg Latency: N/A")

    # Demonstrate query filters
    print(f"\n🔍 Query: Only executed actions")
    executed = await runtime.persistence.get_agent_history(
        agent_id,
        status="executed",
        limit=5
    )
    print(f"   Found {len(executed)} executed actions")

    print("\n🛑 Shutting down...")
    await runtime.shutdown()
    print("✅ Complete! Check ./data/lre_core.db\n")

if __name__ == "__main__":
    asyncio.run(main())
