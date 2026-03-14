"""add provider management tables

Revision ID: f3c2a1b4c5d6
Revises: d5e78f9a1b2c
Create Date: 2026-03-13 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3c2a1b4c5d6"
down_revision: Union[str, None] = "d5e78f9a1b2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {col["name"] for col in inspector.get_columns("api_keys")}

    if "validation_status" not in existing_columns:
        op.add_column(
            "api_keys",
            sa.Column(
                "validation_status",
                sa.String(length=20),
                nullable=True,
                server_default="valid",
            ),
        )
    if "validation_error" not in existing_columns:
        op.add_column(
            "api_keys", sa.Column("validation_error", sa.Text(), nullable=True)
        )
    if "last_validated_at" not in existing_columns:
        op.add_column(
            "api_keys",
            sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "last_validation_latency_ms" not in existing_columns:
        op.add_column(
            "api_keys",
            sa.Column("last_validation_latency_ms", sa.Integer(), nullable=True),
        )

    existing_tables = set(inspector.get_table_names())
    if "custom_models" not in existing_tables:
        op.create_table(
            "custom_models",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("provider", sa.String(length=100), nullable=False),
            sa.Column("model_name", sa.String(length=255), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=False),
            sa.Column(
                "validation_status",
                sa.String(length=20),
                nullable=True,
                server_default="valid",
            ),
            sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "provider", "model_name", name="uq_custom_models_provider_model"
            ),
        )
        op.create_index("ix_custom_models_id", "custom_models", ["id"], unique=False)
        op.create_index(
            "ix_custom_models_provider", "custom_models", ["provider"], unique=False
        )

    if "agent_configurations" not in existing_tables:
        op.create_table(
            "agent_configurations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("agent_key", sa.String(length=100), nullable=False),
            sa.Column("model_name", sa.String(length=255), nullable=True),
            sa.Column("model_provider", sa.String(length=100), nullable=True),
            sa.Column("fallback_model_name", sa.String(length=255), nullable=True),
            sa.Column("fallback_model_provider", sa.String(length=100), nullable=True),
            sa.Column("system_prompt_override", sa.Text(), nullable=True),
            sa.Column("system_prompt_append", sa.Text(), nullable=True),
            sa.Column("temperature", sa.Float(), nullable=True),
            sa.Column("max_tokens", sa.Integer(), nullable=True),
            sa.Column("top_p", sa.Float(), nullable=True),
            sa.Column(
                "is_active", sa.Boolean(), nullable=True, server_default=sa.text("1")
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("agent_key"),
        )
        op.create_index(
            "ix_agent_configurations_id", "agent_configurations", ["id"], unique=False
        )
        op.create_index(
            "ix_agent_configurations_agent_key",
            "agent_configurations",
            ["agent_key"],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if "agent_configurations" in existing_tables:
        op.drop_index(
            "ix_agent_configurations_agent_key", table_name="agent_configurations"
        )
        op.drop_index("ix_agent_configurations_id", table_name="agent_configurations")
        op.drop_table("agent_configurations")

    if "custom_models" in existing_tables:
        op.drop_index("ix_custom_models_provider", table_name="custom_models")
        op.drop_index("ix_custom_models_id", table_name="custom_models")
        op.drop_table("custom_models")

    existing_columns = {col["name"] for col in inspector.get_columns("api_keys")}
    if "last_validation_latency_ms" in existing_columns:
        op.drop_column("api_keys", "last_validation_latency_ms")
    if "last_validated_at" in existing_columns:
        op.drop_column("api_keys", "last_validated_at")
    if "validation_error" in existing_columns:
        op.drop_column("api_keys", "validation_error")
    if "validation_status" in existing_columns:
        op.drop_column("api_keys", "validation_status")
