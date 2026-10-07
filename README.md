# Demo Business Systems

## Mini Shop — Milestone 1

`POST /api/orders` persists an order and then synchronously publishes an `order.created` external event to the Integration Platform. The Mini Shop migration seeds `SKU-001` (`Example Product`, `10.50 EUR`) as reproducible demo data.

Known limitation: an order is committed before the HTTP publish attempt. If the Platform is unavailable, the API returns `502`, but the order remains in `shop_db`. A transactional Outbox is deliberately deferred to a later milestone.

Mini Shop and CRM are separate demo information systems. They share this Git repository for convenience only: they have independent application code, PostgreSQL databases, migrations, Docker images and external APIs.

Milestone 0 intentionally contains only startup and health checks. No business entities or integration calls are implemented yet.
