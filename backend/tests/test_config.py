from app.core.config import sqlalchemy_database_url


def test_postgres_scheme_uses_psycopg_driver():
    assert sqlalchemy_database_url("postgres://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )
    assert sqlalchemy_database_url("postgresql://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )


def test_existing_psycopg_and_non_postgres_urls_are_unchanged():
    psycopg_url = "postgresql+psycopg://user:pass@host/db"
    sqlite_url = "sqlite:///./test.db"

    assert sqlalchemy_database_url(psycopg_url) == psycopg_url
    assert sqlalchemy_database_url(sqlite_url) == sqlite_url
