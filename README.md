# FastAPI Template

FastAPI starter project with PostgreSQL, SQLAlchemy, Alembic migrations, JWT
authentication, password hashing, refresh tokens, logout token revocation, CORS,
Docker, and role-based admin protection.

## Stack

- Python 3.14+
- FastAPI
- PostgreSQL 17
- SQLAlchemy 2
- Alembic
- Pydantic Settings
- PyJWT
- pwdlib with Argon2
- uv
- Ruff

## Requirements

- Python 3.14+
- uv
- PostgreSQL for local development, or Docker Compose for the full stack

## Local Setup

Install dependencies:

```bash
uv sync
```

Create a `.env` file:

```env
APP_NAME=fastapi-template
ENVIRONMENT=development
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8000","http://127.0.0.1:3000","http://127.0.0.1:8000"]

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fastapi_template

JWT_SECRET_KEY=<long-random-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

Generate suitable local secrets:

```bash
openssl rand -hex 32
```

`JWT_SECRET_KEY` is required for secure token signing. Use a long random value
for local development and production.

## Database

Create the local database if it does not exist:

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

## Run Locally

Start the development server:

```bash
uv run fastapi dev app/main.py
```

The API runs at `http://localhost:8000`. Interactive docs are available at
`http://localhost:8000/docs`.

Check the health endpoint:

```bash
curl http://localhost:8000/
```

## Docker

Build and run the API with PostgreSQL:

```bash
docker compose up --build
```

The backend waits for PostgreSQL to become healthy, runs Alembic migrations,
then starts FastAPI on `http://localhost:8000`.

Docker Compose starts a `backend` service and a `postgres` service. The backend
connects to PostgreSQL through the internal Compose hostname:

```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fastapi_template
```

PostgreSQL is exposed to the host on `POSTGRES_PORT`, defaulting to `5432`.

Database data is not mounted to a named volume, so recreating the PostgreSQL
container resets local Docker database state.

Stop and remove the containers:

```bash
docker compose down
```

## Authentication

Register a user:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "exampleuser",
    "first_name": "Example",
    "last_name": "User",
    "password": "password123456"
  }'
```

Login with an email or username:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123456"
```

Use the OAuth2-compatible token endpoint from Swagger UI:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123456"
```

Call an authenticated endpoint:

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access-token>"
```

Refresh an access token with a refresh token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Authorization: Bearer <refresh-token>"
```

Logout by revoking the presented access or refresh token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access-or-refresh-token>"
```

## API Routes

```text
GET  /                              Health-style root response
POST /api/v1/auth/register          Create a regular user and return token pair
POST /api/v1/auth/login             Return the user and token pair
POST /api/v1/auth/token             Return an OAuth2-compatible token pair
POST /api/v1/auth/refresh           Return a new access token from a refresh token
POST /api/v1/auth/logout            Revoke the presented access or refresh token
GET  /api/v1/auth/me                Return the current user
GET  /api/v1/auth/admin-only        Require an admin user
```

Newly registered users use the `regular` role. The base migration creates the
users and token blocklist tables; it does not seed an admin user.

## Registration Validation

```text
email       Max 255 characters
username    Max 100 characters
password    8-128 characters
first_name  Max 30 characters
last_name   Max 30 characters
```

## Quality

Run Ruff:

```bash
uv run ruff check .
```

## Project Layout

```text
app/main.py                       FastAPI application and middleware
app/api/router.py                 API router registration
app/api/v1/auth.py                Auth routes
app/api/v1/schemas/               Request and response schemas
app/core/security.py              Password hashing and JWT logic
app/core/settings.py              Environment settings
app/db/deps.py                    Database session dependency
app/db/models/base_model.py       Shared model fields
app/db/models/user.py             User model and roles
app/db/models/token_blocklist.py  Revoked token model
alembic/versions/                 Alembic migrations
docker-compose.yml                Backend and PostgreSQL services
Dockerfile                        Backend image
```
