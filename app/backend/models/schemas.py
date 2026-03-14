from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from src.llm.models import ModelProvider
from enum import Enum
from app.backend.services.graph import extract_base_agent_key


class FlowRunStatus(str, Enum):
    IDLE = "IDLE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class AgentModelConfig(BaseModel):
    agent_id: str
    model_name: Optional[str] = None
    model_provider: Optional[ModelProvider] = None
    fallback_model_name: Optional[str] = None
    fallback_model_provider: Optional[ModelProvider] = None
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
    provider: Optional[str] = None
    source: Optional[str] = None
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
    model_provider: Optional[ModelProvider] = ModelProvider.OPENAI
    margin_requirement: float = 0.0
    portfolio_positions: Optional[List[PortfolioPosition]] = None
    api_keys: Optional[Dict[str, str]] = None

    def get_agent_ids(self) -> List[str]:
        """Extract agent IDs from graph structure"""
        return [node.id for node in self.graph_nodes]

    def get_agent_model_config(self, agent_id: str) -> tuple[str, ModelProvider]:
        """Get model configuration for a specific agent"""
        if self.agent_models:
            # Extract base agent key from unique node ID for matching
            base_agent_key = extract_base_agent_key(agent_id)

            for config in self.agent_models:
                # Check both unique node ID and base agent key for matches
                config_base_key = extract_base_agent_key(config.agent_id)
                if config.agent_id == agent_id or config_base_key == base_agent_key:
                    return (
                        config.model_name or self.model_name or "gpt-4.1",
                        config.model_provider
                        or self.model_provider
                        or ModelProvider.OPENAI,
                    )
        # Fallback to global model settings
        return self.model_name or "gpt-4.1", self.model_provider or ModelProvider.OPENAI

    def get_agent_runtime_config(self, agent_id: str) -> Optional[AgentModelConfig]:
        if not self.agent_models:
            return None
        base_agent_key = extract_base_agent_key(agent_id)
        for config in self.agent_models:
            config_base_key = extract_base_agent_key(config.agent_id)
            if config.agent_id == agent_id or config_base_key == base_agent_key:
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
    request_data: Optional[Dict[str, Any]]
    results: Optional[Dict[str, Any]]
    error_message: Optional[str]

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
    provider: str = Field(..., min_length=1, max_length=100)
    key_value: str = Field(..., min_length=1)


class ApiKeyValidateResponse(BaseModel):
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
    display_name: Optional[str] = None
    source: Optional[str] = None
    status: str = "unconfigured"
    is_active: bool
    description: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime]
    last_used: Optional[datetime]
    has_key: bool = True
    has_stored_key: bool = True
    last_validated_at: Optional[datetime] = None
    validation_error: Optional[str] = None
    last_validation_latency_ms: Optional[int] = None
    supports_model_discovery: bool = False

    model_config = ConfigDict(from_attributes=True)


class ApiKeyBulkUpdateRequest(BaseModel):
    """Request to update multiple API keys at once"""

    api_keys: List[ApiKeyCreateRequest]


class CustomModelRequest(BaseModel):
    provider: str = Field(..., min_length=1, max_length=100)
    model_name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(default=None, max_length=255)


class CustomModelResponse(BaseModel):
    id: Optional[int] = None
    provider: str
    model_name: str
    display_name: str
    validation_status: str = "valid"
    last_validated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ModelDiscoveryRequest(BaseModel):
    provider: str = Field(..., min_length=1, max_length=100)
    force_refresh: bool = False


class ModelDiscoveryResponse(BaseModel):
    provider: str
    cache_state: str
    discovered_at: str
    expires_at: str
    models: List[ProviderModelResponse]


class AgentConfigurationUpdateRequest(BaseModel):
    model_name: Optional[str] = None
    model_provider: Optional[ModelProvider] = None
    fallback_model_name: Optional[str] = None
    fallback_model_provider: Optional[ModelProvider] = None
    system_prompt_override: Optional[str] = None
    system_prompt_append: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None


class AgentConfigurationResponse(BaseModel):
    agent_key: str
    display_name: str
    description: Optional[str] = None
    model_name: Optional[str] = None
    model_provider: Optional[ModelProvider] = None
    fallback_model_name: Optional[str] = None
    fallback_model_provider: Optional[ModelProvider] = None
    system_prompt_override: Optional[str] = None
    system_prompt_append: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    updated_at: Optional[datetime] = None


class AgentConfigurationListResponse(BaseModel):
    agents: List[AgentConfigurationResponse]


class AgentDefaultPromptResponse(BaseModel):
    agent_key: str
    default_prompt: str


class AgentApplyToAllRequest(BaseModel):
    fields: AgentConfigurationUpdateRequest
    exclude_agents: List[str] = Field(default_factory=list)
