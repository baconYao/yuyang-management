import asyncio
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.config import db_settings

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"
MIGRATIONS_DIR = BACKEND_ROOT / "migrations"
MAX_RETRIES = 30
RETRY_DELAY_SECONDS = 2


def _run_alembic_upgrade() -> None:
    if not ALEMBIC_INI.is_file():
        raise FileNotFoundError(f"Alembic config not found: {ALEMBIC_INI}")
    if not MIGRATIONS_DIR.is_dir():
        raise FileNotFoundError(f"Migrations directory not found: {MIGRATIONS_DIR}")

    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", db_settings.POSTGRES_URL)
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    command.upgrade(cfg, "head")


async def run_migrations() -> None:
    """Run Alembic migrations, retrying until PostgreSQL is reachable."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await asyncio.to_thread(_run_alembic_upgrade)
            logger.info("Database migrations completed successfully")
            return
        except Exception as exc:
            if attempt == MAX_RETRIES:
                logger.exception(
                    "Database migration failed after %d attempts", MAX_RETRIES
                )
                raise
            logger.warning(
                "Migration attempt %d/%d failed: %s",
                attempt,
                MAX_RETRIES,
                exc,
                exc_info=True,
            )
            await asyncio.sleep(RETRY_DELAY_SECONDS)
