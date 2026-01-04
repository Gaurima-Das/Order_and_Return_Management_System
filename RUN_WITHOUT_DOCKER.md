# Running Without Docker - Options Guide

This guide provides multiple options to run the Order Management System without Docker and Docker Compose.

## Option 1: Local PostgreSQL + Local Redis (Recommended for Development)

### Prerequisites
- PostgreSQL installed locally
- Redis installed locally

### Setup Steps

#### 1. Install PostgreSQL
**Windows:**
- Download from: https://www.postgresql.org/download/windows/
- Or use installer: https://www.postgresql.org/download/windows/installer/
- Default port: 5432
- Default user: postgres (set password during installation)

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### 2. Create Database
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE order_management;

# Exit
\q
```

#### 3. Install Redis
**Windows:**
- Download from: https://github.com/microsoftarchive/redis/releases
- Or use WSL: `wsl --install` then `sudo apt install redis-server`
- Or use Memurai (Redis for Windows): https://www.memurai.com/

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
```

#### 4. Update .env File
```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/order_management
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:your_password@localhost:5432/order_management
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### 5. Run Application
```bash
# Run migrations
alembic upgrade head

# Start FastAPI
uvicorn app.main:app --reload

# Start Celery (in another terminal)
celery -A app.celery_app worker --loglevel=info
```

---

## Option 2: SQLite + Database as Celery Broker (Simplest Setup)

This option requires **NO external services** - everything runs locally with SQLite.

### Setup Steps

#### 1. Update Configuration
We'll modify the database configuration to use SQLite and use the database as Celery broker.

#### 2. Update .env File
```env
# Use SQLite
DATABASE_URL=sqlite:///./order_management.db
DATABASE_URL_ASYNC=sqlite+aiosqlite:///./order_management.db

# Use database as Celery broker (no Redis needed)
CELERY_BROKER_URL=db+sqlite:///./celery_broker.db
CELERY_RESULT_BACKEND=db+sqlite:///./celery_broker.db
```

#### 3. Install Additional Dependency
```bash
pip install aiosqlite
```

#### 4. Update requirements.txt
Add `aiosqlite` to requirements.txt

#### 5. Note on Limitations
- SQLite doesn't support all PostgreSQL features (JSON columns work differently)
- Database as Celery broker is slower than Redis
- Not recommended for production
- Good for development and testing

---

## Option 3: Cloud Services (No Local Installation)

### PostgreSQL Options
1. **Supabase** (Free tier): https://supabase.com
2. **Neon** (Free tier): https://neon.tech
3. **ElephantSQL** (Free tier): https://www.elephantsql.com
4. **Railway** (Free tier): https://railway.app

### Redis Options
1. **Upstash Redis** (Free tier): https://upstash.com
2. **Redis Cloud** (Free tier): https://redis.com/try-free/
3. **Railway Redis** (Free tier): https://railway.app

### Setup Example (Supabase + Upstash)

#### 1. Create Supabase Project
- Go to https://supabase.com
- Create new project
- Get connection string from Settings → Database

#### 2. Create Upstash Redis
- Go to https://upstash.com
- Create Redis database
- Get connection URL

#### 3. Update .env File
```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres
REDIS_URL=redis://[UPSTASH_URL]:[PORT]
CELERY_BROKER_URL=redis://[UPSTASH_URL]:[PORT]
CELERY_RESULT_BACKEND=redis://[UPSTASH_URL]:[PORT]
```

---

## Option 4: PostgreSQL + SQLite for Celery (Hybrid)

Use PostgreSQL for main database but SQLite-based broker for Celery.

### Setup Steps

#### 1. Install PostgreSQL (see Option 1)

#### 2. Update .env File
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/order_management
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:password@localhost:5432/order_management

# Use database as broker (no Redis needed)
CELERY_BROKER_URL=db+sqlite:///./celery_broker.db
CELERY_RESULT_BACKEND=db+sqlite:///./celery_broker.db
```

#### 3. Install Dependency
```bash
pip install aiosqlite
```

---

## Option 5: Windows-Specific (WSL + Local Services)

If you're on Windows, you can use WSL (Windows Subsystem for Linux) to run PostgreSQL and Redis.

### Setup Steps

#### 1. Install WSL
```powershell
wsl --install
```

#### 2. Install PostgreSQL in WSL
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server
sudo service postgresql start
sudo service redis-server start
```

#### 3. Create Database
```bash
sudo -u postgres psql
CREATE DATABASE order_management;
\q
```

#### 4. Update .env File
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/order_management
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:postgres@localhost:5432/order_management
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## Quick Setup Scripts

### Windows PowerShell Script (Option 1 - Local PostgreSQL + Redis)

Create `setup-local.ps1`:
```powershell
# Check if PostgreSQL is installed
Write-Host "Checking PostgreSQL..."
# Add your PostgreSQL setup commands here

# Check if Redis is installed
Write-Host "Checking Redis..."
# Add your Redis setup commands here

# Create database
Write-Host "Creating database..."
# Add database creation commands

Write-Host "Setup complete! Update .env file with your credentials."
```

### Linux/macOS Script (Option 1)

Create `setup-local.sh`:
```bash
#!/bin/bash

# Install PostgreSQL (if not installed)
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL..."
    # Add installation commands for your OS
fi

# Install Redis (if not installed)
if ! command -v redis-server &> /dev/null; then
    echo "Installing Redis..."
    # Add installation commands for your OS
fi

# Create database
echo "Creating database..."
sudo -u postgres psql -c "CREATE DATABASE order_management;" || echo "Database might already exist"

echo "Setup complete! Update .env file with your credentials."
```

---

## Recommended Approach by Use Case

### Development/Testing
- **Best**: Option 2 (SQLite + Database broker) - Simplest, no setup
- **Alternative**: Option 1 (Local PostgreSQL + Redis) - More production-like

### Learning/Prototyping
- **Best**: Option 2 (SQLite + Database broker) - Zero configuration

### Production-like Development
- **Best**: Option 1 (Local PostgreSQL + Redis) - Matches production environment

### No Local Installation
- **Best**: Option 3 (Cloud services) - Use Supabase + Upstash

---

## Troubleshooting

### PostgreSQL Connection Issues
- Check if PostgreSQL is running: `pg_isready` or `sudo systemctl status postgresql`
- Verify credentials in .env file
- Check firewall settings
- Ensure PostgreSQL is listening on localhost:5432

### Redis Connection Issues
- Check if Redis is running: `redis-cli ping` (should return PONG)
- Verify Redis URL in .env file
- Check Redis is listening on localhost:6379

### SQLite Issues
- Ensure write permissions in project directory
- SQLite files will be created in project root
- For async SQLite, ensure `aiosqlite` is installed

---

## Next Steps

1. Choose an option that fits your needs
2. Follow the setup steps for that option
3. Update your `.env` file accordingly
4. Run migrations: `alembic upgrade head`
5. Start the application

For the **simplest setup** (no external services), see the SQLite configuration guide next.

