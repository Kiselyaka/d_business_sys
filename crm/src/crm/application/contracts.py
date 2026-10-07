from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ClientContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_customer_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    phone: str | None = None


class DealContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Decimal
    currency: str = Field(min_length=3, max_length=3)


class DeliveryAddressContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    country: str = Field(min_length=1)
    city: str = Field(min_length=1)
    postal_code: str = Field(min_length=1)
    street: str = Field(min_length=1)
    building: str = Field(min_length=1)
    apartment: str | None = None


class PositionContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_product_code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    price: Decimal


class IntegrationOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_order_id: str = Field(min_length=1)
    client: ClientContract
    deal: DealContract
    delivery_address: DeliveryAddressContract
    positions: list[PositionContract] = Field(min_length=1)


class IntegrationOrderResponse(BaseModel):
    status: str = "accepted"
    external_order_id: str
