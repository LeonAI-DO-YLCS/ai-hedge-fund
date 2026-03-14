"""streamlined provider records and inventory

Revision ID: 7a9b3c1d2e4f
Revises: f3c2a1b4c5d6
Create Date: 2026-03-13 22:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a9b3c1d2e4f"
down_revision: Union[str, None] = "f3c2a1b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if "provider_records" not in existing_tables:
        op.create_table(
            "provider_records",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("provider_key", sa.String(length=100), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=False),
            sa.Column(
                "provider_kind",
                sa.String(length=50),
                nullable=False,
                server_default="builtin",
            ),
            sa.Column("builtin_provider_key", sa.String(length=100), nullable=True),
            sa.Column("connection_mode", sa.String(length=50), nullable=True),
            sa.Column("endpoint_url", sa.Text(), nullable=True),
            sa.Column("models_url", sa.Text(), nullable=True),
            sa.Column("auth_mode", sa.String(length=50), nullable=True),
            sa.Column("request_defaults", sa.JSON(), nullable=True),
            sa.Column("extra_headers", sa.JSON(), nullable=True),
            sa.Column(
                "is_enabled", sa.Boolean(), nullable=True, server_default=sa.text("1")
            ),
            sa.Column(
                "is_retired", sa.Boolean(), nullable=True, server_default=sa.text("0")
            ),
            sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "provider_key", name="uq_provider_records_provider_key"
            ),
        )
        op.create_index(
            "ix_provider_records_id", "provider_records", ["id"], unique=False
        )
        op.create_index(
            "ix_provider_records_provider_key",
            "provider_records",
            ["provider_key"],
            unique=False,
        )

    api_key_columns = {col["name"] for col in inspector.get_columns("api_keys")}
    if "provider_record_id" not in api_key_columns:
        op.add_column(
            "api_keys", sa.Column("provider_record_id", sa.Integer(), nullable=True)
        )
        op.create_index(
            "ix_api_keys_provider_record_id",
            "api_keys",
            ["provider_record_id"],
            unique=False,
        )

    custom_model_columns = {
        col["name"] for col in inspector.get_columns("custom_models")
    }
    for column_name, column in [
        (
            "provider_record_id",
            sa.Column("provider_record_id", sa.Integer(), nullable=True),
        ),
        (
            "source",
            sa.Column(
                "source", sa.String(length=50), nullable=True, server_default="manual"
            ),
        ),
        (
            "is_enabled",
            sa.Column(
                "is_enabled", sa.Boolean(), nullable=True, server_default=sa.text("0")
            ),
        ),
        (
            "availability_status",
            sa.Column(
                "availability_status",
                sa.String(length=20),
                nullable=True,
                server_default="available",
            ),
        ),
        ("status_reason", sa.Column("status_reason", sa.Text(), nullable=True)),
        ("metadata_json", sa.Column("metadata_json", sa.JSON(), nullable=True)),
        (
            "last_seen_at",
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        ),
    ]:
        if column_name not in custom_model_columns:
            op.add_column("custom_models", column)

    custom_model_indexes = {
        index["name"] for index in inspector.get_indexes("custom_models")
    }
    if "ix_custom_models_provider_record_id" not in custom_model_indexes:
        op.create_index(
            "ix_custom_models_provider_record_id",
            "custom_models",
            ["provider_record_id"],
            unique=False,
        )
    if "ix_custom_models_availability_status" not in custom_model_indexes:
        op.create_index(
            "ix_custom_models_availability_status",
            "custom_models",
            ["availability_status"],
            unique=False,
        )
    if "uq_custom_models_provider_record_model" not in custom_model_indexes:
        op.create_index(
            "uq_custom_models_provider_record_model",
            "custom_models",
            ["provider_record_id", "model_name"],
            unique=True,
        )

    op.execute(
        sa.text(
            """
            INSERT INTO provider_records (provider_key, display_name, provider_kind, builtin_provider_key, connection_mode, is_enabled, is_retired)
            VALUES
                ('openai', 'OpenAI', 'builtin', 'openai', 'openai_compatible', 1, 0),
                ('anthropic', 'Anthropic', 'builtin', 'anthropic', 'anthropic_compatible', 1, 0),
                ('deepseek', 'DeepSeek', 'builtin', 'deepseek', 'openai_compatible', 1, 0),
                ('google', 'Google', 'builtin', 'google', 'direct_http', 1, 0),
                ('groq', 'Groq', 'builtin', 'groq', 'openai_compatible', 1, 0),
                ('openrouter', 'OpenRouter', 'builtin', 'openrouter', 'openai_compatible', 1, 0),
                ('xai', 'xAI', 'builtin', 'xai', 'openai_compatible', 1, 0),
                ('azure_openai', 'Azure OpenAI', 'builtin', 'azure_openai', 'openai_compatible', 1, 0),
                ('ollama', 'Ollama', 'local', 'ollama', 'local_probe', 1, 0),
                ('lmstudio', 'LMStudio', 'local', 'lmstudio', 'local_probe', 1, 0)
            ON CONFLICT(provider_key) DO NOTHING
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE api_keys
            SET provider_record_id = (
                CASE provider
                    WHEN 'OPENAI_API_KEY' THEN (SELECT id FROM provider_records WHERE provider_key = 'openai')
                    WHEN 'ANTHROPIC_API_KEY' THEN (SELECT id FROM provider_records WHERE provider_key = 'anthropic')
                    WHEN 'DEEPSEEK_API_KEY' THEN (SELECT id FROM provider_records WHERE provider_key = 'deepseek')
                    WHEN 'GOOGLE_API_KEY' THEN (SELECT id FROM provider_records WHERE provider_key = 'google')
                    WHEN 'GROQ_API_KEY' THEN (SELECT id FROM provider_records WHERE provider_key = 'groq')
                    WHEN 'OPENROUTER_API_KEY' THEN (SELECT id FROM provider_records WHERE provider_key = 'openrouter')
                    WHEN 'XAI_API_KEY' THEN (SELECT id FROM provider_records WHERE provider_key = 'xai')
                    WHEN 'AZURE_OPENAI_API_KEY' THEN (SELECT id FROM provider_records WHERE provider_key = 'azure_openai')
                    ELSE provider_record_id
                END
            )
            WHERE provider_record_id IS NULL
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE custom_models
            SET
                provider_record_id = CASE provider
                    WHEN 'OpenAI' THEN (SELECT id FROM provider_records WHERE provider_key = 'openai')
                    WHEN 'Anthropic' THEN (SELECT id FROM provider_records WHERE provider_key = 'anthropic')
                    WHEN 'DeepSeek' THEN (SELECT id FROM provider_records WHERE provider_key = 'deepseek')
                    WHEN 'Google' THEN (SELECT id FROM provider_records WHERE provider_key = 'google')
                    WHEN 'Groq' THEN (SELECT id FROM provider_records WHERE provider_key = 'groq')
                    WHEN 'OpenRouter' THEN (SELECT id FROM provider_records WHERE provider_key = 'openrouter')
                    WHEN 'xAI' THEN (SELECT id FROM provider_records WHERE provider_key = 'xai')
                    WHEN 'Azure OpenAI' THEN (SELECT id FROM provider_records WHERE provider_key = 'azure_openai')
                    WHEN 'Ollama' THEN (SELECT id FROM provider_records WHERE provider_key = 'ollama')
                    WHEN 'LMStudio' THEN (SELECT id FROM provider_records WHERE provider_key = 'lmstudio')
                    ELSE provider_record_id
                END,
                source = COALESCE(source, 'manual'),
                is_enabled = COALESCE(is_enabled, 0),
                availability_status = CASE
                    WHEN provider = 'GigaChat' THEN 'retired'
                    ELSE COALESCE(availability_status, 'available')
                END,
                status_reason = CASE
                    WHEN provider = 'GigaChat' THEN 'Legacy GigaChat reference retained for cleanup visibility.'
                    ELSE status_reason
                END
            WHERE provider_record_id IS NULL OR availability_status IS NULL
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    custom_model_columns = {
        col["name"] for col in inspector.get_columns("custom_models")
    }
    custom_model_indexes = {
        index["name"] for index in inspector.get_indexes("custom_models")
    }
    for index_name in [
        "uq_custom_models_provider_record_model",
        "ix_custom_models_availability_status",
        "ix_custom_models_provider_record_id",
    ]:
        if index_name in custom_model_indexes:
            op.drop_index(index_name, table_name="custom_models")
    for column_name in [
        "last_seen_at",
        "metadata_json",
        "status_reason",
        "availability_status",
        "is_enabled",
        "source",
        "provider_record_id",
    ]:
        if column_name in custom_model_columns:
            op.drop_column("custom_models", column_name)

    api_key_columns = {col["name"] for col in inspector.get_columns("api_keys")}
    if "provider_record_id" in api_key_columns:
        op.drop_index("ix_api_keys_provider_record_id", table_name="api_keys")
        op.drop_column("api_keys", "provider_record_id")

    existing_tables = set(inspector.get_table_names())
    if "provider_records" in existing_tables:
        op.drop_index("ix_provider_records_provider_key", table_name="provider_records")
        op.drop_index("ix_provider_records_id", table_name="provider_records")
        op.drop_table("provider_records")
