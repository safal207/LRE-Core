"""
LTP WebSocket Server Demo

Starts the LRE-Core runtime with WebSocket transport.

Usage:
    python src/examples/server_demo.py

Then connect a client to: ws://localhost:8000
"""

import asyncio
import websockets
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.runtime import LRERuntime
from src.ltp.handler import handle_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    print("\n" + "="*70)
    print("🚀 LRE-Core WebSocket Server")
    print("="*70)

    # Initialize runtime
    logger.info("Initializing LRE-Core runtime...")
    runtime = LRERuntime()
    await runtime.initialize()

    print("\n✅ Runtime initialized successfully")
    print(f"   Available actions: {', '.join(runtime.registry.list_actions())}")

    # Start WebSocket server
    host = "localhost"
    port = 8000

    logger.info(f"Starting WebSocket server on {host}:{port}")

    async with websockets.serve(
        lambda ws: handle_client(ws, runtime),
        host,
        port
    ):
        print(f"\n✅ LTP Server running on ws://{host}:{port}")
        print("\n" + "="*70)
        print("📡 Ready to accept connections!")
        print("="*70)

        print("\nExample commands to send via WebSocket:")
        print('  {"action": "system_ping", "agent_id": "agent_001", "payload": {}}')
        print('  {"action": "echo_payload", "agent_id": "agent_001", "payload": {"test": "data"}}')

        print("\nPress Ctrl+C to stop the server\n")

        # Run forever
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            pass

    # Cleanup
    logger.info("Shutting down runtime...")
    await runtime.shutdown()
    print("\n✅ Server stopped cleanly\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Received interrupt signal")
