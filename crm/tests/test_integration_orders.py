from sqlalchemy import func, select
from fastapi.testclient import TestClient

from crm.database import create_database_engine, create_session_factory
from crm.domain.models import Base, Customer, Deal, DealPosition
from crm.main import create_app
from crm.settings import Settings


def _request() -> dict[str, object]:
    return {
        "external_order_id": "order-001",
        "client": {
            "external_customer_id": "customer-001",
            "name": "Ada Lovelace",
            "email": "ada@example.test",
            "phone": None,
        },
        "deal": {"amount": "21.00", "currency": "EUR"},
        "delivery_address": {
            "country": "RU",
            "city": "Moscow",
            "postal_code": "101000",
            "street": "Tverskaya",
            "building": "1",
            "apartment": None,
        },
        "positions": [
            {"external_product_code": "SKU-001", "title": "Example Product", "quantity": 2, "price": "10.50"}
        ],
    }


def _client_and_session_factory() -> tuple[TestClient, object]:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    app = create_app(Settings(database_url="sqlite+pysqlite:///:memory:"), session_factory=session_factory)
    return TestClient(app), session_factory


def test_creates_customer_deal_and_positions() -> None:
    client, session_factory = _client_and_session_factory()

    response = client.post("/api/integration/orders", json=_request())

    assert response.status_code == 200
    assert response.json() == {"status": "accepted", "external_order_id": "order-001"}
    with session_factory() as session:  # type: ignore[operator]
        assert session.scalar(select(func.count()).select_from(Customer)) == 1
        assert session.scalar(select(func.count()).select_from(Deal)) == 1
        assert session.scalar(select(func.count()).select_from(DealPosition)) == 1


def test_repeated_order_updates_instead_of_creating_duplicates() -> None:
    client, session_factory = _client_and_session_factory()
    first = _request()
    second = _request()
    second["client"] = {**second["client"], "name": "Ada Updated"}  # type: ignore[arg-type]
    second["positions"] = [
        {"external_product_code": "SKU-001", "title": "Example Product", "quantity": 3, "price": "10.50"}
    ]

    assert client.post("/api/integration/orders", json=first).status_code == 200
    assert client.post("/api/integration/orders", json=second).status_code == 200
    with session_factory() as session:  # type: ignore[operator]
        assert session.scalar(select(func.count()).select_from(Customer)) == 1
        assert session.scalar(select(func.count()).select_from(Deal)) == 1
        assert session.scalar(select(func.count()).select_from(DealPosition)) == 1
        customer = session.scalar(select(Customer))
        position = session.scalar(select(DealPosition))
    assert customer is not None and customer.name == "Ada Updated"
    assert position is not None and position.quantity == 3


def test_rejects_an_invalid_target_contract() -> None:
    client, _ = _client_and_session_factory()

    response = client.post("/api/integration/orders", json={"external_order_id": "order-001"})

    assert response.status_code == 422
