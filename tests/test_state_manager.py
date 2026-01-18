
import asyncio
import pytest


@pytest.mark.asyncio
async def test_concurrent_state_updates_no_data_loss():
    """
    Test that concurrent state updates don't lose data by merging non-conflicting keys.
    """
    from src.storage.sqlite_backend import SQLiteBackend
    from src.storage.state_manager import StateManager

    backend = SQLiteBackend(":memory:")
    state_manager = StateManager(backend)

    trace_id = "concurrent-test"

    # Initialize state
    state_manager.update_state(trace_id, {'initial': True})

    async def worker(worker_id: int):
        """Each worker adds its own key."""
        state_manager.update_state(
            trace_id,
            {f'worker_{worker_id}': True},
            merge=True
        )

    # Run 10 workers concurrently
    await asyncio.gather(*[worker(i) for i in range(10)])

    # Verify final count
    final_state = state_manager.get_state(trace_id)
    assert len(final_state.keys()) == 11 # 10 workers + initial key
    assert final_state['initial'] == True
    for i in range(10):
        assert f'worker_{i}' in final_state


def test_update_state_merge_vs_replace():
    """Test merge=True vs merge=False behavior."""
    from src.storage.sqlite_backend import SQLiteBackend
    from src.storage.state_manager import StateManager

    backend = SQLiteBackend(":memory:")
    state_manager = StateManager(backend)

    trace_id = "test-merge"

    # Initial state
    state_manager.update_state(trace_id, {'a': 1, 'b': 2})

    # Merge update - should keep 'a'
    state_manager.update_state(trace_id, {'b': 3, 'c': 4}, merge=True)
    state = state_manager.get_state(trace_id)
    assert state == {'a': 1, 'b': 3, 'c': 4}

    # Replace update - should remove 'a' and 'c'
    state_manager.update_state(trace_id, {'x': 10}, merge=False)
    state = state_manager.get_state(trace_id)
    assert state == {'x': 10}
