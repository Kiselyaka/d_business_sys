import logging

import httpx

from mini_shop.application.contracts import OrderCreatedEvent
from mini_shop.application.ports import EventPublicationError

logger = logging.getLogger(__name__)


class HttpIntegrationEventPublisher:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._endpoint = f"{base_url.rstrip('/')}/api/v1/events"
        self._timeout_seconds = timeout_seconds

    def publish(self, event: OrderCreatedEvent) -> None:
        try:
            response = httpx.post(self._endpoint, json=event.model_dump(mode="json"), timeout=self._timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPError as error:
            logger.error("external_event_publish_failed", extra={"event_id": event.event_id, "error": str(error)})
            raise EventPublicationError("Order was saved, but order.created could not be delivered to the Integration Platform") from error
