from decimal import Decimal

import pytest
from pydantic import ValidationError

from mini_shop.application.contracts import ReservationResultRequest
from mini_shop.application.services import (
    OrderNotFoundError,
    ReservationResultConflictError,
    apply_reservation_result,
)
from mini_shop.database import create_database_engine, create_session_factory
from mini_shop.domain.models import Base, Customer, Order, OrderStatus


def build_session_factory() -> object:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    with session_factory.begin() as session:
        customer = Customer(id="customer-1", customer_id="C-1001", full_name="Example", email="example@test")
        session.add(customer)
        session.add(
            Order(
                id="order-1",
                customer=customer,
                currency="EUR",
                total_amount=Decimal("10.50"),
                status=OrderStatus.WAITING_FOR_RESERVATION.value,
                shipping_address={"country": "RU"},
            )
        )
    return session_factory


def reservation_result(result: str, **failure_details: str) -> ReservationResultRequest:
    return ReservationResultRequest(
        order_id="order-1",
        reservation_result=result,  # type: ignore[arg-type]
        warehouse_event_id="warehouse-event-1",
        **failure_details,
    )


@pytest.mark.parametrize(
    ("result", "expected_status", "failure_details"),
    [
        ("succeeded", "CONFIRMED", {}),
        ("failed", "REJECTED", {"reason_code": "OUT_OF_STOCK", "message": "No stock"}),
    ],
)
def test_waiting_order_accepts_warehouse_result(
    result: str, expected_status: str, failure_details: dict[str, str]
) -> None:
    session_factory = build_session_factory()

    response = apply_reservation_result(session_factory, reservation_result(result, **failure_details))  # type: ignore[arg-type]

    assert response.model_dump() == {"order_id": "order-1", "status": expected_status}
    with session_factory() as session:  # type: ignore[operator]
        order = session.get(Order, "order-1")
        assert order is not None and order.status == expected_status


@pytest.mark.parametrize(
    ("first", "second", "expected_status", "second_details"),
    [
        ("succeeded", "succeeded", "CONFIRMED", {}),
        ("failed", "failed", "REJECTED", {"reason_code": "OUT_OF_STOCK", "message": "No stock"}),
    ],
)
def test_same_reservation_result_is_idempotent(
    first: str, second: str, expected_status: str, second_details: dict[str, str]
) -> None:
    session_factory = build_session_factory()
    first_details = {"reason_code": "OUT_OF_STOCK", "message": "No stock"} if first == "failed" else {}

    assert apply_reservation_result(session_factory, reservation_result(first, **first_details)).status == expected_status  # type: ignore[arg-type]
    assert apply_reservation_result(session_factory, reservation_result(second, **second_details)).status == expected_status  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("first", "second", "first_details", "second_details"),
    [
        ("succeeded", "failed", {}, {"reason_code": "OUT_OF_STOCK", "message": "No stock"}),
        ("failed", "succeeded", {"reason_code": "OUT_OF_STOCK", "message": "No stock"}, {}),
    ],
)
def test_conflicting_reservation_result_is_rejected(
    first: str, second: str, first_details: dict[str, str], second_details: dict[str, str]
) -> None:
    session_factory = build_session_factory()

    apply_reservation_result(session_factory, reservation_result(first, **first_details))  # type: ignore[arg-type]
    with pytest.raises(ReservationResultConflictError):
        apply_reservation_result(session_factory, reservation_result(second, **second_details))  # type: ignore[arg-type]


def test_unknown_order_is_not_found() -> None:
    session_factory = build_session_factory()
    request = ReservationResultRequest(
        order_id="unknown-order",
        reservation_result="succeeded",
        warehouse_event_id="warehouse-event-1",
    )

    with pytest.raises(OrderNotFoundError):
        apply_reservation_result(session_factory, request)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "payload",
    [
        {"order_id": "order-1", "reservation_result": "failed", "warehouse_event_id": "event-1"},
        {
            "order_id": "order-1",
            "reservation_result": "succeeded",
            "warehouse_event_id": "event-1",
            "reason_code": "OUT_OF_STOCK",
        },
    ],
)
def test_reservation_result_contract_rejects_invalid_failure_details(payload: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        ReservationResultRequest.model_validate(payload)
