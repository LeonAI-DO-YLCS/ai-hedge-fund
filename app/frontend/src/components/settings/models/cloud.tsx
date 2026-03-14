import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { clearModelsCache } from '@/data/models';
import { cn } from '@/lib/utils';
import { api, LanguageModelProviderResponse, ProviderInventoryResponse } from '@/services/api';
import { ChevronDown, ChevronRight, Cloud, Loader2, Plus, RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

interface CloudModelsProps {
  className?: string;
}

const normalizeSearchText = (value: string): string => {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
};

const matchesModelSearch = (query: string, displayName: string, modelName: string): boolean => {
  const normalizedQuery = normalizeSearchText(query);
  if (!normalizedQuery) {
    return true;
  }

  const tokens = normalizedQuery.split(' ');
  const searchTargets = [displayName, modelName]
    .map((value) => normalizeSearchText(value))
    .filter(Boolean);
  const combinedTarget = searchTargets.join(' ');

  return tokens.every((token) => combinedTarget.includes(token));
};

const compareInventoryItems = (
  left: ProviderInventoryResponse['inventory'][number],
  right: ProviderInventoryResponse['inventory'][number]
): number => {
  if (Boolean(left.is_enabled) !== Boolean(right.is_enabled)) {
    return left.is_enabled ? -1 : 1;
  }

  return left.display_name.localeCompare(right.display_name, undefined, {
    sensitivity: 'base',
    numeric: true,
  });
};

export function CloudModels({ className }: CloudModelsProps) {
  const [providers, setProviders] = useState<LanguageModelProviderResponse[]>([]);
  const [inventories, setInventories] = useState<Record<string, ProviderInventoryResponse>>({});
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [search, setSearch] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busyProvider, setBusyProvider] = useState<string | null>(null);
  const [customModelInputs, setCustomModelInputs] = useState<Record<string, string>>({});
  const [customErrors, setCustomErrors] = useState<Record<string, string | null>>({});

  const fetchProviders = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getLanguageModelProviders();
      setProviders(data.filter((provider) => provider.group !== 'retired'));
    } catch (fetchError) {
      console.error('Failed to fetch cloud model providers:', fetchError);
      setError('Failed to connect to backend service');
    }
    setLoading(false);
  };

  useEffect(() => {
    void fetchProviders();
  }, []);

  const visibleProviders = useMemo(
    () => providers.filter((provider) => provider.provider_kind !== 'retired'),
    [providers]
  );

  const openProvider = async (providerKey: string) => {
    setExpanded((prev) => ({ ...prev, [providerKey]: !prev[providerKey] }));
    if (expanded[providerKey] || inventories[providerKey]) return;
    try {
      const inventory = await api.getProviderInventory(providerKey);
      setInventories((prev) => ({ ...prev, [providerKey]: inventory }));
    } catch (fetchError) {
      console.error(`Failed to load inventory for ${providerKey}:`, fetchError);
      setCustomErrors((prev) => ({
        ...prev,
        [providerKey]: fetchError instanceof Error ? fetchError.message : 'Failed to load provider inventory.',
      }));
    }
  };

  const handleRefresh = async (providerKey: string) => {
    setBusyProvider(providerKey);
    try {
      await api.refreshProviderInventory(providerKey);
      const inventory = await api.getProviderInventory(providerKey);
      setInventories((prev) => ({ ...prev, [providerKey]: inventory }));
      clearModelsCache();
      await fetchProviders();
    } catch (refreshError) {
      console.error(`Failed to refresh models for ${providerKey}:`, refreshError);
      setCustomErrors((prev) => ({
        ...prev,
        [providerKey]: refreshError instanceof Error ? refreshError.message : 'Failed to refresh provider models.',
      }));
    } finally {
      setBusyProvider(null);
    }
  };

  const handleEnabledToggle = async (providerKey: string, modelName: string, checked: boolean) => {
    const currentInventory = inventories[providerKey];
    if (!currentInventory) return;
    const enabledModels = currentInventory.inventory
      .filter((item) => (item.is_enabled && item.model_name !== modelName) || (item.model_name === modelName && checked))
      .map((item) => item.model_name);

    setBusyProvider(providerKey);
    try {
      const updated = await api.updateEnabledModels(providerKey, enabledModels);
      setInventories((prev) => ({ ...prev, [providerKey]: updated }));
      clearModelsCache();
      await fetchProviders();
    } catch (toggleError) {
      setCustomErrors((prev) => ({
        ...prev,
        [providerKey]: toggleError instanceof Error ? toggleError.message : 'Failed to update enabled models.',
      }));
    } finally {
      setBusyProvider(null);
    }
  };

  const handleCustomModelSave = async (providerKey: string) => {
    const value = (customModelInputs[providerKey] || '').trim();
    if (!value) {
      setCustomErrors((prev) => ({ ...prev, [providerKey]: 'Enter a model name first.' }));
      return;
    }

    setBusyProvider(providerKey);
    setCustomErrors((prev) => ({ ...prev, [providerKey]: null }));
    try {
      const validation = await api.validateCustomModel(providerKey, value);
      if (!validation.valid) {
        setCustomErrors((prev) => ({ ...prev, [providerKey]: validation.error || 'Model is not accessible for this provider.' }));
        return;
      }
      await api.createCustomModel(providerKey, value, validation.model?.display_name || value);
      const inventory = await api.getProviderInventory(providerKey);
      setInventories((prev) => ({ ...prev, [providerKey]: inventory }));
      clearModelsCache();
      setCustomModelInputs((prev) => ({ ...prev, [providerKey]: '' }));
      await fetchProviders();
    } catch (customError) {
      console.error(`Failed to save custom model for ${providerKey}:`, customError);
      setCustomErrors((prev) => ({
        ...prev,
        [providerKey]: customError instanceof Error ? customError.message : 'Failed to save custom model.',
      }));
    } finally {
      setBusyProvider(null);
    }
  };

  return (
    <div className={cn('space-y-6', className)}>
      {error ? (
        <div className="rounded-lg border border-red-600/30 bg-red-900/20 p-4">
          <div className="flex items-start gap-3">
            <Cloud className="mt-0.5 h-5 w-5 text-red-500" />
            <div>
              <h4 className="font-medium text-red-300">Error</h4>
              <p className="mt-1 text-sm text-red-500">{error}</p>
            </div>
          </div>
        </div>
      ) : null}

      <div className="space-y-2">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-medium text-primary">Provider Inventories</h3>
          <span className="text-xs text-muted-foreground">
            {visibleProviders.reduce((sum, provider) => sum + (provider.enabled_model_count || 0), 0)} enabled models from {visibleProviders.length} providers
          </span>
        </div>

        {loading ? (
          <div className="py-8 text-center">
            <RefreshCw className="mx-auto mb-2 h-8 w-8 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Loading providers...</p>
          </div>
        ) : visibleProviders.length > 0 ? (
          <div className="space-y-4">
            {visibleProviders.map((provider) => {
              const providerKey = provider.provider_key || provider.provider;
              const inventory = inventories[providerKey];
               const query = search[providerKey] || '';
               const filteredInventory = (inventory?.inventory || [])
                 .filter((item) => matchesModelSearch(query, item.display_name, item.model_name))
                 .sort(compareInventoryItems);
               const isExpanded = !!expanded[providerKey];

              return (
                <div key={providerKey} className="space-y-3 rounded-lg border border-border/60 bg-muted/20 p-4">
                  <button className="flex w-full items-center justify-between gap-3 text-left" onClick={() => void openProvider(providerKey)}>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-primary">{provider.display_name || providerKey}</h4>
                        <Badge className="border-border bg-muted text-xs text-muted-foreground">{provider.status}</Badge>
                        {provider.source ? (
                          <Badge className="border-primary/30 bg-primary/10 text-xs text-primary">{provider.source}</Badge>
                        ) : null}
                      </div>
                      {provider.error ? <p className="mt-1 text-xs text-amber-500">{provider.error}</p> : null}
                      <p className="mt-1 text-xs text-muted-foreground">
                        {provider.enabled_model_count || 0} enabled / {provider.inventory_count || 0} known models
                      </p>
                    </div>
                    {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  </button>

                  {isExpanded ? (
                    <div className="space-y-3 border-t border-border/60 pt-3">
                      <div className="flex flex-wrap gap-2">
                        <Input
                          value={search[providerKey] || ''}
                          onChange={(event) => setSearch((prev) => ({ ...prev, [providerKey]: event.target.value }))}
                          placeholder="Search models by words or spaces"
                        />
                        <Button variant="outline" size="sm" onClick={() => void handleRefresh(providerKey)} disabled={busyProvider === providerKey}>
                          {busyProvider === providerKey ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
                          Refresh
                        </Button>
                      </div>

                      <div className="space-y-2">
                        {filteredInventory.length > 0 ? filteredInventory.map((model) => (
                          <label key={`${providerKey}-${model.model_name}`} className="flex items-center justify-between gap-3 rounded-md bg-muted px-3 py-2.5 transition-colors hover:bg-muted/80">
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2">
                                <input
                                  type="checkbox"
                                  checked={!!model.is_enabled}
                                  onChange={(event) => void handleEnabledToggle(providerKey, model.model_name, event.target.checked)}
                                />
                                <span className="truncate text-sm font-medium text-primary">{model.display_name}</span>
                                {model.model_name !== model.display_name ? <span className="font-mono text-xs text-muted-foreground">{model.model_name}</span> : null}
                              </div>
                              {model.status_reason ? <div className="mt-1 text-xs text-amber-400">{model.status_reason}</div> : null}
                            </div>
                            <div className="flex items-center gap-2">
                              {model.is_custom ? <Badge className="border-amber-500/30 bg-amber-500/10 text-xs text-amber-400">Manual</Badge> : null}
                              {model.availability_status ? <Badge className="border-border bg-panel text-xs text-muted-foreground">{model.availability_status}</Badge> : null}
                            </div>
                          </label>
                        )) : <div className="rounded-md border border-dashed border-border/70 p-4 text-sm text-muted-foreground">No models loaded for this provider yet.</div>}
                      </div>

                      <div className="flex flex-col gap-2 rounded-md border border-dashed border-border/70 p-3">
                        <div className="text-xs font-medium text-primary">Add Manual Model</div>
                        <div className="flex gap-2">
                          <Input
                            value={customModelInputs[providerKey] || ''}
                            onChange={(event) => setCustomModelInputs((prev) => ({ ...prev, [providerKey]: event.target.value }))}
                            placeholder="provider/model-name"
                          />
                          <Button size="sm" onClick={() => void handleCustomModelSave(providerKey)} disabled={busyProvider === providerKey}>
                            {busyProvider === providerKey ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                            Add
                          </Button>
                        </div>
                        {customErrors[providerKey] ? <p className="text-xs text-red-400">{customErrors[providerKey]}</p> : null}
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        ) : (
          !loading ? (
            <div className="py-8 text-center text-muted-foreground">
              <Cloud className="mx-auto mb-2 h-8 w-8 opacity-50" />
              <p className="text-sm">No provider inventory is available yet</p>
            </div>
          ) : null
        )}
      </div>
    </div>
  );
}
