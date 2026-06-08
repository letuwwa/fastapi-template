## Setup
Install dependencies:
```bash
uv sync
```

Create local env file:
```bash
cp .env.example .env
```

Generate a JWT secret and put it in `.env`:
```bash
openssl rand -hex 32
```

Required env values:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fastapi_template

JWT_SECRET_KEY=<long-random-secret>

JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Database
Create the database if needed:
```bash
createdb fastapi_template
```

Run migrations:
```bash
uv run alembic upgrade head
```

Create a migration after model changes:
```bash
uv run alembic revision --autogenerate -m "describe change"
```

## Run
```bash
uv run fastapi dev app/main.py
```

Login:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

Use token:
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <jwt-token>"
```

## Key Files
```text
app/main.py              FastAPI app
app/api/v1/auth.py       Auth routes
app/core/security.py     Password hashing and JWT logic
app/core/config.py       Env settings
app/db/models/user.py    User model and roles
alembic/versions/        DB migrations
```
