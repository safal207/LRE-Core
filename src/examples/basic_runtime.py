import asyncio
import logging
import sys
from pathlib import Path

# Adjust path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.runtime import LRERuntime

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

async def main():
    print("\n" + "="*60)
    print("🚀 LRE-Core Action Registry Demo")
    print("="*60)

    # Initialize runtime
    runtime = LRERuntime()
    await runtime.initialize()
    print(f"\n✅ Runtime initialized with {len(runtime.registry.list_actions())} actions")
    print(f"   Available: {', '.join(runtime.registry.list_actions())}\n")

    # Helper to print result safely
    def get_action_result(ctx_summary):
        """Extracts the actual action result from the context summary."""
        # Context status
        if ctx_summary.get("status") != "executed":
             return ctx_summary

        # LRE-DP result
        lre_dp_res = ctx_summary.get("result", {})
        if not isinstance(lre_dp_res, dict):
             return lre_dp_res

        # Check LRE-DP status
        if lre_dp_res.get("status") == "executed":
             return lre_dp_res.get("result", {})

        # If rejected/failed in LRE-DP
        return lre_dp_res

    # Test 1: system_ping
    print("📡 Test 1: System Ping")
    result = await runtime.process_decision({
        "action": "system_ping",
        "agent_id": "agent_001",
        "payload": {}
    })
    print(f"   Status: {result['status']}")

    action_res = get_action_result(result)
    if isinstance(action_res, dict) and "message" in action_res:
         print(f"   Message: {action_res['message']}")

    if 'latency_ms' in result:
        print(f"   Latency: {result['latency_ms']:.2f}ms\n")
    else:
        print("\n")

    # Test 2: echo_payload
    print("🔊 Test 2: Echo Payload")
    result = await runtime.process_decision({
        "action": "echo_payload",
        "agent_id": "agent_001",
        "payload": {"test": "data", "number": 42}
    })
    action_res = get_action_result(result)
    if isinstance(action_res, dict) and "echo" in action_res:
        print(f"   Echoed: {action_res['echo']}\n")
    else:
        print(f"   Result: {action_res}\n")

    # Test 3: Unknown action (should not crash)
    print("❌ Test 3: Unknown Action")
    result = await runtime.process_decision({
        "action": "nonexistent_action",
        "agent_id": "agent_001",
        "payload": {}
    })
    print(f"   Status: {result['status']}")

    action_res = get_action_result(result)
    if isinstance(action_res, dict) and "reason" in action_res:
        print(f"   Reason: {action_res['reason']}\n")
    else:
        print(f"   Result: {action_res}\n")

    # Test 4: mock_deploy
    print("🚀 Test 4: Mock Deploy (1 second)")
    result = await runtime.process_decision({
        "action": "mock_deploy",
        "agent_id": "agent_001",
        "payload": {"duration": 1}
    })
    action_res = get_action_result(result)
    if isinstance(action_res, dict) and "deployment_id" in action_res:
        print(f"   Deployment ID: {action_res['deployment_id']}")
        print(f"   Duration: {action_res['duration']}s\n")
    else:
        print(f"   Result: {action_res}\n")

    print("🛑 Shutting down...")
    await runtime.shutdown()
    print("✅ Complete!\n")

if __name__ == "__main__":
    asyncio.run(main())
