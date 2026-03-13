import ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database.models import Base

def _build_url(raw: str) -> str:
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+asyncpg://", 1)
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw

def _make_engine(url: str):
    if url.startswith("sqlite"):
        return create_async_engine(url, echo=False)

    # Lokal PostgreSQL uchun SSL kerak emas
    is_local = "localhost" in url or "127.0.0.1" in url
    connect_args = {} if is_local else {"ssl": ssl.create_default_context()}

    return create_async_engine(
        url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        connect_args=connect_args,
    )

_engine           = None
AsyncSessionLocal = None

def init_engine():
    global _engine, AsyncSessionLocal
    from config import config
    url     = _build_url(config.DATABASE_URL)
    _engine = _make_engine(url)
    AsyncSessionLocal = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _engine

async def init_db():
    engine = _engine or init_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tayyor!")
