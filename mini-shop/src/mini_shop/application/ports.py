from typing import Protocol

from mini_shop.application.contracts import OrderCreatedEvent


class EventPublicationError(RuntimeError):
    """The persisted order could not be submitted to the Integration Platform."""


class IntegrationEventPublisher(Protocol):
    def publish(self, event: OrderCreatedEvent) -> None:
        """Submit one external event to the Integration Platform."""
