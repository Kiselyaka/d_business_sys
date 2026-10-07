from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CustomerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    phone: str | None = None


class ShippingAddress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    country: str = Field(min_length=1)
    city: str = Field(min_length=1)
    postal_code: str = Field(min_length=1)
    street: str = Field(min_length=1)
    building: str = Field(min_length=1)
    apartment: str | None = None


class OrderItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_code: str = Field(min_length=1)
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer: CustomerInput
    shipping_address: ShippingAddress
    items: list[OrderItemInput] = Field(min_length=1)


class OrderCreatedItem(BaseModel):
    product_code: str
    name: str
    quantity: int
    unit_price: Decimal


class OrderCreatedPayload(BaseModel):
    customer: CustomerInput
    order_id: str
    shipping_address: ShippingAddress
    items: list[OrderCreatedItem]
    currency: str
    total_amount: Decimal


class OrderCreatedEvent(BaseModel):
    event_id: str
    event_type: str = "order.created"
    source_system: str = "mini-shop"
    occurred_at: datetime
    correlation_id: str
    schema_version: int = 1
    payload: OrderCreatedPayload


class CreateOrderResponse(BaseModel):
    order_id: str
    status: str
