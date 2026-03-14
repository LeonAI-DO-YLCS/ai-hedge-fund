import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { clearModelsCache } from '@/data/models';
import {
  ApiKey,
  ApiKeySummary,
  apiKeysService,
  ConnectionMode,
  GenericProviderUpsertRequest,
} from '@/services/api-keys-api';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Eye,
  EyeOff,
  Key,
  Loader2,
  Plus,
  Trash2,
  XCircle,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

const CONNECTION_MODES: ConnectionMode[] = ['openai_compatible', 'anthropic_compatible', 'direct_http'];

type DetailMap = Record<string, ApiKey>;
type DraftMap = Record<string, string>;
type GenericDraftMap = Record<string, GenericProviderUpsertRequest>;

const STATUS_LABELS: Record<string, string> = {
  valid: 'Validated',
  invalid: 'Invalid',
  unverified: 'Unverified',
  unconfigured: 'Unconfigured',
  inactive: 'Inactive',
  disabled: 'Disabled',
  retired: 'Retired',
};

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === 'valid'
      ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'
      : status === 'invalid'
      ? 'text-red-400 border-red-500/30 bg-red-500/10'
      : status === 'unverified' || status === 'inactive'
      ? 'text-amber-400 border-amber-500/30 bg-amber-500/10'
      : 'text-muted-foreground border-border bg-muted/40';

  const Icon =
    status === 'valid'
      ? CheckCircle2
      : status === 'invalid'
      ? XCircle
      : status === 'unverified' || status === 'inactive'
      ? AlertTriangle
      : Key;

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] ${tone}`}>
      <Icon className="h-3 w-3" />
      {STATUS_LABELS[status] || status}
    </span>
  );
}

export function ApiKeysSettings() {
  const [providers, setProviders] = useState<ApiKeySummary[]>([]);
  const [details, setDetails] = useState<DetailMap>({});
  const [draftValues, setDraftValues] = useState<DraftMap>({});
  const [genericValues, setGenericValues] = useState<GenericDraftMap>({});
  const [visibleKeys, setVisibleKeys] = useState<Record<string, boolean>>({});
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [busyKeys, setBusyKeys] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});
  const [loading, setLoading] = useState(true);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [genericDraft, setGenericDraft] = useState<GenericProviderUpsertRequest>({
    display_name: '',
    connection_mode: 'openai_compatible',
    endpoint_url: '',
    models_url: '',
    key_value: '',
    is_active: true,
  });

  const loadProviders = async () => {
    setLoading(true);
    setGlobalError(null);
    try {
      const response = await apiKeysService.getAllApiKeys(true);
      setProviders(response);
    } catch (error) {
      console.error('Failed to load providers:', error);
      setGlobalError('Failed to load provider settings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadProviders();
  }, []);

  const groupedProviders = useMemo(() => {
    const groups: Record<string, ApiKeySummary[]> = {
      activated: [],
      inactive: [],
      disabled: [],
      unconfigured: [],
      retired: [],
    };
    providers.forEach((provider) => {
      const group = String(provider.group || 'unconfigured');
      groups[group] = groups[group] || [];
      groups[group].push(provider);
    });
    return groups;
  }, [providers]);

  const ensureDetail = async (providerKey: string) => {
    if (details[providerKey]) return details[providerKey];
    const detail = await apiKeysService.getApiKey(providerKey);
    setDetails((prev) => ({ ...prev, [providerKey]: detail }));
    setDraftValues((prev) => ({ ...prev, [providerKey]: detail.key_value || '' }));
    if (detail.provider_kind === 'generic') {
      setGenericValues((prev) => ({
        ...prev,
        [providerKey]: {
          provider_key: detail.provider_key || providerKey,
          display_name: detail.display_name || providerKey,
          provider_kind: 'generic',
          connection_mode: detail.connection_mode || 'openai_compatible',
          endpoint_url: detail.endpoint_url || '',
          models_url: detail.models_url || '',
          key_value: detail.key_value || '',
          request_defaults: detail.request_defaults || null,
          extra_headers: detail.extra_headers || null,
          is_active: detail.is_active,
        },
      }));
    }
    return detail;
  };

  const toggleExpanded = async (providerKey: string) => {
    setExpanded((prev) => ({ ...prev, [providerKey]: !prev[providerKey] }));
    if (!expanded[providerKey]) {
      try {
        await ensureDetail(providerKey);
      } catch (error) {
        setErrors((prev) => ({ ...prev, [providerKey]: error instanceof Error ? error.message : 'Failed to load provider details.' }));
      }
    }
  };

  const saveBuiltInProvider = async (provider: ApiKeySummary) => {
    const providerKey = provider.provider_key || provider.provider;
    const keyValue = (draftValues[providerKey] || '').trim();
    setBusyKeys((prev) => ({ ...prev, [providerKey]: true }));
    setErrors((prev) => ({ ...prev, [providerKey]: null }));
    try {
      if (!keyValue) {
        await apiKeysService.deleteApiKey(providerKey);
      } else {
        await apiKeysService.createOrUpdateApiKey({
          provider: providerKey,
          key_value: keyValue,
          is_active: true,
        });
      }
      clearModelsCache();
      setDetails((prev) => ({ ...prev, [providerKey]: undefined as never }));
      await loadProviders();
    } catch (error) {
      setErrors((prev) => ({ ...prev, [providerKey]: error instanceof Error ? error.message : 'Failed to save provider.' }));
    } finally {
      setBusyKeys((prev) => ({ ...prev, [providerKey]: false }));
    }
  };

  const deleteGenericProvider = async (providerKey: string) => {
    setBusyKeys((prev) => ({ ...prev, [providerKey]: true }));
    try {
      await apiKeysService.deleteGenericProvider(providerKey);
      clearModelsCache();
      await loadProviders();
    } catch (error) {
      setErrors((prev) => ({ ...prev, [providerKey]: error instanceof Error ? error.message : 'Failed to retire provider.' }));
    } finally {
      setBusyKeys((prev) => ({ ...prev, [providerKey]: false }));
    }
  };

  const createGenericProvider = async () => {
    setBusyKeys((prev) => ({ ...prev, generic: true }));
    setGlobalError(null);
    try {
      await apiKeysService.createGenericProvider(genericDraft);
      clearModelsCache();
      setGenericDraft({
        display_name: '',
        connection_mode: 'openai_compatible',
        endpoint_url: '',
        models_url: '',
        key_value: '',
        is_active: true,
      });
      await loadProviders();
    } catch (error) {
      setGlobalError(error instanceof Error ? error.message : 'Failed to create provider.');
    } finally {
      setBusyKeys((prev) => ({ ...prev, generic: false }));
    }
  };

  const saveGenericProvider = async (providerKey: string) => {
    const genericValue = genericValues[providerKey];
    if (!genericValue) {
      return;
    }
    setBusyKeys((prev) => ({ ...prev, [providerKey]: true }));
    setErrors((prev) => ({ ...prev, [providerKey]: null }));
    try {
      await apiKeysService.updateGenericProvider(providerKey, {
        ...genericValue,
        key_value: (draftValues[providerKey] || '').trim() || undefined,
      });
      clearModelsCache();
      setDetails((prev) => ({ ...prev, [providerKey]: undefined as never }));
      await loadProviders();
    } catch (error) {
      setErrors((prev) => ({
        ...prev,
        [providerKey]: error instanceof Error ? error.message : 'Failed to update provider.',
      }));
    } finally {
      setBusyKeys((prev) => ({ ...prev, [providerKey]: false }));
    }
  };

  const renderProviderCard = (provider: ApiKeySummary) => {
    const providerKey = provider.provider_key || provider.provider;
    const isExpanded = !!expanded[providerKey];
    const detail = details[providerKey];
    const draftValue = draftValues[providerKey] ?? detail?.key_value ?? '';
    const isGeneric = provider.provider_kind === 'generic';
    const genericValue = genericValues[providerKey];
    const busy = !!busyKeys[providerKey];

    return (
      <div key={providerKey} className="rounded-lg border border-border/60 bg-panel">
        <button
          className="flex w-full items-start justify-between gap-3 px-4 py-3 text-left"
          onClick={() => void toggleExpanded(providerKey)}
        >
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-primary">{provider.display_name || providerKey}</span>
              <StatusBadge status={String(provider.status || 'unconfigured')} />
              {provider.source && provider.source !== 'none' ? (
                <span className="text-[11px] text-muted-foreground">Source: {provider.source}</span>
              ) : null}
            </div>
            <div className="text-xs text-muted-foreground">
              {provider.enabled_model_count || 0} enabled / {provider.inventory_count || 0} known models
            </div>
            {provider.error ? <div className="text-xs text-amber-400">{provider.error}</div> : null}
          </div>
          {isExpanded ? <ChevronDown className="mt-0.5 h-4 w-4" /> : <ChevronRight className="mt-0.5 h-4 w-4" />}
        </button>

        {isExpanded ? (
          <div className="space-y-3 border-t border-border/60 px-4 py-3">
            {isGeneric && detail && genericValue ? (
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <Input
                  value={genericValue.display_name}
                  onChange={(event) => setGenericValues((prev) => ({
                    ...prev,
                    [providerKey]: { ...genericValue, display_name: event.target.value },
                  }))}
                  placeholder="Display name"
                />
                <select
                  className="h-10 rounded-md border border-border bg-node px-3 text-sm text-primary"
                  value={genericValue.connection_mode}
                  onChange={(event) => setGenericValues((prev) => ({
                    ...prev,
                    [providerKey]: { ...genericValue, connection_mode: event.target.value },
                  }))}
                >
                  {CONNECTION_MODES.map((mode) => (
                    <option key={mode} value={mode}>{mode}</option>
                  ))}
                </select>
                <Input
                  value={genericValue.endpoint_url || ''}
                  onChange={(event) => setGenericValues((prev) => ({
                    ...prev,
                    [providerKey]: { ...genericValue, endpoint_url: event.target.value },
                  }))}
                  placeholder="Endpoint URL"
                />
                <Input
                  value={genericValue.models_url || ''}
                  onChange={(event) => setGenericValues((prev) => ({
                    ...prev,
                    [providerKey]: { ...genericValue, models_url: event.target.value },
                  }))}
                  placeholder="Models URL"
                />
              </div>
            ) : null}

            <div className="relative">
              <Input
                type={visibleKeys[providerKey] ? 'text' : 'password'}
                placeholder="Provider key"
                value={draftValue}
                onChange={(event) => setDraftValues((prev) => ({ ...prev, [providerKey]: event.target.value }))}
                className="pr-20"
              />
              <div className="absolute right-1 top-1/2 flex -translate-y-1/2 items-center gap-1">
                {draftValue ? (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 hover:bg-red-500/10 hover:text-red-500"
                    onClick={() => setDraftValues((prev) => ({ ...prev, [providerKey]: '' }))}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                ) : null}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => setVisibleKeys((prev) => ({ ...prev, [providerKey]: !prev[providerKey] }))}
                >
                  {visibleKeys[providerKey] ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                </Button>
              </div>
            </div>

            {errors[providerKey] ? <p className="text-xs text-red-400">{errors[providerKey]}</p> : null}

            <div className="flex flex-wrap gap-2">
              {!isGeneric ? (
                <Button size="sm" onClick={() => void saveBuiltInProvider(provider)} disabled={busy}>
                  {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Save & Validate
                </Button>
              ) : null}
              {isGeneric ? (
                <Button size="sm" onClick={() => void saveGenericProvider(providerKey)} disabled={busy}>
                  {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Save Changes
                </Button>
              ) : null}
              {isGeneric ? (
                <Button variant="outline" size="sm" onClick={() => void deleteGenericProvider(providerKey)} disabled={busy}>
                  {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Retire Provider
                </Button>
              ) : null}
              {provider.last_validated_at ? (
                <span className="text-[11px] text-muted-foreground">
                  Last checked: {new Date(provider.last_validated_at).toLocaleString()}
                </span>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>
    );
  };

  const renderGroup = (title: string, items: ApiKeySummary[]) => {
    if (items.length === 0) return null;
    return (
      <Card className="border-gray-700 bg-panel dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-medium text-primary">
            <Key className="h-4 w-4" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">{items.map(renderProviderCard)}</CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="mb-2 text-xl font-semibold text-primary">Providers</h2>
        <p className="text-sm text-muted-foreground">
          Activated providers stay at the top, unused providers stay collapsed, and generic providers join the same workflow.
        </p>
      </div>

      {globalError ? (
        <div className="rounded-lg border border-red-600/30 bg-red-900/20 p-4 text-sm text-red-300">{globalError}</div>
      ) : null}

      <Card className="border-gray-700 bg-panel dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-medium text-primary">
            <Plus className="h-4 w-4" />
            Add Generic Provider
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Input
            placeholder="Display name"
            value={genericDraft.display_name}
            onChange={(event) => setGenericDraft((prev) => ({ ...prev, display_name: event.target.value }))}
          />
          <select
            className="h-10 rounded-md border border-border bg-node px-3 text-sm text-primary"
            value={genericDraft.connection_mode}
            onChange={(event) => setGenericDraft((prev) => ({ ...prev, connection_mode: event.target.value }))}
          >
            {CONNECTION_MODES.map((mode) => (
              <option key={mode} value={mode}>{mode}</option>
            ))}
          </select>
          <Input
            placeholder="Endpoint URL"
            value={genericDraft.endpoint_url || ''}
            onChange={(event) => setGenericDraft((prev) => ({ ...prev, endpoint_url: event.target.value }))}
          />
          <Input
            placeholder="Models URL"
            value={genericDraft.models_url || ''}
            onChange={(event) => setGenericDraft((prev) => ({ ...prev, models_url: event.target.value }))}
          />
          <Input
            placeholder="API key"
            value={genericDraft.key_value || ''}
            onChange={(event) => setGenericDraft((prev) => ({ ...prev, key_value: event.target.value }))}
          />
          <div className="flex items-center">
            <Button onClick={() => void createGenericProvider()} disabled={!!busyKeys.generic}>
              {busyKeys.generic ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Create Provider
            </Button>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="rounded-lg border border-border/60 bg-panel p-6 text-sm text-muted-foreground">Loading provider settings...</div>
      ) : (
        <div className="space-y-6">
          {renderGroup('Activated Providers', groupedProviders.activated)}
          {renderGroup('Inactive Providers', groupedProviders.inactive)}
          {renderGroup('Disabled Providers', groupedProviders.disabled)}
          {renderGroup('Unconfigured Providers', groupedProviders.unconfigured)}
          {renderGroup('Retired Providers', groupedProviders.retired)}
        </div>
      )}
    </div>
  );
}
