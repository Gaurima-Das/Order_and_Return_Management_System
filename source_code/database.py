from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings

# Determine if using SQLite
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Synchronous database (for migrations, etc.)
# SQLite needs different pool settings
if is_sqlite:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite-specific
        pool_pre_ping=True,
    )
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Asynchronous database (for FastAPI) - lazy initialization
_async_engine = None
_AsyncSessionLocal = None

def get_async_engine():
    """Get or create async engine (lazy initialization)."""
    global _async_engine
    if _async_engine is None:
        # SQLite needs different configuration
        if is_sqlite:
            _async_engine = create_async_engine(
                settings.DATABASE_URL_ASYNC,
                connect_args={"check_same_thread": False},
                pool_pre_ping=True,
                echo=settings.DEBUG,
            )
        else:
            _async_engine = create_async_engine(
                settings.DATABASE_URL_ASYNC,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=settings.DEBUG,
            )
    return _async_engine

def get_async_session_local():
    """Get or create async session local (lazy initialization)."""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _AsyncSessionLocal

Base = declarative_base()


# Dependency for FastAPI
async def get_db():
    """Dependency to get database session."""
    async_session = get_async_session_local()
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

