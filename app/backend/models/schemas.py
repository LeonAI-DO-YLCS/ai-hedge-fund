from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from src.llm.models import ModelProvider
from enum import Enum
import re

class FlowRunStatus(str, Enum):
    IDLE = "IDLE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


def extract_base_agent_key(unique_id: str) -> str:
    """
    Extract the base agent key from a unique node ID. (Blueprint Section 19.3)
    """
    # For agent nodes, remove the last underscore and 6-character suffix
    parts = unique_id.split('_')
    if len(parts) >= 2:
        last_part = parts[-1]
        # If the last part is a 6-character alphanumeric string, it's likely our suffix
        if len(last_part) == 6 and re.match(r'^[a-z0-9]+$', last_part):
            return '_'.join(parts[:-1])
    return unique_id


class AgentModelConfig(BaseModel):
    agent_id: str
    model_name: Optional[str] = None
    model_provider: Optional[str] = None
    provider_key: Optional[str] = None
    fallback_model_name: Optional[str] = None
    fallback_model_provider: Optional[str] = None
    fallback_provider_key: Optional[str] = None
    system_prompt_override: Optional[str] = None
    system_prompt_append: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class PortfolioPosition(BaseModel):
    ticker: str
    quantity: float
    trade_price: float

    @field_validator("trade_price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Trade price must be positive!")
        return v


class GraphNode(BaseModel):
    id: str
    type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    position: Optional[Dict[str, Any]] = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class HedgeFundResponse(BaseModel):
    decisions: dict
    analyst_signals: dict


class ErrorResponse(BaseModel):
    message: str
    error: str | None = None


class MT5ConnectionResponse(BaseModel):
    status: Literal["ready", "degraded", "unavailable", "unknown"] = "unknown"
    connected: bool
    authorized: bool = False
    broker: Optional[str] = None
    account_id: Optional[int] = None
    balance: Optional[float] = None
    latency_ms: Optional[int] = None
    last_checked_at: str
    error: Optional[str] = None


class MT5SymbolEntry(BaseModel):
    ticker: str
    mt5_symbol: str
    category: str
    lot_size: Optional[float] = None
    enabled: bool = True
    source: str = "symbols_yaml"
    runtime_status: Optional[str] = None


class MT5SymbolsResponse(BaseModel):
    status: Literal["ready", "degraded", "unavailable", "unknown"] = "unknown"
    symbols: List[MT5SymbolEntry]
    count: int
    last_refreshed_at: str
    error: Optional[str] = None


class FlowRunLaunchRequest(BaseModel):
    flow_id: int
    profile_name: str = "default"
    overrides: Optional[Dict[str, Any]] = None
    live_intent_confirmed: bool = False


class FlowRunResponse(BaseModel):
    run_id: int
    flow_id: int
    profile_name: str
    status: str
    mode: Optional[str] = None
    events_url: Optional[str] = None
    details_url: Optional[str] = None


class MT5MetricsResponse(BaseModel):
    status: Literal["ready", "degraded", "unavailable", "unknown"] = "unknown"
    uptime_seconds: float = 0.0
    total_requests: int = 0
    requests_by_endpoint: Dict[str, int] = Field(default_factory=dict)
    errors_count: int = 0
    last_request_at: Optional[str] = None
    retention_days: int = 1
    error: Optional[str] = None


class MT5LogEntry(BaseModel):
    timestamp: str
    request: Dict[str, Any] = Field(default_factory=dict)
    response: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None


class MT5LogsResponse(BaseModel):
    status: Literal["ready", "degraded", "unavailable", "unknown"] = "unknown"
    total: int = 0
    offset: int = 0
    limit: int = 50
    entries: List[MT5LogEntry] = Field(default_factory=list)
    error: Optional[str] = None


class MT5RuntimeDiagnosticsResponse(BaseModel):
    status: Literal["ready", "degraded", "unavailable", "unknown"] = "unknown"
    diagnostics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class MT5SymbolDiagnosticsResponse(BaseModel):
    status: Literal["ready", "degraded", "unavailable", "unknown"] = "unknown"
    generated_at: Optional[str] = None
    worker_state: Optional[str] = None
    configured_symbols: int = 0
    checked_count: int = 0
    items: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


class ProviderModelResponse(BaseModel):
    display_name: str
    model_name: str
    provider_key: Optional[str] = None
    provider: Optional[str] = None
    source: Optional[str] = None
    is_enabled: bool = False
    availability_status: Optional[str] = None
    status_reason: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    is_custom: bool = False
    is_stale: bool = False


class ProviderStatusResponse(BaseModel):
    name: str
    type: Literal["cloud", "local"]
    available: bool
    status: str
    source: Optional[str] = None
    error: Optional[str] = None
    last_checked_at: str
    models: List[ProviderModelResponse]


# Base class for shared fields between HedgeFundRequest and BacktestRequest
class BaseHedgeFundRequest(BaseModel):
    tickers: List[str]
    graph_nodes: List[GraphNode]
    graph_edges: List[GraphEdge]
    agent_models: Optional[List[AgentModelConfig]] = None
    model_name: Optional[str] = "gpt-4.1"
    model_provider: Optional[str] = ModelProvider.OPENAI.value
    margin_requirement: float = 0.0
    portfolio_positions: Optional[List[PortfolioPosition]] = None
    api_keys: Optional[Dict[str, str]] = None

    def get_agent_ids(self) -> List[str]:
        """Extract agent IDs from graph structure"""
        return [node.id for node in self.graph_nodes]

    def get_agent_model_config(self, agent_id: str) -> tuple[str, str]:
        """Get model configuration for a specific agent with exact-match precedence."""
        if not self.agent_models:
            return (
                self.model_name or "gpt-4.1",
                self.model_provider or ModelProvider.OPENAI.value,
            )

        # 1. Try exact node ID match first (Blueprint Section 19.5)
        for config in self.agent_models:
            if config.agent_id == agent_id:
                return (
                    config.model_name or self.model_name or "gpt-4.1",
                    config.model_provider
                    or self.model_provider
                    or ModelProvider.OPENAI.value,
                )

        # 2. Fallback to base agent key match
        base_agent_key = extract_base_agent_key(agent_id)
        for config in self.agent_models:
            if extract_base_agent_key(config.agent_id) == base_agent_key:
                return (
                    config.model_name or self.model_name or "gpt-4.1",
                    config.model_provider
                    or self.model_provider
                    or ModelProvider.OPENAI.value,
                )

        # 3. Final fallback to global model settings
        return (
            self.model_name or "gpt-4.1",
            self.model_provider or ModelProvider.OPENAI.value,
        )

    def get_agent_runtime_config(self, agent_id: str) -> Optional[AgentModelConfig]:
        """Get full runtime config for a specific agent with exact-match precedence."""
        if not self.agent_models:
            return None

        # 1. Try exact node ID match first
        for config in self.agent_models:
            if config.agent_id == agent_id:
                return config

        # 2. Fallback to base agent key match
        base_agent_key = extract_base_agent_key(agent_id)
        for config in self.agent_models:
            if extract_base_agent_key(config.agent_id) == base_agent_key:
                return config

        return None


class BacktestRequest(BaseHedgeFundRequest):
    start_date: str
    end_date: str
    initial_capital: float = 100000.0


class BacktestDayResult(BaseModel):
    date: str
    portfolio_value: float
    cash: float
    decisions: Dict[str, Any]
    executed_trades: Dict[str, float]
    analyst_signals: Dict[str, Any]
    current_prices: Dict[str, float]
    long_exposure: float
    short_exposure: float
    gross_exposure: float
    net_exposure: float
    long_short_ratio: Optional[float] = None


class BacktestPerformanceMetrics(BaseModel):
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    max_drawdown_date: Optional[str] = None
    long_short_ratio: Optional[float] = None
    gross_exposure: Optional[float] = None
    net_exposure: Optional[float] = None


class BacktestResponse(BaseModel):
    results: List[BacktestDayResult]
    performance_metrics: BacktestPerformanceMetrics
    final_portfolio: Dict[str, Any]


class HedgeFundRequest(BaseHedgeFundRequest):
    end_date: Optional[str] = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d")
    )
    start_date: Optional[str] = None
    initial_cash: float = 100000.0

    def get_start_date(self) -> str:
        """Calculate start date if not provided"""
        if self.start_date:
            return self.start_date
        if not self.end_date:
            raise ValueError("end_date is required to calculate a default start_date")
        return (
            datetime.strptime(self.end_date, "%Y-%m-%d") - timedelta(days=90)
        ).strftime("%Y-%m-%d")


# Flow-related schemas
class FlowCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    viewport: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    is_template: bool = False
    tags: Optional[List[str]] = None


class FlowUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    viewport: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    is_template: Optional[bool] = None
    tags: Optional[List[str]] = None


class FlowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    viewport: Optional[Dict[str, Any]]
    data: Optional[Dict[str, Any]]
    is_template: bool
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class FlowSummaryResponse(BaseModel):
    """Lightweight flow response without nodes/edges for listing"""

    id: int
    name: str
    description: Optional[str]
    is_template: bool
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Flow Run schemas
class FlowRunCreateRequest(BaseModel):
    """Request to create a new flow run"""

    request_data: Optional[Dict[str, Any]] = None


class FlowRunUpdateRequest(BaseModel):
    """Request to update an existing flow run"""

    status: Optional[FlowRunStatus] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class FlowRunResponse(BaseModel):
    """Complete flow run response"""

    id: int
    flow_id: int
    status: FlowRunStatus
    run_number: int
    created_at: datetime
    updated_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    profile_name: Optional[str] = None
    request_data: Optional[Dict[str, Any]]
    results: Optional[Dict[str, Any]]
    error_message: Optional[str]
    cancellation_requested: bool = False

    model_config = ConfigDict(from_attributes=True)


class FlowRunSummaryResponse(BaseModel):
    """Lightweight flow run response for listing"""

    id: int
    flow_id: int
    status: FlowRunStatus
    run_number: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# API Key schemas
class ApiKeyCreateRequest(BaseModel):
    """Request to create or update an API key"""

    provider: str = Field(..., min_length=1, max_length=100)
    key_value: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_active: bool = True
    validation_status: Optional[str] = None
    validation_error: Optional[str] = None
    last_validated_at: Optional[datetime] = None
    last_validation_latency_ms: Optional[int] = None


class ApiKeyUpdateRequest(BaseModel):
    """Request to update an existing API key"""

    key_value: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    validation_status: Optional[str] = None
    validation_error: Optional[str] = None
    last_validated_at: Optional[datetime] = None
    last_validation_latency_ms: Optional[int] = None


class ApiKeyValidateRequest(BaseModel):
    provider: Optional[str] = Field(default=None, min_length=1, max_length=100)
    provider_key: Optional[str] = Field(default=None, min_length=1, max_length=100)
    key_value: str = Field(..., min_length=1)


class ApiKeyValidateResponse(BaseModel):
    provider_key: Optional[str] = None
    provider: str
    display_name: str
    valid: bool
    status: str
    checked_at: str
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    discovered_models: Optional[List[str]] = None


class ApiKeyResponse(BaseModel):
    """Complete API key response"""

    id: int
    provider: str
    provider_key: Optional[str] = None
    provider_kind: Optional[str] = None
    connection_mode: Optional[str] = None
    endpoint_url: Optional[str] = None
    models_url: Optional[str] = None
    request_defaults: Optional[Dict[str, Any]] = None
    extra_headers: Optional[Dict[str, str]] = None
    key_value: str
    is_active: bool
    description: Optional[str]
    display_name: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    validation_error: Optional[str] = None
    last_validated_at: Optional[datetime] = None
    last_validation_latency_ms: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime]
    last_used: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ApiKeySummaryResponse(BaseModel):
    """API key response without the actual key value"""

    id: Optional[int] = None
    provider: str
    provider_key: Optional[str] = None
    display_name: Optional[str] = None
    provider_kind: Optional[str] = None
    connection_mode: Optional[str] = None
    source: Optional[str] = None
    status: str = "unconfigured"
    group: Optional[str] = None
    available: bool = False
    error: Optional[str] = None
    is_active: bool
    description: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime]
    last_used: Optional[datetime]
    has_key: bool = True
    has_stored_key: bool = True
    enabled_model_count: int = 0
    inventory_count: int = 0
    collapsed_by_default: bool = True
    last_validated_at: Optional[datetime] = None
    validation_error: Optional[str] = None
    last_validation_latency_ms: Optional[int] = None
    supports_model_discovery: bool = False

    model_config = ConfigDict(from_attributes=True)


class ApiKeyBulkUpdateRequest(BaseModel):
    """Request to update multiple API keys at once"""

    api_keys: List[ApiKeyCreateRequest]


class ProviderUpsertRequest(BaseModel):
    provider_key: Optional[str] = None
    display_name: str = Field(..., min_length=1, max_length=255)
    provider_kind: str = Field(default="generic")
    connection_mode: str = Field(..., min_length=1, max_length=50)
    endpoint_url: Optional[str] = None
    models_url: Optional[str] = None
    key_value: Optional[str] = None
    request_defaults: Optional[Dict[str, Any]] = None
    extra_headers: Optional[Dict[str, str]] = None
    is_active: bool = True


class CustomModelRequest(BaseModel):
    provider: Optional[str] = Field(default=None, min_length=1, max_length=100)
    provider_key: Optional[str] = Field(default=None, min_length=1, max_length=100)
    model_name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(default=None, max_length=255)


class CustomModelResponse(BaseModel):
    id: Optional[int] = None
    provider: str
    provider_key: Optional[str] = None
    model_name: str
    display_name: str
    source: Optional[str] = None
    is_enabled: bool = False
    availability_status: Optional[str] = None
    status_reason: Optional[str] = None
    validation_status: str = "valid"
    last_validated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ModelDiscoveryRequest(BaseModel):
    provider: Optional[str] = Field(default=None, min_length=1, max_length=100)
    provider_key: Optional[str] = Field(default=None, min_length=1, max_length=100)
    force_refresh: bool = False


class ModelDiscoveryResponse(BaseModel):
    provider: str
    provider_key: Optional[str] = None
    cache_state: str
    discovered_at: str
    expires_at: str
    models: List[ProviderModelResponse]


class ProviderInventoryResponse(BaseModel):
    provider_key: str
    display_name: str
    search_enabled: bool = True
    inventory: List[ProviderModelResponse] = Field(default_factory=list)


class UpdateEnabledModelsRequest(BaseModel):
    enabled_models: List[str] = Field(default_factory=list)


class ProviderSummaryListResponse(BaseModel):
    providers: List[ApiKeySummaryResponse]


class AgentConfigurationUpdateRequest(BaseModel):
    model_name: Optional[str] = None
    model_provider: Optional[str] = None
    fallback_model_name: Optional[str] = None
    fallback_model_provider: Optional[str] = None
    system_prompt_override: Optional[str] = None
    system_prompt_append: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None


class AgentConfigurationSummaryResponse(BaseModel):
    agent_key: str
    display_name: str
    description: Optional[str] = None
    updated_at: Optional[datetime] = None
    has_customizations: bool = False
    warnings: List[str] = Field(default_factory=list)


class AgentConfigurationPersistedResponse(BaseModel):
    system_prompt_override: Optional[str] = None
    system_prompt_append: Optional[str] = None
    model_name: Optional[str] = None
    model_provider: Optional[str] = None
    fallback_model_name: Optional[str] = None
    fallback_model_provider: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None


class AgentConfigurationDefaultsResponse(BaseModel):
    system_prompt_text: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None


class AgentConfigurationEffectiveResponse(BaseModel):
    system_prompt_text: str
    prompt_mode: Literal["default", "override", "append"] = "default"
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    model_name: Optional[str] = None
    model_provider: Optional[str] = None
    fallback_model_name: Optional[str] = None
    fallback_model_provider: Optional[str] = None


class AgentConfigurationSourcesResponse(BaseModel):
    system_prompt_text: str
    temperature: str
    max_tokens: str
    top_p: str
    model_name: str
    model_provider: str
    fallback_model_name: str
    fallback_model_provider: str


class AgentConfigurationDetailResponse(BaseModel):
    agent_key: str
    display_name: str
    description: Optional[str] = None
    persisted: AgentConfigurationPersistedResponse
    defaults: AgentConfigurationDefaultsResponse
    effective: AgentConfigurationEffectiveResponse
    sources: AgentConfigurationSourcesResponse
    warnings: List[str] = Field(default_factory=list)
    updated_at: Optional[datetime] = None


class AgentConfigurationListResponse(BaseModel):
    agents: List[AgentConfigurationSummaryResponse]


class AgentConfigurationEffectiveUpdateRequest(BaseModel):
    effective: AgentConfigurationEffectiveResponse


class AgentDefaultPromptResponse(BaseModel):
    agent_key: str
    default_prompt: str


class AgentApplyToAllRequest(BaseModel):
    fields: AgentConfigurationUpdateRequest
    exclude_agents: List[str] = Field(default_factory=list)
# --- CLI Flow Control and Manifest Management Schemas ---

class CatalogResponse(BaseModel):
    status: Literal["ready", "degraded", "unavailable"] = "ready"
    version: str
    items: List[Dict[str, Any]]


class AgentCatalogEntry(BaseModel):
    agent_key: str
    display_name: str
    description: Optional[str] = None
    agent_type: str = "analyst"
    default_order: int = 10
    supported_node_category: str = "analyst"
    configurable_runtime_fields: List[str] = Field(default_factory=list)


class NodeTypeCatalogEntry(BaseModel):
    type_key: str
    category: str
    display_name: str
    allowed_inbound: List[str]
    allowed_outbound: List[str]
    required_fields: List[str]
    optional_fields: List[str]
    compiler_strategy: str


class SwarmCatalogEntry(BaseModel):
    swarm_id: str
    display_name: str
    member_templates: List[str]
    execution_policy: str
    merge_policy: str
    risk_policy: str
    output_target: str


class OutputSinkCatalogEntry(BaseModel):
    sink_key: str
    display_name: str
    delivery_modes: List[str]
    artifact_types: List[str]


class FlowManifestSchema(BaseModel):
    manifest_version: str = "1.0"
    flow: Dict[str, Any] = Field(default_factory=dict)
    catalog_refs: Dict[str, str] = Field(default_factory=dict)
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    swarms: List[Dict[str, Any]] = Field(default_factory=list)
    input_resolution: Dict[str, Any] = Field(default_factory=dict)
    agent_runtime: Dict[str, Any] = Field(default_factory=dict)
    portfolio_policy: Dict[str, Any] = Field(default_factory=dict)
    execution_policy: Dict[str, Any] = Field(default_factory=dict)
    data_policy: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    run_profiles: List[Dict[str, Any]] = Field(default_factory=list)
    audit_policy: Dict[str, Any] = Field(default_factory=dict)
    compatibility_mappings: List[Dict[str, Any]] = Field(default_factory=list)


class ManifestImportRequest(BaseModel):
    manifest: FlowManifestSchema
    options: Dict[str, Any] = Field(default_factory=lambda: {"validate_only": False, "materialize_legacy_projection": True})


class ManifestExportResponse(BaseModel):
    manifest: FlowManifestSchema
    compiled_view: Optional[Dict[str, Any]] = None
    legacy_projection: Optional[Dict[str, Any]] = None
    latest_run_snapshot: Optional[Dict[str, Any]] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    code: str
    path: str
    message: str


class ValidationResponse(BaseModel):
    valid: bool
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    catalog_versions: Dict[str, str] = Field(default_factory=dict)


class CompilationResponse(BaseModel):
    compiled_request: Dict[str, Any]
    compatibility_projection: Dict[str, Any]
    expansion_map: Dict[str, List[str]]
    resolved_symbols: List[Any] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)


class RunLaunchRequest(BaseModel):
    profile_name: str
    overrides: Dict[str, Any] = Field(default_factory=dict)
    live_execution_confirmed: bool = False


class RunLaunchResponse(BaseModel):
    run_id: int
    flow_id: int
    profile_name: str
    status: FlowRunStatus
    mode: str
    events_url: str
    details_url: str


class RunProfileResponse(BaseModel):
    profile_name: str
    mode: str
    config: Dict[str, Any]


class RunSummaryResponse(BaseModel):
    run_id: int
    flow_id: int
    status: FlowRunStatus
    profile_name: Optional[str] = None
    manifest_snapshot_ref: Optional[str] = None
    resolved_symbols_count: int = 0
    artifact_count: int = 0
    bridge_status: str = "unknown"


class DecisionJournalEntry(BaseModel):
    timestamp: datetime
    decision_stage: str
    instrument: str
    action: str
    quantity: float
    rationale: Optional[str] = None


class TradeJournalEntry(BaseModel):
    timestamp: datetime
    instrument: str
    intent: str
    mode: str
    status: str
    execution_details: Dict[str, Any] = Field(default_factory=dict)


class ArtifactIndexEntry(BaseModel):
    artifact_id: str
    artifact_type: str
    format: str
    created_at: datetime
    download_url: str


class ProvenanceResponse(BaseModel):
    status: str
    resolved_at: datetime
    symbols: List[Dict[str, Any]]
    diagnostics: List[str]
    bridge_snapshot: Optional[Dict[str, Any]] = None
