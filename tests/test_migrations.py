from io import StringIO
from pathlib import Path

from alembic.config import Config

from alembic import command


def test_offline_migration_sql_contains_schema_and_reverse_operations() -> None:
    output = StringIO()
    config = Config(
        str(Path(__file__).resolve().parents[1] / "alembic.ini"), output_buffer=output
    )
    command.upgrade(config, "head", sql=True)
    upgrade_sql = output.getvalue()
    assert "CREATE TABLE users" in upgrade_sql
    assert "CREATE TABLE token_blocklist" in upgrade_sql
    assert "CREATE INDEX ix_token_blocklist_expires_at" in upgrade_sql
    assert "ck_users_username_no_at" in upgrade_sql
    assert "COMMIT;" in upgrade_sql

    output.seek(0)
    output.truncate()
    command.downgrade(config, "head:base", sql=True)
    downgrade_sql = output.getvalue()
    assert "DROP TABLE users" in downgrade_sql
    assert "DROP TABLE token_blocklist" in downgrade_sql
    assert "DROP TYPE user_role" in downgrade_sql
    assert "COMMIT;" in downgrade_sql
