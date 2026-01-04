# Order & Return Management System

A reliable order and return management system built with FastAPI, featuring complex order state management, multi-step returns workflow, and asynchronous background jobs.

## Features

- ✅ Complex Order State Management with state machine
- ✅ Multi-Step Returns Workflow
- ✅ Asynchronous Background Jobs (Celery)
- ✅ RESTful API with FastAPI
- ✅ PostgreSQL database with SQLAlchemy
- ✅ Redis for caching and job queue

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **State Machine**: Transitions
- **Background Jobs**: Celery + Redis
- **Cache**: Redis

## Prerequisites

- Python 3.11+
- **Option 1 (Docker)**: Docker & Docker Compose
- **Option 2 (No Docker)**: See [RUN_WITHOUT_DOCKER.md](RUN_WITHOUT_DOCKER.md) for alternatives:
  - SQLite (no installation needed) ⭐ Easiest
  - Local PostgreSQL + Redis
  - Cloud services (Supabase, Upstash, etc.)

## Quick Start

### 🐳 With Docker (Recommended for Production-like Setup)

See below for Docker setup.

### 🚀 Without Docker (Easier Setup)

**Fastest option - SQLite (no installation needed):**
- See [QUICK_START_NO_DOCKER.md](QUICK_START_NO_DOCKER.md) for quick setup
- Or run: `setup-sqlite.bat` (Windows) / `./setup-sqlite.sh` (Linux/macOS)

**For all no-Docker options, see:**
- [QUICK_START_NO_DOCKER.md](QUICK_START_NO_DOCKER.md) - Quick reference
- [SETUP_SQLITE.md](SETUP_SQLITE.md) - SQLite setup (easiest)
- [RUN_WITHOUT_DOCKER.md](RUN_WITHOUT_DOCKER.md) - All options detailed

---

### 1. Clone and Setup (Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Services with Docker

```bash
docker-compose up -d
```

This will start PostgreSQL and Redis containers.

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Start the Application

```bash
# Start FastAPI server
uvicorn app.main:app --reload --port 8000

# In another terminal, start Celery worker
celery -A app.celery_app worker --loglevel=info

# Optional: Start Celery beat for scheduled tasks
celery -A app.celery_app beat --loglevel=info
```

### 6. Access the Application

- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## Project Structure

```
order_management_app/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database connection
│   ├── celery_app.py           # Celery configuration
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── order.py
│   │   ├── return.py
│   │   └── payment.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── order.py
│   │   ├── return.py
│   │   └── payment.py
│   ├── state_machines/         # State machine definitions
│   │   ├── __init__.py
│   │   ├── order_state.py
│   │   └── return_state.py
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── orders.py
│   │   │   ├── returns.py
│   │   │   └── payments.py
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── order_service.py
│   │   ├── return_service.py
│   │   └── payment_service.py
│   └── tasks/                  # Celery background tasks
│       ├── __init__.py
│       ├── order_tasks.py
│       ├── return_tasks.py
│       └── notification_tasks.py
├── alembic/                    # Database migrations
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Orders
- `POST /api/v1/orders` - Create new order
- `GET /api/v1/orders` - List orders
- `GET /api/v1/orders/{order_id}` - Get order details
- `PATCH /api/v1/orders/{order_id}/state` - Update order state
- `POST /api/v1/orders/{order_id}/cancel` - Cancel order

### Returns
- `POST /api/v1/returns` - Initiate return
- `GET /api/v1/returns` - List returns
- `GET /api/v1/returns/{return_id}` - Get return details
- `PATCH /api/v1/returns/{return_id}/state` - Update return state

### Payments
- `POST /api/v1/payments` - Process payment
- `GET /api/v1/payments/{payment_id}` - Get payment details
- `POST /api/v1/payments/{payment_id}/refund` - Process refund

## State Machine

### Order States
- `pending` → `confirmed` → `processing` → `shipped` → `delivered`
- Can transition to `cancelled` from most states
- Can transition to `returned` from `delivered`

### Return States
- `initiated` → `approved` → `pickup_scheduled` → `in_transit` → `received` → `processed` → `refunded`
- Can transition to `rejected` from `initiated` or `approved`

## Development

```bash
# Run tests
pytest

# Format code
black app/

# Lint code
flake8 app/
```

## License

MIT

