import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LanguageModel } from '@/data/models';
import { api, LanguageModelProviderResponse } from '@/services/api';
import { RefreshCw, Server } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

export function LMStudioSettings() {
  const [provider, setProvider] = useState<LanguageModelProviderResponse | null>(null);
  const [models, setModels] = useState<LanguageModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const [providers, allModels] = await Promise.all([
        api.getLanguageModelProviders(),
        api.getLanguageModels(),
      ]);
      const lmstudio = providers.find((p) => p.provider_key === 'lmstudio' || p.display_name === 'LMStudio') || null;
      setProvider(lmstudio);
      setModels(allModels.filter((m) => m.provider === 'LMStudio'));
      setError(null);
    } catch (err) {
      console.error('Failed loading LMStudio settings:', err);
      setError('Failed to load LMStudio provider data');
    } finally {
      setLoading(false);
      if (isManual) setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-primary">LMStudio</h3>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refresh(true)}
          disabled={refreshing}
          className="gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <div className="rounded-lg border border-border bg-muted p-4 space-y-2">
        <div className="flex items-center gap-2">
          <Server className="h-4 w-4 text-blue-400" />
          <span className="font-medium">Provider Status:</span>
          <Badge className="text-xs bg-muted text-muted-foreground border-border">
            {provider?.status || 'unknown'}
          </Badge>
        </div>
        <div className="text-sm">
          <span className="text-muted-foreground">Available:</span>{' '}
          {provider?.available ? 'Yes' : 'No'}
        </div>
        <div className="text-sm">
          <span className="text-muted-foreground">Last Checked:</span>{' '}
          {provider?.last_checked_at || '—'}
        </div>
        {(provider?.error || error) && (
          <p className="text-sm text-yellow-500">{provider?.error || error}</p>
        )}
      </div>

      <div className="rounded-lg border border-border bg-muted p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-primary">LMStudio Models</h4>
          <span className="text-xs text-muted-foreground">{models.length} models</span>
        </div>

        {loading ? (
          <p className="text-sm text-muted-foreground">Loading LMStudio models...</p>
        ) : models.length ? (
          <div className="space-y-2 max-h-72 overflow-auto">
            {models.map((model) => (
              <div key={model.model_name} className="rounded border border-border px-3 py-2 bg-panel">
                <p className="text-sm font-medium text-primary">{model.display_name}</p>
                <p className="text-xs text-muted-foreground font-mono">{model.model_name}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            {provider?.available
              ? 'No LMStudio models currently reported.'
              : 'LMStudio unavailable. Start LMStudio and refresh.'}
          </p>
        )}
      </div>
    </div>
  );
}
