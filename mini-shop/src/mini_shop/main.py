from fastapi import FastAPI, HTTPException, Response, status
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from mini_shop.application.contracts import (
    CreateOrderRequest,
    CreateOrderResponse,
    ReservationResultRequest,
    ReservationResultResponse,
)
from mini_shop.application.ports import EventPublicationError, IntegrationEventPublisher
from mini_shop.application.services import (
    OrderNotFoundError,
    ProductNotFoundError,
    ReservationResultConflictError,
    apply_reservation_result,
    create_order,
)
from mini_shop.database import create_database_engine, create_session_factory, database_is_ready
from mini_shop.infrastructure.http_publisher import HttpIntegrationEventPublisher
from mini_shop.settings import Settings


def create_app(
    settings: Settings | None = None,
    publisher: IntegrationEventPublisher | None = None,
    session_factory: sessionmaker[Session] | None = None,
) -> FastAPI:
    settings = settings or Settings()
    engine: Engine = create_database_engine(settings.database_url)
    session_factory = session_factory or create_session_factory(engine)
    publisher = publisher or HttpIntegrationEventPublisher(
        settings.integration_platform_url, settings.integration_publish_timeout_seconds
    )
    app = FastAPI(title="Mini Shop", version="0.1.0")

    @app.get("/health/live", tags=["health"])
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    def ready(response: Response) -> dict[str, str]:
        if database_is_ready(engine):
            return {"status": "ok", "database": "available"}
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "unavailable"}

    @app.post("/api/orders", response_model=CreateOrderResponse, status_code=status.HTTP_201_CREATED, tags=["orders"])
    def post_order(request: CreateOrderRequest) -> CreateOrderResponse:
        try:
            return create_order(session_factory, request, publisher)
        except ProductNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
        except EventPublicationError as error:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    @app.post(
        "/api/integration/reservation-results",
        response_model=ReservationResultResponse,
        status_code=status.HTTP_200_OK,
        tags=["integration"],
    )
    def post_reservation_result(request: ReservationResultRequest) -> ReservationResultResponse:
        try:
            return apply_reservation_result(session_factory, request)
        except OrderNotFoundError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
        except ReservationResultConflictError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    return app


app = create_app()
