"""
LTP WebSocket Test Client

Connects to the LTP server and sends test commands.

Usage:
    # Terminal 1: Start server
    python src/examples/server_demo.py

    # Terminal 2: Run client
    python src/examples/test_client.py
"""

import asyncio
import websockets
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.events import Events

async def test_client():
    uri = "ws://localhost:8000"

    print("\n" + "="*70)
    print("🔌 LTP WebSocket Test Client")
    print("="*70)

    print(f"\nConnecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!\n")

            # Test 1: system_ping
            print("="*70)
            print("Test 1: System Ping")
            print("="*70)

            command = {
                "type": Events.SYSTEM_PING,
                "trace_id": "test-uuid-1",
                "timestamp": "2025-01-14T12:00:00Z",
                "payload": {}
            }

            print(f"📤 Sending: {json.dumps(command, indent=2)}")
            await websocket.send(json.dumps(command))

            response = await websocket.recv()
            result = json.loads(response)

            print(f"📥 Received: {json.dumps(result, indent=2)}\n")

            # Test 2: echo_payload
            print("="*70)
            print("Test 2: Echo Payload")
            print("="*70)

            command = {
                "type": Events.ECHO_PAYLOAD,
                "trace_id": "test-uuid-2",
                "timestamp": "2025-01-14T12:00:01Z",
                "payload": {
                    "message": "Hello from WebSocket client!",
                    "timestamp": 1234567890,
                    "data": [1, 2, 3, 4, 5]
                }
            }

            print(f"📤 Sending: {json.dumps(command, indent=2)}")
            await websocket.send(json.dumps(command))

            response = await websocket.recv()
            result = json.loads(response)

            print(f"📥 Received: {json.dumps(result, indent=2)}\n")

            # Test 3: Unknown action (error handling)
            print("="*70)
            print("Test 3: Unknown Action (Error Test)")
            print("="*70)

            command = {
                "type": "nonexistent_action",
                "trace_id": "test-uuid-3",
                "timestamp": "2025-01-14T12:00:02Z",
                "payload": {}
            }

            print(f"📤 Sending: {json.dumps(command, indent=2)}")
            await websocket.send(json.dumps(command))

            response = await websocket.recv()
            result = json.loads(response)

            print(f"📥 Received: {json.dumps(result, indent=2)}\n")

            # Test 4: Invalid JSON (error handling)
            print("="*70)
            print("Test 4: Invalid Command (Missing 'type')")
            print("="*70)

            command = {
                "trace_id": "test-uuid-4",
                "timestamp": "2025-01-14T12:00:03Z",
                "payload": {}
                # Missing 'type' field
            }

            print(f"📤 Sending: {json.dumps(command, indent=2)}")
            await websocket.send(json.dumps(command))

            response = await websocket.recv()
            result = json.loads(response)

            print(f"📥 Received: {json.dumps(result, indent=2)}\n")

            print("="*70)
            print("✅ All tests completed successfully!")
            print("="*70)
            print()

    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused. Is the server running?")
        print("   Start it with: python src/examples/server_demo.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_client())
