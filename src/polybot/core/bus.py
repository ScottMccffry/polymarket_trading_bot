"""Event bus for publishing and subscribing to events."""

import asyncio
import structlog
from collections import defaultdict
from typing import Callable, Coroutine, Type, Any

from .events import Event

logger = structlog.get_logger()

Handler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """Async event bus for loose coupling between components."""

    def __init__(self) -> None:
        self._handlers: dict[Type[Event], list[Handler]] = defaultdict(list)
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False
        self._task: asyncio.Task[None] | None = None

    def subscribe(self, event_type: Type[Event], handler: Handler) -> None:
        """Subscribe a handler to an event type."""
        self._handlers[event_type].append(handler)
        logger.debug(
            "handler_subscribed",
            event_type=event_type.__name__,
            handler=handler.__name__,
        )

    def unsubscribe(self, event_type: Type[Event], handler: Handler) -> None:
        """Unsubscribe a handler from an event type."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        await self._queue.put(event)
        logger.debug("event_published", event_type=type(event).__name__)

    def publish_sync(self, event: Event) -> None:
        """Synchronously add an event to the queue."""
        self._queue.put_nowait(event)

    async def start(self) -> None:
        """Start processing events."""
        self._running = True
        logger.info("event_bus_started")

        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            handlers = self._handlers[type(event)]
            if not handlers:
                logger.debug(
                    "no_handlers_for_event",
                    event_type=type(event).__name__,
                )
                continue

            # Execute handlers concurrently
            results = await asyncio.gather(
                *(self._safe_execute(h, event) for h in handlers),
                return_exceptions=True,
            )

            # Log any errors
            for handler, result in zip(handlers, results):
                if isinstance(result, Exception):
                    logger.error(
                        "handler_error",
                        handler=handler.__name__,
                        event_type=type(event).__name__,
                        error=str(result),
                    )

    async def _safe_execute(self, handler: Handler, event: Event) -> None:
        """Execute a handler with error handling."""
        try:
            await handler(event)
        except Exception as e:
            logger.exception(
                "handler_exception",
                handler=handler.__name__,
                event_type=type(event).__name__,
            )
            raise

    def stop(self) -> None:
        """Stop processing events."""
        self._running = False
        logger.info("event_bus_stopped")

    async def start_background(self) -> None:
        """Start the event bus in a background task."""
        self._task = asyncio.create_task(self.start())

    async def stop_and_wait(self) -> None:
        """Stop the event bus and wait for completion."""
        self.stop()
        if self._task:
            await self._task
