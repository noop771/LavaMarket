# LavaMarket

Интернет-магазин пиццы, роллов и напитков. Бэкенд на FastAPI.

## Запуск окружения

### PostgreSQL (Docker)

```bash
docker run --name fastapi-postgres \
  -e POSTGRES_PASSWORD=<пароль> \
  -e POSTGRES_DB=LavaMarket \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  -d postgres:16

