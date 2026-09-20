FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/app/src
EXPOSE 8002
CMD ["sh", "-c", "alembic upgrade head && uvicorn mini_shop.main:app --host 0.0.0.0 --port 8002"]

