import asyncio
import fnmatch
from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """
    Simple, in-memory async pub/sub system.
    Supports wildcard topic matching.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, topic: str, handler: Callable):
        """
        Subscribe a handler to a topic.
        """
        async with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            if handler not in self._subscribers[topic]:
                self._subscribers[topic].append(handler)
            logger.debug(f"Subscribed {handler} to {topic}")

    async def unsubscribe(self, topic: str, handler: Callable):
        """
        Remove a handler from a topic subscription.
        """
        async with self._lock:
            if topic in self._subscribers:
                if handler in self._subscribers[topic]:
                    self._subscribers[topic].remove(handler)
                    logger.debug(f"Unsubscribed {handler} from {topic}")
                    if not self._subscribers[topic]:
                        del self._subscribers[topic]

    async def publish(self, topic: str, data: Any):
        """
        Publish an event to a topic.
        Matches subscribers using simple wildcard matching.
        """
        handlers_to_call = []

        async with self._lock:
            for sub_topic, handlers in self._subscribers.items():
                if self._matches(sub_topic, topic):
                    handlers_to_call.extend(handlers)

        if not handlers_to_call:
            logger.debug(f"No subscribers for topic {topic}")
            return

        # Execute handlers concurrently
        # We catch exceptions to prevent one handler from breaking the bus or other handlers
        tasks = []
        for handler in handlers_to_call:
            tasks.append(self._safe_execute(handler, topic, data))

        await asyncio.gather(*tasks)

    def _matches(self, subscription_pattern: str, topic: str) -> bool:
        """
        Check if topic matches the subscription pattern.
        Supports simple shell-style wildcards via fnmatch.
        """
        return fnmatch.fnmatch(topic, subscription_pattern)

    async def _safe_execute(self, handler: Callable, topic: str, data: Any):
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(topic, data)
            else:
                # If the handler is synchronous, run it directly (or in a thread executor if needed,
                # but for now assuming fast sync handlers or async handlers)
                # Given strict async requirements, we might prefer enforcing async handlers,
                # but calling sync is safer than crashing.
                handler(topic, data)
        except Exception as e:
            logger.error(f"Error in event handler {handler} for topic {topic}: {e}", exc_info=True)
