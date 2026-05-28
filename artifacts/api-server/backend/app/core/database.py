from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings

_raw_url = settings.DATABASE_URL


def _build_asyncpg_url(raw: str) -> tuple[str, dict]:
    """Convert a postgres:// URL with psycopg2-style sslmode to asyncpg format."""
    if raw.startswith("postgresql://") or raw.startswith("postgres://"):
        scheme = "postgresql+asyncpg"
        rest = raw.split("://", 1)[1]
    elif raw.startswith("postgresql+asyncpg://"):
        scheme = "postgresql+asyncpg"
        rest = raw.split("://", 1)[1]
    else:
        return raw, {}

    parsed = urlparse(f"postgresql://{rest}")
    params = parse_qs(parsed.query, keep_blank_values=True)

    connect_args: dict = {}
    ssl_mode = params.pop("sslmode", [None])[0]
    if ssl_mode in ("require", "verify-ca", "verify-full"):
        import ssl as _ssl
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        connect_args["ssl"] = ctx
    elif ssl_mode in ("disable", "allow", "prefer"):
        connect_args["ssl"] = False

    new_query = urlencode({k: v[0] for k, v in params.items()})
    clean_parsed = parsed._replace(scheme=scheme, query=new_query)
    final_url = urlunparse(clean_parsed)
    return final_url, connect_args


DATABASE_URL, _connect_args = _build_asyncpg_url(_raw_url)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args=_connect_args,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
