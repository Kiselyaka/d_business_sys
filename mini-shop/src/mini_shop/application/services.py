import logging
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from mini_shop.application.contracts import (
    CreateOrderRequest,
    CreateOrderResponse,
    OrderCreatedEvent,
    OrderCreatedItem,
    OrderCreatedPayload,
    ReservationResultRequest,
    ReservationResultResponse,
)
from mini_shop.application.ports import IntegrationEventPublisher
from mini_shop.domain.models import Customer, Order, OrderItem, OrderStatus, Product, ReservationTransitionError

logger = logging.getLogger(__name__)


class ProductNotFoundError(ValueError):
    pass


class OrderNotFoundError(ValueError):
    pass


class ReservationResultConflictError(ValueError):
    pass


def create_order(
    session_factory: sessionmaker[Session], request: CreateOrderRequest, publisher: IntegrationEventPublisher
) -> CreateOrderResponse:
    """Persist the order first, then synchronously publish its external event."""
    with session_factory() as session:
        customer = session.scalar(select(Customer).where(Customer.customer_id == request.customer.customer_id))
        if customer is None:
            customer = Customer(id=str(uuid4()), **request.customer.model_dump())
            session.add(customer)
        else:
            customer.full_name = request.customer.full_name
            customer.email = request.customer.email
            customer.phone = request.customer.phone

        products_by_code = {
            product.product_code: product
            for product in session.scalars(select(Product).where(Product.product_code.in_([item.product_code for item in request.items])))
        }
        missing_codes = [item.product_code for item in request.items if item.product_code not in products_by_code]
        if missing_codes:
            raise ProductNotFoundError(f"Unknown product_code: {', '.join(missing_codes)}")

        order = Order(
            id=str(uuid4()),
            customer=customer,
            currency="EUR",
            total_amount=sum((products_by_code[item.product_code].price * item.quantity for item in request.items), Decimal("0")),
            status=OrderStatus.WAITING_FOR_RESERVATION.value,
            shipping_address=request.shipping_address.model_dump(mode="json"),
        )
        order.items = [
            OrderItem(
                id=str(uuid4()),
                product_code=item.product_code,
                name_snapshot=products_by_code[item.product_code].name,
                quantity=item.quantity,
                unit_price=products_by_code[item.product_code].price,
            )
            for item in request.items
        ]
        session.add(order)
        session.commit()
        session.refresh(order)

        event = OrderCreatedEvent(
            event_id=f"order-created-{order.id}",
            occurred_at=order.created_at,
            correlation_id=f"order-{order.id}",
            payload=OrderCreatedPayload(
                order_id=order.id,
                customer=request.customer,
                shipping_address=request.shipping_address,
                items=[
                    OrderCreatedItem(
                        product_code=item.product_code,
                        name=item.name_snapshot,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                    )
                    for item in order.items
                ],
                currency=order.currency,
                total_amount=order.total_amount,
            ),
        )

    logger.info("order_created", extra={"order_id": order.id})
    publisher.publish(event)
    logger.info("external_event_sent", extra={"event_id": event.event_id, "order_id": order.id})
    return CreateOrderResponse(order_id=order.id, status=order.status)


def apply_reservation_result(
    session_factory: sessionmaker[Session], request: ReservationResultRequest
) -> ReservationResultResponse:
    with session_factory() as session:
        order = session.get(Order, request.order_id)
        if order is None:
            raise OrderNotFoundError(f"Order not found: {request.order_id}")
        try:
            order.apply_reservation_result(request.reservation_result)
        except ReservationTransitionError as error:
            raise ReservationResultConflictError(str(error)) from error
        session.commit()
        session.refresh(order)
        response = ReservationResultResponse(order_id=order.id, status=order.status)

    logger.info(
        "reservation_result_applied",
        extra={"order_id": request.order_id, "warehouse_event_id": request.warehouse_event_id, "status": response.status},
    )
    return response
