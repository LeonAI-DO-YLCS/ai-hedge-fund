import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { clearModelsCache } from '@/data/models';
import { ApiKeyStatus, ApiKeySummary, apiKeysService } from '@/services/api-keys-api';
import { AlertTriangle, CheckCircle2, Eye, EyeOff, Key, Loader2, Trash2, XCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

interface ApiKeyField {
  key: string;
  label: string;
  description: string;
  url: string;
  placeholder: string;
  requiresValidation?: boolean;
}

const FINANCIAL_API_KEYS: ApiKeyField[] = [
  {
    key: 'FINANCIAL_DATASETS_API_KEY',
    label: 'Financial Datasets API',
    description: 'For getting financial data to power the hedge fund',
    url: 'https://financialdatasets.ai/',
    placeholder: 'your-financial-datasets-api-key',
    requiresValidation: false,
  },
];

const LLM_API_KEYS: ApiKeyField[] = [
  { key: 'ANTHROPIC_API_KEY', label: 'Anthropic API', description: 'For Claude models', url: 'https://anthropic.com/', placeholder: 'your-anthropic-api-key', requiresValidation: true },
  { key: 'DEEPSEEK_API_KEY', label: 'DeepSeek API', description: 'For DeepSeek models', url: 'https://deepseek.com/', placeholder: 'your-deepseek-api-key', requiresValidation: true },
  { key: 'GROQ_API_KEY', label: 'Groq API', description: 'For Groq-hosted models', url: 'https://groq.com/', placeholder: 'your-groq-api-key', requiresValidation: true },
  { key: 'GOOGLE_API_KEY', label: 'Google API', description: 'For Gemini models', url: 'https://ai.dev/', placeholder: 'your-google-api-key', requiresValidation: true },
  { key: 'OPENAI_API_KEY', label: 'OpenAI API', description: 'For OpenAI models', url: 'https://platform.openai.com/', placeholder: 'your-openai-api-key', requiresValidation: true },
  { key: 'OPENROUTER_API_KEY', label: 'OpenRouter API', description: 'For router and aggregator models', url: 'https://openrouter.ai/', placeholder: 'your-openrouter-api-key', requiresValidation: true },
  { key: 'XAI_API_KEY', label: 'xAI API', description: 'For Grok models', url: 'https://x.ai/', placeholder: 'your-xai-api-key', requiresValidation: true },
  { key: 'GIGACHAT_API_KEY', label: 'GigaChat API', description: 'For GigaChat models', url: 'https://github.com/ai-forever/gigachat', placeholder: 'your-gigachat-api-key', requiresValidation: true },
  { key: 'AZURE_OPENAI_API_KEY', label: 'Azure OpenAI API', description: 'For Azure OpenAI deployments', url: 'https://azure.microsoft.com/', placeholder: 'your-azure-openai-api-key', requiresValidation: true },
];

type StatusMap = Record<string, ApiKeyStatus | string>;
type SummaryMap = Record<string, ApiKeySummary>;

const STATUS_LABELS: Record<string, string> = {
  valid: 'Validated',
  invalid: 'Invalid',
  unverified: 'Unverified',
  unconfigured: 'Unconfigured',
  unsaved: 'Unsaved changes',
  unavailable: 'Unavailable',
};

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === 'valid'
      ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'
      : status === 'invalid'
      ? 'text-red-400 border-red-500/30 bg-red-500/10'
      : status === 'unverified' || status === 'unsaved'
      ? 'text-amber-400 border-amber-500/30 bg-amber-500/10'
      : 'text-muted-foreground border-border bg-muted/40';

  const Icon =
    status === 'valid'
      ? CheckCircle2
      : status === 'invalid'
      ? XCircle
      : status === 'unverified' || status === 'unsaved'
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
  const [draftValues, setDraftValues] = useState<Record<string, string>>({});
  const [savedValues, setSavedValues] = useState<Record<string, string>>({});
  const [summaries, setSummaries] = useState<SummaryMap>({});
  const [statuses, setStatuses] = useState<StatusMap>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});
  const [visibleKeys, setVisibleKeys] = useState<Record<string, boolean>>({});
  const [busyKeys, setBusyKeys] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [globalError, setGlobalError] = useState<string | null>(null);

  const allFields = useMemo(() => [...FINANCIAL_API_KEYS, ...LLM_API_KEYS], []);

  useEffect(() => {
    void loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      setLoading(true);
      setGlobalError(null);
      const apiKeySummaries = await apiKeysService.getAllApiKeys(true);
      const summaryMap: SummaryMap = {};
      const initialDrafts: Record<string, string> = {};
      const initialSaved: Record<string, string> = {};
      const initialStatuses: StatusMap = {};

      for (const field of allFields) {
        const summary = apiKeySummaries.find((item) => item.provider === field.key);
        if (summary) {
          summaryMap[field.key] = summary;
          initialStatuses[field.key] = summary.status || 'unconfigured';
          if (summary.has_stored_key) {
            try {
              const fullKey = await apiKeysService.getApiKey(field.key);
              initialDrafts[field.key] = fullKey.key_value;
              initialSaved[field.key] = fullKey.key_value;
            } catch (error) {
              console.warn(`Failed to load key for ${field.key}:`, error);
              initialDrafts[field.key] = '';
              initialSaved[field.key] = '';
            }
          } else {
            initialDrafts[field.key] = '';
            initialSaved[field.key] = '';
          }
        } else {
          initialStatuses[field.key] = 'unconfigured';
          initialDrafts[field.key] = '';
          initialSaved[field.key] = '';
        }
      }

      setSummaries(summaryMap);
      setDraftValues(initialDrafts);
      setSavedValues(initialSaved);
      setStatuses(initialStatuses);
    } catch (error) {
      console.error('Failed to load API keys:', error);
      setGlobalError('Failed to load API keys. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleKeyVisibility = (key: string) => {
    setVisibleKeys((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const setBusy = (key: string, value: boolean) => {
    setBusyKeys((prev) => ({ ...prev, [key]: value }));
  };

  const handleDraftChange = (key: string, value: string) => {
    setDraftValues((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => ({ ...prev, [key]: null }));
    const savedValue = savedValues[key] || '';
    setStatuses((prev) => ({
      ...prev,
      [key]: value.trim() === savedValue.trim() ? (summaries[key]?.status || 'unconfigured') : 'unsaved',
    }));
  };

  const saveFinancialKey = async (field: ApiKeyField) => {
    const rawValue = draftValues[field.key] || '';
    const trimmedValue = rawValue.trim();
    setBusy(field.key, true);
    setErrors((prev) => ({ ...prev, [field.key]: null }));
    try {
      if (!trimmedValue) {
        await apiKeysService.deleteApiKey(field.key);
        setSavedValues((prev) => ({ ...prev, [field.key]: '' }));
        setStatuses((prev) => ({ ...prev, [field.key]: 'unconfigured' }));
        return;
      }

      await apiKeysService.createOrUpdateApiKey({
        provider: field.key,
        key_value: trimmedValue,
        is_active: true,
      });
      setSavedValues((prev) => ({ ...prev, [field.key]: trimmedValue }));
      setStatuses((prev) => ({ ...prev, [field.key]: 'valid' }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save API key.';
      setErrors((prev) => ({ ...prev, [field.key]: message }));
      setStatuses((prev) => ({ ...prev, [field.key]: 'invalid' }));
    } finally {
      setBusy(field.key, false);
    }
  };

  const saveAndValidateKey = async (field: ApiKeyField) => {
    const rawValue = draftValues[field.key] || '';
    const trimmedValue = rawValue.trim();

    setBusy(field.key, true);
    setErrors((prev) => ({ ...prev, [field.key]: null }));
    try {
      if (!trimmedValue) {
        await apiKeysService.deleteApiKey(field.key);
        clearModelsCache();
        setSavedValues((prev) => ({ ...prev, [field.key]: '' }));
        setStatuses((prev) => ({ ...prev, [field.key]: 'unconfigured' }));
        await loadApiKeys();
        return;
      }

      const validation = await apiKeysService.validateApiKey(field.key, trimmedValue);
      if (validation.status === 'invalid') {
        setStatuses((prev) => ({ ...prev, [field.key]: 'invalid' }));
        setErrors((prev) => ({ ...prev, [field.key]: validation.error || 'Provider rejected this key.' }));
        return;
      }

      await apiKeysService.createOrUpdateApiKey({
        provider: field.key,
        key_value: trimmedValue,
        is_active: true,
        validation_status: validation.status,
        validation_error: validation.error,
        last_validated_at: validation.checked_at,
        last_validation_latency_ms: validation.latency_ms,
      });

      clearModelsCache();
      setSavedValues((prev) => ({ ...prev, [field.key]: trimmedValue }));
      setStatuses((prev) => ({ ...prev, [field.key]: validation.status }));
      await loadApiKeys();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save API key.';
      setErrors((prev) => ({ ...prev, [field.key]: message }));
      setStatuses((prev) => ({ ...prev, [field.key]: 'invalid' }));
    } finally {
      setBusy(field.key, false);
    }
  };

  const clearKey = async (field: ApiKeyField) => {
    setBusy(field.key, true);
    try {
      await apiKeysService.deleteApiKey(field.key);
      clearModelsCache();
      setDraftValues((prev) => ({ ...prev, [field.key]: '' }));
      setSavedValues((prev) => ({ ...prev, [field.key]: '' }));
      setStatuses((prev) => ({ ...prev, [field.key]: 'unconfigured' }));
      setErrors((prev) => ({ ...prev, [field.key]: null }));
      await loadApiKeys();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete API key.';
      setErrors((prev) => ({ ...prev, [field.key]: message }));
    } finally {
      setBusy(field.key, false);
    }
  };

  const renderApiKeySection = (title: string, description: string, keys: ApiKeyField[]) => (
    <Card className="bg-panel border-gray-700 dark:border-gray-700">
      <CardHeader>
        <CardTitle className="text-lg font-medium text-primary flex items-center gap-2">
          <Key className="h-4 w-4" />
          {title}
        </CardTitle>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardHeader>
      <CardContent className="space-y-5">
        {keys.map((field) => {
          const status = statuses[field.key] || 'unconfigured';
          const isBusy = !!busyKeys[field.key];
          const summary = summaries[field.key];
          return (
            <div key={field.key} className="space-y-2 rounded-lg border border-border/60 p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <button
                    className="text-sm font-medium text-primary hover:text-blue-500 cursor-pointer transition-colors text-left"
                    onClick={() => window.open(field.url, '_blank')}
                  >
                    {field.label}
                  </button>
                  <p className="text-xs text-muted-foreground">{field.description}</p>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge status={status} />
                    {summary?.source && summary.source !== 'none' && (
                      <span className="text-[11px] text-muted-foreground">Source: {summary.source}</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="relative">
                <Input
                  type={visibleKeys[field.key] ? 'text' : 'password'}
                  placeholder={field.placeholder}
                  value={draftValues[field.key] || ''}
                  onChange={(e) => handleDraftChange(field.key, e.target.value)}
                  className="pr-20"
                />
                <div className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  {!!draftValues[field.key] && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 hover:bg-red-500/10 hover:text-red-500"
                      onClick={() => clearKey(field)}
                      disabled={isBusy}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => toggleKeyVisibility(field.key)}
                  >
                    {visibleKeys[field.key] ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                  </Button>
                </div>
              </div>

              {errors[field.key] && <p className="text-xs text-red-400">{errors[field.key]}</p>}
              {status === 'unverified' && !errors[field.key] && (
                <p className="text-xs text-amber-400">Provider could not be verified. The key is saved and will be retried later.</p>
              )}

              <div className="flex flex-wrap items-center gap-2">
                <Button
                  size="sm"
                  onClick={() => (field.requiresValidation ? saveAndValidateKey(field) : saveFinancialKey(field))}
                  disabled={isBusy}
                >
                  {isBusy ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : field.requiresValidation ? (
                    'Save & Validate'
                  ) : (
                    'Save'
                  )}
                </Button>
                {summary?.last_validated_at && (
                  <span className="text-[11px] text-muted-foreground">
                    Last checked: {new Date(summary.last_validated_at).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-primary mb-2">API Keys</h2>
          <p className="text-sm text-muted-foreground">Loading API keys...</p>
        </div>
        <Card className="bg-panel border-gray-700 dark:border-gray-700">
          <CardContent className="p-6 text-sm text-muted-foreground">Please wait while we load your API keys...</CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-primary mb-2">API Keys</h2>
        <p className="text-sm text-muted-foreground">
          Configure provider credentials with explicit Save & Validate steps. Unsaved edits stay local until you confirm them.
        </p>
      </div>

      {globalError && (
        <Card className="bg-red-500/5 border-red-500/20">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Key className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
              <div className="space-y-1">
                <h4 className="text-sm font-medium text-red-500">Error</h4>
                <p className="text-xs text-muted-foreground">{globalError}</p>
                <Button variant="ghost" size="sm" onClick={() => void loadApiKeys()} className="text-xs mt-2 p-0 h-auto text-red-500 hover:text-red-400">
                  Try again
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {renderApiKeySection('Financial Data', 'API keys for accessing financial market data and datasets.', FINANCIAL_API_KEYS)}
      {renderApiKeySection('Language Models', 'API keys for accessing large language model providers.', LLM_API_KEYS)}

      <Card className="bg-amber-500/5 border-amber-500/20">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Key className="h-5 w-5 text-amber-500 mt-0.5 flex-shrink-0" />
            <div className="space-y-1">
              <h4 className="text-sm font-medium text-amber-500">Security Note</h4>
              <p className="text-xs text-muted-foreground">
                API keys are stored locally for this workspace. Save actions are explicit, and provider model caches refresh after key changes.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
