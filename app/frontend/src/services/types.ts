// Shared types for API requests and responses
export enum ModelProvider {
  OPENAI = 'OpenAI',
  ANTHROPIC = 'Anthropic',
  DEEPSEEK = 'DeepSeek',
  GOOGLE = 'Google',
  GROQ = 'Groq',
  OLLAMA = 'Ollama',
  LMSTUDIO = 'LMStudio',
  OPENROUTER = 'OpenRouter',
  XAI = 'xAI',
  AZURE_OPENAI = 'Azure OpenAI',
}

export interface AgentModelConfig {
  agent_id: string;
  model_name?: string;
  model_provider?: ModelProvider | string;
  provider_key?: string;
  fallback_model_name?: string;
  fallback_model_provider?: ModelProvider | string;
  fallback_provider_key?: string;
  system_prompt_override?: string;
  system_prompt_append?: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
}

export interface GraphNode {
  id: string;
  type?: string;
  data?: any;
  position?: { x: number; y: number };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  data?: any;
}

export interface PortfolioPosition {
  ticker: string;
  quantity: number;
  trade_price: number;
}

// Base interface for shared fields between HedgeFundRequest and BacktestRequest
export interface BaseHedgeFundRequest {
  tickers: string[];
  graph_nodes: GraphNode[];
  graph_edges: GraphEdge[];
  agent_models?: AgentModelConfig[];
  model_name?: string;
  model_provider?: ModelProvider | string;
  margin_requirement?: number;
  portfolio_positions?: PortfolioPosition[];
}

export interface HedgeFundRequest extends BaseHedgeFundRequest {
  end_date?: string;
  start_date?: string;
  initial_cash?: number;
}

export interface BacktestRequest extends BaseHedgeFundRequest {
  start_date: string;
  end_date: string;
  initial_capital?: number;
}

export interface BacktestDayResult {
  date: string;
  portfolio_value: number;
  cash: number;
  decisions: Record<string, any>;
  executed_trades: Record<string, number>;
  analyst_signals: Record<string, any>;
  current_prices: Record<string, number>;
  long_exposure: number;
  short_exposure: number;
  gross_exposure: number;
  net_exposure: number;
  long_short_ratio: number | null;
}

export interface BacktestPerformanceMetrics {
  sharpe_ratio?: number;
  sortino_ratio?: number;
  max_drawdown?: number;
  max_drawdown_date?: string;
  long_short_ratio?: number;
  gross_exposure?: number;
  net_exposure?: number;
} 
