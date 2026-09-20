from fastapi import FastAPI, Response, status
from sqlalchemy.engine import Engine

from crm.database import create_database_engine, database_is_ready
from crm.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine: Engine = create_database_engine(settings.database_url)
    app = FastAPI(title="CRM", version="0.1.0")

    @app.get("/health/live", tags=["health"])
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    def ready(response: Response) -> dict[str, str]:
        if database_is_ready(engine):
            return {"status": "ok", "database": "available"}
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "unavailable"}

    return app


app = create_app()

