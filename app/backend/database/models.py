from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    UniqueConstraint,
    Float,
    ForeignKey,
    Integer,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .connection import Base


class HedgeFundFlow(Base):
    """Table to store React Flow configurations (nodes, edges, viewport)"""

    __tablename__ = "hedge_fund_flows"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Flow metadata
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # React Flow state
    nodes = Column(JSON, nullable=False)  # Store React Flow nodes as JSON
    edges = Column(JSON, nullable=False)  # Store React Flow edges as JSON
    viewport = Column(JSON, nullable=True)  # Store viewport state (zoom, x, y)
    data = Column(
        JSON, nullable=True
    )  # Store node internal states (tickers, models, etc.)

    # Additional metadata
    is_template = Column(Boolean, default=False)  # Mark as template for reuse
    tags = Column(JSON, nullable=True)  # Store tags for categorization

    # Relationships
    manifests = relationship("CanonicalManifest", back_populates="flow")
    identifier_mappings = relationship("IdentifierMapping", back_populates="flow")


class CanonicalManifest(Base):
    """Canonical versioned definition of a flow"""

    __tablename__ = "canonical_manifests"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(
        Integer, ForeignKey("hedge_fund_flows.id"), nullable=True, index=True
    )
    manifest_version = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    payload = Column(JSON, nullable=False)  # Entire manifest JSON
    is_template = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    flow = relationship("HedgeFundFlow", back_populates="manifests")


class IdentifierMapping(Base):
    """Compatibility map between canonical stable IDs and legacy IDs"""

    __tablename__ = "identifier_mappings"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(
        Integer, ForeignKey("hedge_fund_flows.id"), nullable=False, index=True
    )
    mapping_scope = Column(String(50), nullable=False)  # node, edge, swarm, artifact
    canonical_id = Column(String(255), nullable=False)
    legacy_id = Column(String(255), nullable=False)
    source = Column(String(100), nullable=True)
    active = Column(Boolean, default=True)

    flow = relationship("HedgeFundFlow", back_populates="identifier_mappings")


class HedgeFundFlowRun(Base):
    """Table to track individual execution runs of a hedge fund flow"""

    __tablename__ = "hedge_fund_flow_runs"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(
        Integer, ForeignKey("hedge_fund_flows.id"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Run execution tracking
    status = Column(
        String(50), nullable=False, default="IDLE"
    )  # IDLE, IN_PROGRESS, COMPLETE, ERROR, CANCELLED
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Run configuration
    trading_mode = Column(
        String(50), nullable=False, default="one-time"
    )  # one-time, continuous, advisory, backtest, paper, live-intent
    profile_name = Column(String(100), nullable=True)  # Named run profile used
    schedule = Column(
        String(50), nullable=True
    )  # hourly, daily, weekly (for continuous mode)
    duration = Column(
        String(50), nullable=True
    )  # 1day, 1week, 1month (for continuous mode)

    # Run data
    request_data = Column(
        JSON, nullable=True
    )  # Store the request parameters (tickers, agents, models, etc.)
    initial_portfolio = Column(JSON, nullable=True)  # Store initial portfolio state
    final_portfolio = Column(JSON, nullable=True)  # Store final portfolio state
    results = Column(JSON, nullable=True)  # Store the output/results from the run
    error_message = Column(Text, nullable=True)  # Store error details if run failed

    # Lifecycle control
    cancellation_requested = Column(Boolean, default=False)

    # Metadata
    run_number = Column(
        Integer, nullable=False, default=1
    )  # Sequential run number for this flow

    # Relationships
    journal = relationship("RunJournal", back_populates="run", uselist=False)
    artifacts = relationship("ArtifactRecord", back_populates="run")


class RunJournal(Base):
    """Audit record for what happened during a run"""

    __tablename__ = "run_journals"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(
        Integer, ForeignKey("hedge_fund_flow_runs.id"), nullable=False, unique=True, index=True
    )
    manifest_snapshot = Column(JSON, nullable=False)
    compiled_request_snapshot = Column(JSON, nullable=True)
    resolved_symbol_snapshot = Column(JSON, nullable=True)
    bridge_provenance_snapshot = Column(JSON, nullable=True)
    analyst_progress_events = Column(JSON, nullable=True)
    analyst_outputs = Column(JSON, nullable=True)
    decision_records = Column(JSON, nullable=True)
    trade_records = Column(JSON, nullable=True)
    portfolio_snapshots = Column(JSON, nullable=True)
    artifact_index = Column(JSON, nullable=True)
    diagnostics = Column(JSON, nullable=True)
    is_finalized = Column(Boolean, default=False)

    run = relationship("HedgeFundFlowRun", back_populates="journal")


class ArtifactRecord(Base):
    """Indexed output produced by a run"""

    __tablename__ = "artifact_records"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(
        Integer, ForeignKey("hedge_fund_flow_runs.id"), nullable=False, index=True
    )
    artifact_id = Column(String(255), nullable=False, unique=True)
    artifact_type = Column(String(100), nullable=False)
    format = Column(String(50), nullable=False)
    storage_ref = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    retention_policy = Column(String(100), nullable=True)

    run = relationship("HedgeFundFlowRun", back_populates="artifacts")


class HedgeFundFlowRunCycle(Base):
    """Individual analysis cycles within a trading session"""

    __tablename__ = "hedge_fund_flow_run_cycles"

    id = Column(Integer, primary_key=True, index=True)
    flow_run_id = Column(
        Integer, ForeignKey("hedge_fund_flow_runs.id"), nullable=False, index=True
    )
    cycle_number = Column(Integer, nullable=False)  # 1, 2, 3, etc. within the run

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Analysis results
    analyst_signals = Column(JSON, nullable=True)  # All agent decisions/signals
    trading_decisions = Column(JSON, nullable=True)  # Portfolio manager decisions
    executed_trades = Column(
        JSON, nullable=True
    )  # Actual trades executed (paper trading)

    # Portfolio state after this cycle
    portfolio_snapshot = Column(
        JSON, nullable=True
    )  # Cash, positions, performance metrics

    # Performance metrics for this cycle
    performance_metrics = Column(JSON, nullable=True)  # Returns, sharpe ratio, etc.

    # Execution tracking
    status = Column(
        String(50), nullable=False, default="IN_PROGRESS"
    )  # IN_PROGRESS, COMPLETED, ERROR
    error_message = Column(Text, nullable=True)  # Store error details if cycle failed

    # Cost tracking
    llm_calls_count = Column(
        Integer, nullable=True, default=0
    )  # Number of LLM calls made
    api_calls_count = Column(
        Integer, nullable=True, default=0
    )  # Number of financial API calls made
    estimated_cost = Column(String(20), nullable=True)  # Estimated cost in USD

    # Metadata
    trigger_reason = Column(
        String(100), nullable=True
    )  # scheduled, manual, market_event, etc.
    market_conditions = Column(
        JSON, nullable=True
    )  # Market data snapshot at cycle start


class ApiKey(Base):
    """Table to store API keys for various services"""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # API key details
    provider = Column(
        String(100), nullable=False, unique=True, index=True
    )  # e.g., "ANTHROPIC_API_KEY"
    key_value = Column(
        Text, nullable=False
    )  # The actual API key (encrypted in production)
    is_active = Column(Boolean, default=True)  # Enable/disable without deletion
    validation_status = Column(String(20), default="valid")
    validation_error = Column(Text, nullable=True)
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    last_validation_latency_ms = Column(Integer, nullable=True)
    provider_record_id = Column(
        Integer, ForeignKey("provider_records.id"), nullable=True, index=True
    )

    # Optional metadata
    description = Column(Text, nullable=True)  # Human-readable description
    last_used = Column(DateTime(timezone=True), nullable=True)  # Track usage
    provider_record = relationship("ProviderRecord", back_populates="api_keys")


class ProviderRecord(Base):
    """Canonical provider identity for built-in, generic, local, and retired providers."""

    __tablename__ = "provider_records"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    provider_key = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    provider_kind = Column(String(50), nullable=False, default="builtin")
    builtin_provider_key = Column(String(100), nullable=True)
    connection_mode = Column(String(50), nullable=True)
    endpoint_url = Column(Text, nullable=True)
    models_url = Column(Text, nullable=True)
    auth_mode = Column(String(50), nullable=True)
    request_defaults = Column(JSON, nullable=True)
    extra_headers = Column(JSON, nullable=True)
    is_enabled = Column(Boolean, default=True)
    is_retired = Column(Boolean, default=False)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    api_keys = relationship("ApiKey", back_populates="provider_record")
    custom_models = relationship("CustomModel", back_populates="provider_record")


class CustomModel(Base):
    """Table to store validated user-added custom models."""

    __tablename__ = "custom_models"
    __table_args__ = (
        UniqueConstraint(
            "provider_record_id",
            "model_name",
            name="uq_custom_models_provider_record_model",
        ),
        Index("ix_custom_models_provider_record_id", "provider_record_id"),
        Index("ix_custom_models_availability_status", "availability_status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    provider = Column(String(100), nullable=False, index=True)
    provider_record_id = Column(
        Integer, ForeignKey("provider_records.id"), nullable=True
    )
    model_name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False, default="manual")
    is_enabled = Column(Boolean, default=False)
    availability_status = Column(String(20), default="available")
    status_reason = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    validation_status = Column(String(20), default="valid")
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    provider_record = relationship("ProviderRecord", back_populates="custom_models")


class AgentConfiguration(Base):
    """Persistent per-agent LLM configuration."""

    __tablename__ = "agent_configurations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    agent_key = Column(String(100), nullable=False, unique=True, index=True)
    model_name = Column(String(255), nullable=True)
    model_provider = Column(String(100), nullable=True)
    fallback_model_name = Column(String(255), nullable=True)
    fallback_model_provider = Column(String(100), nullable=True)
    system_prompt_override = Column(Text, nullable=True)
    system_prompt_append = Column(Text, nullable=True)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    top_p = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
