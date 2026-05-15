# Contact Management API (GoIT Python Web HW-10)

A robust RESTful API built with **FastAPI** for managing contacts. The application supports user authentication (JWT), full CRUD operations for contacts, and automated database migrations using **Alembic** .

## 🚀 Features

- **User Authentication:** Secure registration and login using JWT tokens.
- **Contact Management:** Create, read, update, and delete contacts.
- **Search & Filters:** Search contacts by name, last name, or email.
- **Upcoming Birthdays:** Specialized endpoint to retrieve contacts with birthdays in the next 7 days.
- **Database Migrations:** Version control for your PostgreSQL schema via Alembic.
- **Dockerized Development:** Fully containerized environment with live-syncing for code changes.

## 🛠 Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL (v15)
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Containerization:** Docker & Docker Compose
- **Documentation:** Swagger UI (OpenAPI)

## 📦 Installation & Setup

### 1. Prerequisites

- Docker and Docker Compose installed.
- A `.env` file in the root directory (refer to `.env.example`).

### 2. Launch the Application

Run the following command to build and start the containers in the background:

**Bash**

```
docker-compose up -d
```

This starts two services:

- `postgres_db`: The database running on port `5432`.
- `fastapi_app`: The API running on port `8000`.

### 3. Database Migrations

To set up the database tables (`users`, `contacts`), apply the migrations inside the container:

**Bash**

```
docker-compose exec web alembic upgrade head
```

This will create the necessary relations in your `HW10` database.

## 📋 API Usage & Testing

### Interactive Documentation

Once the app is running, access the interactive Swagger UI to test the endpoints:

- **Swagger:** [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)

### Testing Flow

1. **Register:** Navigate to `POST /api/auth/register`. Click **Try it out** , enter an email and password, and click **Execute** .
2. **Login:** Go to `POST /api/auth/login`. Use the same credentials to receive an `access_token`.
3. **Authorize:** \* Copy the token value.
   - Click the **Authorize** button at the top of the page.
   - Paste the token and save.
4. **Contacts:** You can now manually add/update/delete contacts using API Docs and they will be saved to your PostgreSQL database.

## 📂 Project Structure

- `main.py`: Application entry point.
- `models.py`: SQLAlchemy database models.
- `schemas.py`: Pydantic models for data validation.
- `auth.py`: Authentication handlers.
- `alembic/`: Migration scripts and configuration.
- `docker-compose.yml`: Container orchestration with host-to-container volume syncing.
