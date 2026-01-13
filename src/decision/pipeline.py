import logging
import asyncio
from typing import Dict, Any, Optional

from src.decision.context import DecisionContext

logger = logging.getLogger(__name__)

class DecisionPipeline:
    """
    Executes decisions through the LRE-Core architecture.
    """
    def __init__(self, lpi: Any, lri: Any, lre_dp: Any, event_bus: Any):
        self.lpi = lpi
        self.lri = lri
        self.lre_dp = lre_dp
        self.event_bus = event_bus

    async def execute(self, dml_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the decision pipeline logic.
        """
        # 1. Parse & Validate
        if not self._validate_input(dml_input):
            return {
                "status": "rejected",
                "errors": ["Invalid input format"],
                "decision": dml_input
            }

        async with DecisionContext(dml_input) as ctx:
            try:
                await self.event_bus.publish("decision.received", ctx.get_summary())

                agent_id = dml_input.get("agent_id")
                action = dml_input.get("action")

                # 3. Presence Check (LPI)
                is_online = False
                try:
                    presence_result = self.lpi.query_presence(agent_id)
                    if asyncio.iscoroutine(presence_result):
                        is_online = await presence_result
                    else:
                        is_online = presence_result
                except AttributeError:
                    logger.warning(f"LPI.query_presence not found, assuming online for {agent_id}")
                    is_online = True
                except Exception as e:
                    logger.error(f"Error querying presence: {e}")
                    is_online = False

                if not is_online:
                    ctx.set_result(None, status="deferred")
                    ctx.add_metadata("reason", "agent_offline")
                    await self.event_bus.publish("decision.deferred", ctx.get_summary())
                    return ctx.get_summary()

                # 4. Routing (LRI)
                try:
                    route = self.lri.calculate_route(agent_id, action)
                    if asyncio.iscoroutine(route):
                        route = await route
                    ctx.add_metadata("route", route)
                except AttributeError:
                     logger.warning(f"LRI.calculate_route not found, using default route")
                     ctx.add_metadata("route", "direct")
                except Exception as e:
                    logger.error(f"Error calculating route: {e}")
                    ctx.mark_failed(e)
                    await self.event_bus.publish("decision.failed", ctx.get_summary())
                    return ctx.get_summary()

                # 5. Execute (LRE-DP)
                await self.event_bus.publish("decision.executing", ctx.get_summary())

                try:
                    res = self.lre_dp.execute_decision(ctx)
                    if asyncio.iscoroutine(res):
                        res = await res

                    final_status = res.get("status", "executed") if res else "executed"
                    ctx.set_result(res if res else {"status": "executed"}, status=final_status)

                    if final_status == "failed":
                        await self.event_bus.publish("decision.failed", ctx.get_summary())
                    elif final_status == "rejected":
                        await self.event_bus.publish("decision.rejected", ctx.get_summary())
                    elif final_status == "deferred":
                        await self.event_bus.publish("decision.deferred", ctx.get_summary())
                    else:
                        await self.event_bus.publish("decision.completed", ctx.get_summary())

                except Exception as e:
                    logger.error(f"Error executing decision: {e}")
                    ctx.mark_failed(e)
                    await self.event_bus.publish("decision.failed", ctx.get_summary())

                return ctx.get_summary()

            except Exception as e:
                # Catch-all for unexpected errors in the pipeline setup itself
                logger.error(f"Unexpected error in pipeline: {e}")
                ctx.mark_failed(e)
                return ctx.get_summary()

    def _validate_input(self, dml_input: Dict[str, Any]) -> bool:
        required = ["action", "agent_id", "payload"]
        return all(k in dml_input for k in required)
