"""add manifest and journal tables

Revision ID: 8b2c4a6d5f1e
Revises: 7a9b3c1d2e4f
Create Date: 2026-03-14 11:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b2c4a6d5f1e"
down_revision: Union[str, None] = "7a9b3c1d2e4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    # 1. Create canonical_manifests table
    if "canonical_manifests" not in existing_tables:
        op.create_table(
            "canonical_manifests",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("flow_id", sa.Integer(), nullable=True),
            sa.Column("manifest_version", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("is_template", sa.Boolean(), nullable=True, server_default=sa.text("0")),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["flow_id"], ["hedge_fund_flows.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_canonical_manifests_id", "canonical_manifests", ["id"], unique=False)
        op.create_index("ix_canonical_manifests_flow_id", "canonical_manifests", ["flow_id"], unique=False)

    # 2. Create identifier_mappings table
    if "identifier_mappings" not in existing_tables:
        op.create_table(
            "identifier_mappings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("flow_id", sa.Integer(), nullable=False),
            sa.Column("mapping_scope", sa.String(length=50), nullable=False),
            sa.Column("canonical_id", sa.String(length=255), nullable=False),
            sa.Column("legacy_id", sa.String(length=255), nullable=False),
            sa.Column("source", sa.String(length=100), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=True, server_default=sa.text("1")),
            sa.ForeignKeyConstraint(["flow_id"], ["hedge_fund_flows.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_identifier_mappings_id", "identifier_mappings", ["id"], unique=False)
        op.create_index("ix_identifier_mappings_flow_id", "identifier_mappings", ["flow_id"], unique=False)

    # 3. Add columns to hedge_fund_flow_runs
    flow_run_columns = {col["name"] for col in inspector.get_columns("hedge_fund_flow_runs")}
    if "profile_name" not in flow_run_columns:
        op.add_column("hedge_fund_flow_runs", sa.Column("profile_name", sa.String(length=100), nullable=True))
    if "cancellation_requested" not in flow_run_columns:
        op.add_column("hedge_fund_flow_runs", sa.Column("cancellation_requested", sa.Boolean(), nullable=True, server_default=sa.text("0")))

    # 4. Create run_journals table
    if "run_journals" not in existing_tables:
        op.create_table(
            "run_journals",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("run_id", sa.Integer(), nullable=False),
            sa.Column("manifest_snapshot", sa.JSON(), nullable=False),
            sa.Column("compiled_request_snapshot", sa.JSON(), nullable=True),
            sa.Column("resolved_symbol_snapshot", sa.JSON(), nullable=True),
            sa.Column("bridge_provenance_snapshot", sa.JSON(), nullable=True),
            sa.Column("analyst_progress_events", sa.JSON(), nullable=True),
            sa.Column("analyst_outputs", sa.JSON(), nullable=True),
            sa.Column("decision_records", sa.JSON(), nullable=True),
            sa.Column("trade_records", sa.JSON(), nullable=True),
            sa.Column("portfolio_snapshots", sa.JSON(), nullable=True),
            sa.Column("artifact_index", sa.JSON(), nullable=True),
            sa.Column("diagnostics", sa.JSON(), nullable=True),
            sa.Column("is_finalized", sa.Boolean(), nullable=True, server_default=sa.text("0")),
            sa.ForeignKeyConstraint(["run_id"], ["hedge_fund_flow_runs.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("run_id", name="uq_run_journals_run_id"),
        )
        op.create_index("ix_run_journals_id", "run_journals", ["id"], unique=False)
        op.create_index("ix_run_journals_run_id", "run_journals", ["run_id"], unique=False)

    # 5. Create artifact_records table
    if "artifact_records" not in existing_tables:
        op.create_table(
            "artifact_records",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("run_id", sa.Integer(), nullable=False),
            sa.Column("artifact_id", sa.String(length=255), nullable=False),
            sa.Column("artifact_type", sa.String(length=100), nullable=False),
            sa.Column("format", sa.String(length=50), nullable=False),
            sa.Column("storage_ref", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
            sa.Column("retention_policy", sa.String(length=100), nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["hedge_fund_flow_runs.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("artifact_id", name="uq_artifact_records_artifact_id"),
        )
        op.create_index("ix_artifact_records_id", "artifact_records", ["id"], unique=False)
        op.create_index("ix_artifact_records_run_id", "artifact_records", ["run_id"], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if "artifact_records" in existing_tables:
        op.drop_table("artifact_records")
    
    if "run_journals" in existing_tables:
        op.drop_table("run_journals")

    flow_run_columns = {col["name"] for col in inspector.get_columns("hedge_fund_flow_runs")}
    if "cancellation_requested" in flow_run_columns:
        op.drop_column("hedge_fund_flow_runs", "cancellation_requested")
    if "profile_name" in flow_run_columns:
        op.drop_column("hedge_fund_flow_runs", "profile_name")

    if "identifier_mappings" in existing_tables:
        op.drop_table("identifier_mappings")

    if "canonical_manifests" in existing_tables:
        op.drop_table("canonical_manifests")
