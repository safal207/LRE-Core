from typing import Dict, Callable, Optional, List, Any
import functools

class ActionRegistry:
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def register(self, name: str, handler: Callable):
        """Register an action handler."""
        if name in self._handlers:
            # We might want to warn or overwrite. For now, overwrite is fine as per Python dicts.
            pass
        self._handlers[name] = handler

    def get_handler(self, name: str) -> Optional[Callable]:
        """Get handler by action name."""
        return self._handlers.get(name)

    def list_actions(self) -> List[str]:
        """List all registered action names."""
        return list(self._handlers.keys())

    def has_action(self, name: str) -> bool:
        """Check if action exists."""
        return name in self._handlers

# Global default registry (module-level)
_default_registry: Optional[ActionRegistry] = None

def set_default_registry(registry: ActionRegistry):
    """Set the default registry for @action decorator."""
    global _default_registry
    _default_registry = registry

def action(name: str, registry: Optional[ActionRegistry] = None):
    """
    Decorator to register an action handler.

    Usage:
        @action("my_action")
        async def my_handler(ctx: DecisionContext) -> dict:
            return {"status": "success"}
    """
    def decorator(func: Callable):
        target_registry = registry or _default_registry
        if target_registry is None:
            # This might happen if the decorator is evaluated before the registry is set.
            # Ideally, the user sets the default registry before importing modules that use this decorator.
            # But module level execution happens at import time.
            # So, we need to ensure set_default_registry is called before imports of stdlib.
            raise RuntimeError(f"No registry available for action '{name}'. Set default registry first.")

        target_registry.register(name, func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator
