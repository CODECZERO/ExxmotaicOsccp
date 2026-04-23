"""shared.db.client — SQLAlchemy engine and session factory."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "",  # empty = no DB configured
)


if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=3,
        pool_timeout=15,  # Wait up to 15s before failing if pool is busy
        echo=False,
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    logger.info("Database engine created for %s", DATABASE_URL.split("@")[-1])
else:
    engine = None
    SessionLocal = None
    logger.warning("DATABASE_URL not set — running without database persistence")



@contextmanager
def get_db() -> Generator[Session | None, None, None]:
    """Yield a SQLAlchemy session, or ``None`` if no DB is configured."""
    if SessionLocal is None:
        yield None
        return

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("DB session error — rolled back")
        raise
    finally:
        session.close()


def db_available() -> bool:
    """Return True if a database connection is configured."""
    return engine is not None
