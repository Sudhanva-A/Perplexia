from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings
import ssl
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()           # For common tables (Supabase)
NeonBase = declarative_base()       # For Neon-specific tables

# Remove sslmode from the URL string
DATABASE_URL = f"postgresql+asyncpg://{settings.SUPABASE_DB_USER}:{settings.SUPABASE_DB_PASSWORD}@{settings.SUPABASE_DB_HOST}:{settings.SUPABASE_DB_PORT}/{settings.SUPABASE_DB_DBNAME}"

NEON_DATABASE_URL = f"postgresql+asyncpg://{settings.NEOND_DB_USER}:{settings.NEOND_DB_PASSWORD}@{settings.NEOND_DB_HOST}/{settings.NEOND_DB_NAME}"

# Create SSL context for secure connections
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Pass SSL configuration as connect_args
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"ssl": ssl_context}
)

# Fix: Add SSL for NeonDB connection as well
neon_engine = create_async_engine(
    NEON_DATABASE_URL,
    connect_args={"ssl": ssl_context},
    # Add connection pooling settings
    pool_pre_ping=True,        # Verify connections before using them
    pool_recycle=300,          # Recycle connections after 5 minutes
    pool_size=5,               # Keep a smaller pool size
    max_overflow=10,           # Allow up to 10 extra connections
    pool_timeout=30            # Wait up to 30 seconds for a connection
)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

NeonAsyncSessionLocal = sessionmaker(
    bind=neon_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()

async def get_neon_db():
    db = NeonAsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()  