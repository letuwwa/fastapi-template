# FastAPI Template

FastAPI starter project with PostgreSQL, SQLAlchemy, Alembic migrations, JWT
authentication, password hashing, refresh tokens, logout token revocation, CORS,
Docker, and role-based admin protection.

## Stack

- Python 3.14+
- FastAPI
- PostgreSQL 18
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

Copy the example configuration and replace the blank JWT secret:

```bash
cp .env.example .env
openssl rand -hex 32
```

The resulting `.env` should contain:

```env
APP_NAME=fastapi-template
ENVIRONMENT=development
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8000","http://127.0.0.1:3000","http://127.0.0.1:8000"]

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fastapi_template

JWT_SECRET_KEY=<paste-the-generated-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

`JWT_SECRET_KEY` is required for secure token signing. Use a long random value
for local development and a separate secret in every deployed environment.
Access-token lifetime must not exceed refresh-token lifetime.

## Database

### Native PostgreSQL

Create the configured local database if it does not exist:

```bash
createdb -h localhost -p 5432 -U postgres fastapi_template
```

Run migrations:

```bash
uv run alembic upgrade head
```

Create a migration after model changes:

```bash
uv run alembic revision --autogenerate -m "describe change"
```

### Docker PostgreSQL

To create only the project database on localhost, set `JWT_SECRET_KEY` in
`.env`, then run:

```bash
docker compose up -d postgres
```

The default host port is `5432`. If it is already occupied, choose another
localhost port without changing the container port:

```env
POSTGRES_PORT=5434
```

The backend always uses PostgreSQL's internal Compose port `5432`.

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

Compose reads `JWT_SECRET_KEY` from `.env` and refuses to start the backend when
it is missing, preventing accidental use of a public default signing key.

The backend waits for PostgreSQL to become healthy, runs Alembic migrations,
then starts FastAPI on `http://localhost:8000`.

Docker Compose starts a non-root `backend` service and a PostgreSQL 18 service.
Both published ports bind only to `127.0.0.1`. The backend connects through the
internal Compose hostname:

```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fastapi_template
```

PostgreSQL is exposed to localhost on `POSTGRES_PORT`, defaulting to `5432`.
The API is exposed on `BACKEND_PORT`, defaulting to `8000`.

Database data is stored in the container and is intended for disposable local
development. Running `docker compose down` and recreating the database container
resets that state.

Stop and remove the containers:

```bash
docker compose down
```

Check service health and logs:

```bash
docker compose ps
docker compose logs backend postgres
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

Rotate a session with a refresh token. The old access and refresh tokens are
revoked, and a new token pair is returned:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Authorization: Bearer <refresh-token>"
```

Logout by revoking the session associated with the presented access or refresh
token. Both tokens in the pair are invalidated:

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
POST /api/v1/auth/refresh           Rotate a refresh token and return a new token pair
POST /api/v1/auth/logout            Revoke the presented token's entire session
GET  /api/v1/auth/me                Return the current user
GET  /api/v1/auth/admin-only        Require an admin user
```

Newly registered users use the `regular` role. The base migration creates the
users and token blocklist tables; it does not seed an admin user.

## Registration Validation

```text
email       Max 255 characters
username    1-100 ASCII letters, digits, underscores, or hyphens
password    8-128 characters
first_name  1-30 non-whitespace characters
last_name   1-30 non-whitespace characters
```

Email addresses are validated and normalized to lowercase before storage and
login. Usernames cannot contain `@`, preventing ambiguous login identifiers.

## Quality

Run Ruff:

```bash
uv run ruff check .
uv run ruff format --check .
```

Run the test suite:

```bash
uv run pytest
```

Update and inspect dependencies:

```bash
uv lock --upgrade
uv tree --outdated --depth 1
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
docker/entrypoint.sh              Migrations and container process startup
tests/                             Authentication and settings regression tests
```
