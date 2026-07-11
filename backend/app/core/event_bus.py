"""
Module implementing the thread-safe, in-memory asynchronous Event Bus.

Handles real-time publishing, history logging, pub-sub routing, and chronological
replay capabilities for Server-Sent Events (SSE).
"""

import asyncio
from typing import Dict, List
from app.models.event import Event
from app.core.logger import logger


class EventBus:
    """
    In-memory async Event Bus for publishing, subscribing, and replaying events.
    """
    def __init__(self) -> None:
        self._events: List[Event] = []
        self._subscriptions: Dict[str, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def publish(self, event: Event) -> None:
        """
        Publishes a unified flat event to the bus.
        
        Appends the event to memory storage, routes it to all active subscriber queues
        for the given mission, and registers it through the structured logger.
        """
        async with self._lock:
            self._events.append(event)
            
            # Log the event through the structured logger with formatted fields
            extra_payload = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "agent": event.agent.value if event.agent else None,
                "status": event.status.value if event.status else None,
                "severity": event.severity.value,
                "confidence": event.confidence,
                "latency_ms": event.latency_ms,
                "tools_used": event.tools_used,
                "metadata": event.metadata
            }
            logger.info(
                f"[EVENT BUS] published={event.event_type.value} title='{event.title}' message='{event.message}'",
                extra={"extra_fields": extra_payload}
            )
            
            # Forward event to subscribers of this specific mission
            m_id = event.mission_id
            if m_id in self._subscriptions:
                for q in self._subscriptions[m_id]:
                    await q.put(event)

    async def get_events(self, mission_id: str) -> List[Event]:
        """
        Retrieves all historical events registered to a specific mission.
        """
        async with self._lock:
            return [e for e in self._events if e.mission_id == mission_id]

    async def replay_events(self, mission_id: str) -> List[Event]:
        """
        Replays and returns all mission events in chronological order based on timestamp.
        """
        events = await self.get_events(mission_id)
        # Sort chronologically by timestamp
        return sorted(events, key=lambda x: x.timestamp)

    async def subscribe(self, mission_id: str) -> asyncio.Queue:
        """
        Registers an active real-time subscriber queue for a specific mission_id.
        
        Returns:
            An asyncio.Queue yielding Event payloads as they are published.
        """
        async with self._lock:
            q: asyncio.Queue[Event] = asyncio.Queue()
            if mission_id not in self._subscriptions:
                self._subscriptions[mission_id] = []
            self._subscriptions[mission_id].append(q)
            logger.debug(f"[EVENT BUS] Subscribed queue to mission_id={mission_id}")
            return q

    async def unsubscribe(self, mission_id: str, queue: asyncio.Queue) -> None:
        """
        Deregisters and closes a subscriber queue to avoid memory footprint leaks.
        """
        async with self._lock:
            if mission_id in self._subscriptions:
                if queue in self._subscriptions[mission_id]:
                    self._subscriptions[mission_id].remove(queue)
                    logger.debug(f"[EVENT BUS] Unsubscribed queue from mission_id={mission_id}")
                if not self._subscriptions[mission_id]:
                    del self._subscriptions[mission_id]

    async def clear_mission(self, mission_id: str) -> None:
        """
        Completely clears historical events and subscriber queues for a given mission.
        """
        async with self._lock:
            # Remove from historical list
            self._events = [e for e in self._events if e.mission_id != mission_id]
            # Delete any active subscriptions
            if mission_id in self._subscriptions:
                del self._subscriptions[mission_id]
            logger.debug(f"[EVENT BUS] Cleared events for mission_id={mission_id}")


# Instantiate a global singleton Event Bus
event_bus = EventBus()
