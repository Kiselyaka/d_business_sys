from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from mini_shop.application.contracts import OrderCreatedEvent
from mini_shop.application.ports import EventPublicationError
from mini_shop.database import create_database_engine, create_session_factory
from mini_shop.domain.models import Base, Customer, Order, Product
from mini_shop.main import create_app
from mini_shop.settings import Settings


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[OrderCreatedEvent] = []

    def publish(self, event: OrderCreatedEvent) -> None:
        self.events.append(event)


class FailingPublisher:
    def publish(self, event: OrderCreatedEvent) -> None:
        raise EventPublicationError("platform unavailable")


def build_client(publisher: RecordingPublisher | FailingPublisher) -> tuple[TestClient, object]:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    with session_factory.begin() as session:
        session.add(Product(id="product-1", product_code="SKU-001", name="Example Product", price=Decimal("10.50")))

    app = create_app(Settings(database_url="sqlite+pysqlite:///:memory:"), publisher=publisher, session_factory=session_factory)
    return TestClient(app), session_factory


def order_request() -> dict[str, object]:
    return {
        "customer": {"customer_id": "C-1001", "full_name": "Example Customer", "email": "customer@example.com", "phone": None},
        "shipping_address": {
            "country": "LV",
            "city": "Riga",
            "postal_code": "LV-1001",
            "street": "Example Street",
            "building": "1",
            "apartment": None,
        },
        "items": [{"product_code": "SKU-001", "quantity": 2}],
    }


def test_create_order_persists_domain_data_calculates_total_and_publishes_event() -> None:
    publisher = RecordingPublisher()
    client, session_factory = build_client(publisher)

    response = client.post("/api/orders", json=order_request())

    assert response.status_code == 201
    order_id = response.json()["order_id"]
    with session_factory() as session:
        order = session.get(Order, order_id)
        customer = session.scalar(select(Customer).where(Customer.customer_id == "C-1001"))
        assert order is not None
        assert customer is not None
        assert order.status == "CREATED"
        assert order.total_amount == Decimal("21.00")
        assert len(order.items) == 1
        assert order.items[0].name_snapshot == "Example Product"

    assert len(publisher.events) == 1
    event = publisher.events[0]
    assert event.event_type == "order.created"
    assert event.source_system == "mini-shop"
    assert event.correlation_id == f"order-{order_id}"
    assert event.payload.order_id == order_id
    assert event.payload.total_amount == Decimal("21.00")
    assert event.payload.items[0].unit_price == Decimal("10.50")


def test_platform_failure_returns_clear_error_after_order_is_persisted() -> None:
    client, session_factory = build_client(FailingPublisher())

    response = client.post("/api/orders", json=order_request())

    assert response.status_code == 502
    assert "platform unavailable" in response.json()["detail"]
    with session_factory() as session:
        assert len(session.scalars(select(Order)).all()) == 1
