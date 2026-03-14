const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export type ApiKeyStatus = 'valid' | 'invalid' | 'unverified' | 'unconfigured' | 'inactive' | 'disabled' | 'retired' | 'unsaved' | 'unavailable';
export type ProviderGroup = 'activated' | 'inactive' | 'disabled' | 'unconfigured' | 'retired';
export type ConnectionMode = 'openai_compatible' | 'anthropic_compatible' | 'direct_http' | 'local_probe' | string;

export interface ApiKey {
  id: number;
  provider: string;
  provider_key?: string | null;
  provider_kind?: string | null;
  connection_mode?: ConnectionMode | null;
  endpoint_url?: string | null;
  models_url?: string | null;
  request_defaults?: Record<string, unknown> | null;
  extra_headers?: Record<string, string> | null;
  key_value: string;
  is_active: boolean;
  description?: string;
  display_name?: string;
  source?: string;
  status?: ApiKeyStatus | string;
  validation_error?: string | null;
  last_validated_at?: string | null;
  last_validation_latency_ms?: number | null;
  created_at: string;
  updated_at?: string;
  last_used?: string;
}

export interface ApiKeySummary {
  id?: number;
  provider: string;
  provider_key?: string;
  display_name?: string;
  provider_kind?: string | null;
  connection_mode?: ConnectionMode | null;
  source?: string;
  status: ApiKeyStatus | string;
  group?: ProviderGroup | string;
  available?: boolean;
  error?: string | null;
  is_active: boolean;
  description?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  last_used?: string | null;
  last_validated_at?: string | null;
  validation_error?: string | null;
  last_validation_latency_ms?: number | null;
  has_key: boolean;
  has_stored_key?: boolean;
  enabled_model_count?: number;
  inventory_count?: number;
  collapsed_by_default?: boolean;
  supports_model_discovery?: boolean;
}

export interface ApiKeyCreateRequest {
  provider: string;
  key_value: string;
  description?: string;
  is_active: boolean;
  validation_status?: string;
  validation_error?: string | null;
  last_validated_at?: string | null;
  last_validation_latency_ms?: number | null;
}

export interface GenericProviderUpsertRequest {
  provider_key?: string;
  display_name: string;
  provider_kind?: 'generic';
  connection_mode: ConnectionMode;
  endpoint_url?: string | null;
  models_url?: string | null;
  key_value?: string | null;
  request_defaults?: Record<string, unknown> | null;
  extra_headers?: Record<string, string> | null;
  is_active: boolean;
}

export interface ApiKeyUpdateRequest {
  key_value?: string;
  description?: string;
  is_active?: boolean;
  validation_status?: string;
  validation_error?: string | null;
  last_validated_at?: string | null;
  last_validation_latency_ms?: number | null;
}

export interface ApiKeyValidateResponse {
  provider: string;
  provider_key?: string;
  display_name: string;
  valid: boolean;
  status: ApiKeyStatus | string;
  checked_at: string;
  latency_ms?: number | null;
  error?: string | null;
  discovered_models?: string[] | null;
}

export interface ApiKeyBulkUpdateRequest {
  api_keys: ApiKeyCreateRequest[];
}

class ApiKeysService {
  private baseUrl = `${API_BASE_URL}/api-keys`;

  async getAllApiKeys(includeInactive = false): Promise<ApiKeySummary[]> {
    const params = new URLSearchParams();
    if (includeInactive) params.append('include_inactive', 'true');
    const response = await fetch(`${this.baseUrl}?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch API keys: ${response.statusText}`);
    }
    const payload = await response.json();
    return payload.providers || [];
  }

  async getApiKey(providerKey: string): Promise<ApiKey> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(providerKey)}`);
    if (!response.ok) {
      if (response.status === 404) throw new Error('API key not found');
      throw new Error(`Failed to fetch API key: ${response.statusText}`);
    }
    return response.json();
  }

  async validateApiKey(providerKey: string, keyValue: string): Promise<ApiKeyValidateResponse> {
    const response = await fetch(`${this.baseUrl}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider_key: providerKey, key_value: keyValue }),
    });
    if (!response.ok) {
      throw new Error(`Failed to validate API key: ${response.statusText}`);
    }
    return response.json();
  }

  async createOrUpdateApiKey(request: ApiKeyCreateRequest): Promise<ApiKey> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `Failed to create/update API key: ${response.statusText}`);
    }
    return response.json();
  }

  async createGenericProvider(request: GenericProviderUpsertRequest): Promise<ApiKey> {
    const response = await fetch(`${this.baseUrl}/providers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `Failed to create provider: ${response.statusText}`);
    }
    return response.json();
  }

  async updateGenericProvider(providerKey: string, request: GenericProviderUpsertRequest): Promise<ApiKey> {
    const response = await fetch(`${this.baseUrl}/providers/${encodeURIComponent(providerKey)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `Failed to update provider: ${response.statusText}`);
    }
    return response.json();
  }

  async updateApiKey(providerKey: string, request: ApiKeyUpdateRequest): Promise<ApiKey> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(providerKey)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `Failed to update API key: ${response.statusText}`);
    }
    return response.json();
  }

  async deleteApiKey(providerKey: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(providerKey)}`, { method: 'DELETE' });
    if (!response.ok) {
      if (response.status === 404) throw new Error('API key not found');
      throw new Error(`Failed to delete API key: ${response.statusText}`);
    }
  }

  async deleteGenericProvider(providerKey: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/providers/${encodeURIComponent(providerKey)}`, { method: 'DELETE' });
    if (!response.ok) {
      throw new Error(`Failed to delete provider: ${response.statusText}`);
    }
  }

  async bulkUpdateApiKeys(request: ApiKeyBulkUpdateRequest): Promise<ApiKey[]> {
    const response = await fetch(`${this.baseUrl}/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      throw new Error(`Failed to bulk update API keys: ${response.statusText}`);
    }
    return response.json();
  }

  async deactivateProvider(providerKey: string): Promise<ApiKeySummary> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(providerKey)}/deactivate`, { method: 'PATCH' });
    if (!response.ok) {
      throw new Error(`Failed to deactivate provider: ${response.statusText}`);
    }
    return response.json();
  }

  async updateLastUsed(providerKey: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(providerKey)}/last-used`, { method: 'PATCH' });
    if (!response.ok) {
      throw new Error(`Failed to update last used timestamp: ${response.statusText}`);
    }
  }
}

export const apiKeysService = new ApiKeysService();
