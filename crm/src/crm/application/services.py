from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from crm.application.contracts import IntegrationOrderRequest, IntegrationOrderResponse
from crm.domain.models import Customer, Deal, DealPosition


def upsert_integration_order(
    session_factory: sessionmaker[Session], request: IntegrationOrderRequest
) -> IntegrationOrderResponse:
    """Upsert the CRM projection, keyed by external customer and order IDs."""
    with session_factory() as session:
        customer = session.scalar(
            select(Customer).where(Customer.external_customer_id == request.client.external_customer_id)
        )
        if customer is None:
            customer = Customer(id=str(uuid4()), **request.client.model_dump())
            session.add(customer)
        else:
            customer.name = request.client.name
            customer.email = request.client.email
            customer.phone = request.client.phone

        deal = session.scalar(select(Deal).where(Deal.external_order_id == request.external_order_id))
        if deal is None:
            deal = Deal(
                id=str(uuid4()),
                external_order_id=request.external_order_id,
                customer=customer,
                amount=request.deal.amount,
                currency=request.deal.currency,
            )
            session.add(deal)
        else:
            deal.customer = customer
            deal.amount = request.deal.amount
            deal.currency = request.deal.currency
            deal.positions.clear()
            # Flush deletes before inserting replacement rows with the same
            # natural product key; the database uniqueness constraint stays active.
            session.flush()

        deal.positions.extend(
            DealPosition(
                id=str(uuid4()),
                external_product_code=position.external_product_code,
                title=position.title,
                quantity=position.quantity,
                price=position.price,
            )
            for position in request.positions
        )
        session.commit()

    return IntegrationOrderResponse(external_order_id=request.external_order_id)
