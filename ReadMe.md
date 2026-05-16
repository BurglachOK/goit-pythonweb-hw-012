# Premium Contacts API

A professional REST API built with **FastAPI** for managing personal and corporate contacts. This system features a robust JSON Web Token (JWT) authentication workflow, Role-Based Access Control (RBAC), database query optimization using Redis caching, automated codebase documentation via Sphinx, and 90% test coverage with Pytest.

---

## 🚀 Core Features

- **Contact Management (CRUD):** Secure creation, retrieval, updates, and deletion of contact data, equipped with built-in pagination, full-text searching, and field filtering.
- **Birthday Notifications:** Quickly extract a clean, filtered matrix of contacts celebrating birthdays within the upcoming 7 days.
- **Secure JWT Authentication:** Token-based user authentication workflow ensuring stateless session security
- **Redis Caching Strategy:** Low-latency auth performance—the active user profile is cached in-memory directly within the authentication middleware dependency, drastically lowering persistent PostgreSQL query loads.
- **Role-Based Access Control (RBAC):** Strict operational permissions separating `user` and `admin` scopes. Advanced features like updating default avatars using Cloudinary storage are exclusively restricted to administrators.
- **Password Reset Workflow:** Safe recovery system utilizing short-lived, single-action JWT verification tokens dispatched asynchronously via secure email.
- **Email Verification:** Mandated onboarding flow using `fastapi-mail` to verify target email addresses prior to unlocking active API endpoints.

---

## 🛠 Tech Stack

- **Framework:** FastAPI (Python 3.12)
- **Database:** PostgreSQL
- **Caching Layer:** Redis
- **ORM:** SQLAlchemy (2.0-style architecture)
- **Testing Suite:** Pytest, Pytest-Cov (Coverage reporting)
- **API Documentation:** Interactive Swagger UI / ReDoc, alongside Sphinx (HTML documentation compiled from source Docstrings)
- **Containerization:** Docker & Docker Compose
- **Cloud Infrastructure:** Cloudinary API (External secure media storage)

---

## ⚙️ Environment Configuration (`.env`)

Create a `.env` file within your project's root directory and populate it with your specific operational keys:

```
# Database Configuration
DATABASE_URL=postgresql://postgres:secret_password@db:5432/contacts_db

# Security
SECRET_KEY=your_super_secret_jwt_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin Registration Token
ADMIN_REGISTRATION_TOKEN=your_secure_admin_token_here

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Mail Server Configuration
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_app_password
MAIL_FROM=your_email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.example.com

# Cloudinary Configuration
CLOUDINARY_NAME=your_cloudinary_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
```

---

## 🐳 Deployment with Docker Compose

Spin up the entire application stack (FastAPI server + PostgreSQL cluster + Redis instance) using a single command block:

`docker compose up -d --build`

Once up and running, you can interact with the live services at these addresses:

- **Interactive Swagger UI:** [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)

---

## 🔒 Registration Mechanics & RBAC Enforcement

To provide a consistent user experience matching standard login actions, the registration gateway processes inputs via standardized web forms:

1. **Data Format:** The `POST /auth/register` endpoint processes incoming inputs structured as **URL-encoded Form Data** (`application/x-www-form-urlencoded`). This exposes intuitive, explicit input fields directly within the Swagger UI dashboard.
2. **Standard User Onboarding:** To register a typical consumer profile, simply leave the `admin_token` form field blank or keep its default `"string"` placeholder value. The registration engine parses this as an empty input parameter and safely instantiates the new account with a default `role: "user"`.
3. **Elevated Administrator Sign-up:** To provision an authorized administrative operator, pass your secret token string directly into the `admin_token` parameter input. If it evaluates against the `ADMIN_REGISTRATION_TOKEN` environment variable, the profile is built with an elevated `role: "admin"`.
4. **RBAC Boundary Enforcement:** The media asset pipeline (`PATCH /users/avatar`) is tightly guarded by a custom dependency class constructor: `RoleChecker(["admin"])`. Standard users attempting access are blocked immediately at the gateway layer, returning a `403 Forbidden` response.

---

## 🧪 Testing Suite & Coverage Optimization

This codebase is thoroughly evaluated via comprehensive unit and integration tests driven by the `pytest` runner. The testing scope remains completely sandboxed from your live persistent infrastructure through automated SQLAlchemy SQLite test sessions (`test.db`) and robust Redis layer mocking utilizing `unittest.mock.MagicMock`.

To flush previous telemetry data and execute the test pipeline alongside automated coverage analysis within the active application container, run:

```
# Clear legacy environment coverage tracks
rm -f .coverage .coverage.*

# Execute pytest alongside real-time statement coverage tracing
docker compose exec web pytest --cov=. --cov-report=term-missing
```

### Current Test Verification Output:

- **Pipeline Status:** 25 Passed / 25 Total Tests (100% Success Rate)
- **Global Code Metrics:** **90% Total Coverage**

---

## 📚 Generating Sphinx Documentation

The technical metadata describing internal modules, classes, arguments, and helper methods (documented under the strict Google Python Style Guide standard) can be automatically compiled into searchable, standalone HTML web assets using Sphinx and the clean `sphinx_rtd_theme` layout wrapper.

Compile the documentation source files inside the runtime docker environment by executing:

**Bash**

```
docker compose exec web sphinx-build -b html docs docs/_build/html
```

After compilation is complete, load the generated entry point file inside any local web browser to inspect your documentation site:
`docs/_build/html/index.html`
