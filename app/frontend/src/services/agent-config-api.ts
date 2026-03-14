import { ModelProvider } from '@/services/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface AgentConfigurationResponse {
  agent_key: string;
  display_name: string;
  description?: string | null;
  model_name?: string | null;
  model_provider?: ModelProvider | string | null;
  fallback_model_name?: string | null;
  fallback_model_provider?: ModelProvider | string | null;
  system_prompt_override?: string | null;
  system_prompt_append?: string | null;
  temperature?: number | null;
  max_tokens?: number | null;
  top_p?: number | null;
  warnings: string[];
  updated_at?: string | null;
}

export interface AgentConfigurationListResponse {
  agents: AgentConfigurationResponse[];
}

export interface AgentConfigurationUpdateRequest {
  model_name?: string | null;
  model_provider?: ModelProvider | string | null;
  fallback_model_name?: string | null;
  fallback_model_provider?: ModelProvider | string | null;
  system_prompt_override?: string | null;
  system_prompt_append?: string | null;
  temperature?: number | null;
  max_tokens?: number | null;
  top_p?: number | null;
  is_active?: boolean | null;
}

class AgentConfigApiService {
  private baseUrl = `${API_BASE_URL}/agent-config`;

  async getAll(): Promise<AgentConfigurationResponse[]> {
    const response = await fetch(`${this.baseUrl}/`);
    if (!response.ok) {
      throw new Error(`Failed to fetch agent configs: ${response.statusText}`);
    }
    const payload: AgentConfigurationListResponse = await response.json();
    return payload.agents;
  }

  async getOne(agentKey: string): Promise<AgentConfigurationResponse> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(agentKey)}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch agent config: ${response.statusText}`);
    }
    return response.json();
  }

  async update(agentKey: string, request: AgentConfigurationUpdateRequest): Promise<AgentConfigurationResponse> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(agentKey)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      throw new Error(`Failed to update agent config: ${response.statusText}`);
    }
    const payload = await response.json();
    window.dispatchEvent(new CustomEvent('agent-config-updated', { detail: { agentKey } }));
    return payload;
  }

  async reset(agentKey: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(agentKey)}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`Failed to reset agent config: ${response.statusText}`);
    }
    window.dispatchEvent(new CustomEvent('agent-config-updated', { detail: { agentKey } }));
  }

  async getDefaultPrompt(agentKey: string): Promise<string> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(agentKey)}/default-prompt`);
    if (!response.ok) {
      throw new Error(`Failed to fetch default prompt: ${response.statusText}`);
    }
    const payload = await response.json();
    return payload.default_prompt;
  }

  async applyToAll(fields: AgentConfigurationUpdateRequest, excludeAgents: string[] = []): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/apply-to-all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fields, exclude_agents: excludeAgents }),
    });
    if (!response.ok) {
      throw new Error(`Failed to apply config to all agents: ${response.statusText}`);
    }
    const payload = await response.json();
    window.dispatchEvent(new CustomEvent('agent-config-updated', { detail: { agentKey: 'all' } }));
    return payload.updated_agents || [];
  }
}

export const agentConfigApi = new AgentConfigApiService();
