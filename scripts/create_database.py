"""Create SQLite tables declared in src.database.models."""

from src.database.connection import Base, engine
from src.database import models  # noqa: F401


def main() -> None:
    """Create all tables if they do not already exist."""

    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    main()
