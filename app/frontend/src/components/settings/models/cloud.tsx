import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { clearModelsCache } from '@/data/models';
import { cn } from '@/lib/utils';
import { api, LanguageModelProviderResponse } from '@/services/api';
import { Cloud, Loader2, Plus, RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

interface CloudModelsProps {
  className?: string;
}

export function CloudModels({ className }: CloudModelsProps) {
  const [providers, setProviders] = useState<LanguageModelProviderResponse[]>([]);
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
      setProviders(data);
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
    () => providers.filter((provider) => provider.type === 'local' || provider.available),
    [providers]
  );

  const handleRefresh = async (providerName: string) => {
    setBusyProvider(providerName);
    try {
      await api.discoverModels(providerName, true);
      clearModelsCache();
      await fetchProviders();
    } catch (refreshError) {
      console.error(`Failed to refresh models for ${providerName}:`, refreshError);
      setCustomErrors((prev) => ({
        ...prev,
        [providerName]: refreshError instanceof Error ? refreshError.message : 'Failed to refresh provider models.',
      }));
    } finally {
      setBusyProvider(null);
    }
  };

  const handleCustomModelSave = async (providerName: string) => {
    const value = (customModelInputs[providerName] || '').trim();
    if (!value) {
      setCustomErrors((prev) => ({ ...prev, [providerName]: 'Enter a model name first.' }));
      return;
    }

    setBusyProvider(providerName);
    setCustomErrors((prev) => ({ ...prev, [providerName]: null }));
    try {
      const validation = await api.validateCustomModel(providerName, value);
      if (!validation.valid) {
        setCustomErrors((prev) => ({ ...prev, [providerName]: validation.error || 'Model is not accessible for this provider.' }));
        return;
      }

      await api.createCustomModel(providerName, value, validation.model?.display_name || value);
      clearModelsCache();
      setCustomModelInputs((prev) => ({ ...prev, [providerName]: '' }));
      await fetchProviders();
    } catch (customError) {
      console.error(`Failed to save custom model for ${providerName}:`, customError);
      setCustomErrors((prev) => ({
        ...prev,
        [providerName]: customError instanceof Error ? customError.message : 'Failed to save custom model.',
      }));
    } finally {
      setBusyProvider(null);
    }
  };

  return (
    <div className={cn('space-y-6', className)}>
      {error && (
        <div className="bg-red-900/20 border border-red-600/30 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Cloud className="h-5 w-5 text-red-500 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-300">Error</h4>
              <p className="text-sm text-red-500 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-2">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-medium text-primary">Available Models</h3>
          <span className="text-xs text-muted-foreground">
            {visibleProviders.reduce((sum, provider) => sum + provider.models.length, 0)} models from {visibleProviders.length} providers
          </span>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Loading providers...</p>
          </div>
        ) : visibleProviders.length > 0 ? (
          <div className="space-y-4">
            {visibleProviders.map((provider) => (
              <div key={provider.name} className="rounded-lg border border-border/60 p-4 space-y-3 bg-muted/20">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-primary">{provider.name}</h4>
                      <Badge className="text-xs bg-muted text-muted-foreground border-border">{provider.status}</Badge>
                      {provider.source && (
                        <Badge className="text-xs bg-primary/10 text-primary border-primary/30">{provider.source}</Badge>
                      )}
                    </div>
                    {provider.error && <p className="text-xs text-amber-500 mt-1">{provider.error}</p>}
                  </div>
                  {provider.type === 'cloud' && provider.available && (
                    <Button variant="outline" size="sm" onClick={() => handleRefresh(provider.name)} disabled={busyProvider === provider.name}>
                      {busyProvider === provider.name ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
                      Refresh
                    </Button>
                  )}
                </div>

                <div className="space-y-1">
                  {provider.models.map((model) => (
                    <div key={`${provider.name}-${model.model_name}`} className="group flex items-center justify-between bg-muted hover-bg rounded-md px-3 py-2.5 transition-colors">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm truncate text-primary">{model.display_name}</span>
                          {model.model_name !== model.display_name && (
                            <span className="font-mono text-xs text-muted-foreground">{model.model_name}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {model.is_custom && <Badge className="text-xs bg-amber-500/10 text-amber-400 border-amber-500/30">Custom</Badge>}
                        <Badge className="text-xs text-primary bg-primary/10 border-primary/30 hover:bg-primary/20 hover:border-primary/50">{provider.name}</Badge>
                      </div>
                    </div>
                  ))}
                </div>

                {provider.type === 'cloud' && provider.available && (
                  <div className="flex flex-col gap-2 rounded-md border border-dashed border-border/70 p-3">
                    <div className="text-xs font-medium text-primary">Add Custom Model</div>
                    <div className="flex gap-2">
                      <Input
                        value={customModelInputs[provider.name] || ''}
                        onChange={(event) => setCustomModelInputs((prev) => ({ ...prev, [provider.name]: event.target.value }))}
                        placeholder="provider/model-name"
                      />
                      <Button size="sm" onClick={() => handleCustomModelSave(provider.name)} disabled={busyProvider === provider.name}>
                        {busyProvider === provider.name ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                        Validate
                      </Button>
                    </div>
                    {customErrors[provider.name] && <p className="text-xs text-red-400">{customErrors[provider.name]}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          !loading && (
            <div className="text-center py-8 text-muted-foreground">
              <Cloud className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No active provider models are available</p>
            </div>
          )
        )}
      </div>
    </div>
  );
}
