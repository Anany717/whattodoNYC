from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


engine = create_engine(settings.sqlalchemy_database_url, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


SQLITE_COMPATIBILITY_COLUMNS: dict[str, dict[str, str]] = {
    "places": {
        "image_url": "TEXT",
        "google_photo_reference": "TEXT",
        "photo_source": "TEXT",
        "image_last_synced_at": "DATETIME",
        "external_photo_metadata": "JSON",
    },
    "plan_items": {
        "step_type": "VARCHAR(8) NOT NULL DEFAULT 'custom'",
        "order_index": "INTEGER NOT NULL DEFAULT 0",
        "is_selected": "BOOLEAN NOT NULL DEFAULT 0",
        "updated_at": "DATETIME",
    },
}


def ensure_sqlite_compatibility_schema() -> None:
    if not settings.sqlalchemy_database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)

    with engine.begin() as connection:
        for table_name, columns in SQLITE_COMPATIBILITY_COLUMNS.items():
            if not inspector.has_table(table_name):
                continue

            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_sql in columns.items():
                if column_name in existing_columns:
                    continue
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))

        refreshed_inspector = inspect(connection)

        if refreshed_inspector.has_table("plan_items"):
            plan_item_columns = {column["name"] for column in refreshed_inspector.get_columns("plan_items")}
            if "updated_at" in plan_item_columns:
                connection.execute(
                    text(
                        "UPDATE plan_items SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)"
                    )
                )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
