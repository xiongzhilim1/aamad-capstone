"""Alembic environment: migrations run against DATABASE_URL with the app's metadata."""

from alembic import context
from sqlalchemy import create_engine

from app.db.models import Base
from app.settings import get_settings

target_metadata = Base.metadata


def run() -> None:
    url = get_settings().database_url
    if context.is_offline_mode():
        context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run()
