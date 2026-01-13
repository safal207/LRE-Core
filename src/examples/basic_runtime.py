import asyncio
import logging
import sys
from pathlib import Path

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.runtime import LRERuntime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

async def main():
    # 1. Bootstrap LRERuntime
    runtime = LRERuntime()

    # 2. Initialize protocols
    await runtime.initialize()

    # 3. Send mock "Emergency Shutdown" decision
    decision = {
        "action": "emergency_shutdown",
        "agent_id": "agent_001",
        "payload": {
            "reason": "High load detected",
            "severity": "critical"
        }
    }

    print(f"\nSending decision: {decision}")

    # 4. Process the decision
    result = await runtime.process_decision(decision)

    # 5. Print execution log
    print(f"\nExecution Result:")
    print(result)

    # 6. Graceful shutdown
    await runtime.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
