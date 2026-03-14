import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ModelSelector } from '@/components/ui/llm-selector';
import {
  createModelIdentity,
  findModelByIdentity,
  getModelIdentity,
  getModels,
  LanguageModel,
} from '@/data/models';
import { cn } from '@/lib/utils';
import {
  agentConfigApi,
  AgentConfigurationDetail,
  AgentConfigurationEffective,
  AgentConfigurationSummary,
} from '@/services/agent-config-api';
import { RefreshCw, Settings2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

interface AgentsSettingsProps {
  className?: string;
}

type DraftMap = Record<string, AgentConfigurationEffective>;

const toDraft = (detail: AgentConfigurationDetail): AgentConfigurationEffective => ({
  ...detail.effective,
});

const formatSource = (source?: string | null): string => {
  switch (source) {
    case 'persisted_override':
      return 'Saved override';
    case 'default_plus_append':
      return 'Default + append';
    case 'provider_default':
      return 'Auto (provider default)';
    case 'auto':
      return 'Auto';
    case 'default':
      return 'Default';
    default:
      return source ? source.replace(/_/g, ' ') : 'Default';
  }
};

export function AgentsSettings({ className }: AgentsSettingsProps) {
  const [agents, setAgents] = useState<AgentConfigurationSummary[]>([]);
  const [models, setModels] = useState<LanguageModel[]>([]);
  const [details, setDetails] = useState<Record<string, AgentConfigurationDetail>>({});
  const [drafts, setDrafts] = useState<DraftMap>({});
  const [openAgents, setOpenAgents] = useState<string[]>([]);
  const [showDefaults, setShowDefaults] = useState<Record<string, boolean>>({});
  const [detailLoading, setDetailLoading] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [applyAllModel, setApplyAllModel] = useState<LanguageModel | null>(null);

  const loadSummaries = async () => {
    const configs = await agentConfigApi.getAll();
    setAgents(configs);
  };

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [configs, availableModels] = await Promise.all([loadSummaries(), getModels()]);
      await configs;
      setModels(availableModels);
    } catch (fetchError) {
      console.error('Failed to load agent settings:', fetchError);
      setError('Failed to load agent settings.');
    } finally {
      setLoading(false);
    }
  };

  const ensureDetail = async (agentKey: string, force = false) => {
    if (!force && details[agentKey]) {
      return details[agentKey];
    }

    setDetailLoading((prev) => ({ ...prev, [agentKey]: true }));
    try {
      const detail = await agentConfigApi.getOne(agentKey);
      setDetails((prev) => ({ ...prev, [agentKey]: detail }));
      setDrafts((prev) => ({ ...prev, [agentKey]: toDraft(detail) }));
      return detail;
    } finally {
      setDetailLoading((prev) => ({ ...prev, [agentKey]: false }));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const orderedAgents = useMemo(
    () => [...agents].sort((a, b) => a.display_name.localeCompare(b.display_name)),
    [agents]
  );

  const getDraft = (agentKey: string): AgentConfigurationEffective | null => drafts[agentKey] || null;

  const updateDraft = (agentKey: string, patch: Partial<AgentConfigurationEffective>) => {
    const currentDraft = getDraft(agentKey);
    if (!currentDraft) {
      return;
    }
    setDrafts((prev) => ({
      ...prev,
      [agentKey]: {
        ...currentDraft,
        ...patch,
      },
    }));
  };

  const handleAccordionChange = (values: string[]) => {
    setOpenAgents(values);
    values.forEach((agentKey) => {
      if (!details[agentKey] && !detailLoading[agentKey]) {
        void ensureDetail(agentKey);
      }
    });
  };

  const handleSave = async (agentKey: string) => {
    const draft = getDraft(agentKey);
    if (!draft) {
      return;
    }

    setBusyKey(agentKey);
    try {
      const updated = await agentConfigApi.update(agentKey, { effective: draft });
      setDetails((prev) => ({ ...prev, [agentKey]: updated }));
      setDrafts((prev) => ({ ...prev, [agentKey]: toDraft(updated) }));
      await loadSummaries();
    } catch (saveError) {
      console.error(`Failed to save agent config for ${agentKey}:`, saveError);
      setError(saveError instanceof Error ? saveError.message : 'Failed to save agent config.');
    } finally {
      setBusyKey(null);
    }
  };

  const handleReset = async (agentKey: string) => {
    setBusyKey(agentKey);
    try {
      await agentConfigApi.reset(agentKey);
      await loadSummaries();
      const detail = await ensureDetail(agentKey, true);
      setDrafts((prev) => ({ ...prev, [agentKey]: toDraft(detail) }));
    } catch (resetError) {
      console.error(`Failed to reset agent config for ${agentKey}:`, resetError);
      setError(resetError instanceof Error ? resetError.message : 'Failed to reset agent config.');
    } finally {
      setBusyKey(null);
    }
  };

  const handleApplyToAll = async () => {
    if (!applyAllModel) {
      return;
    }
    setBusyKey('all');
    try {
      await agentConfigApi.applyToAll({
        model_name: applyAllModel.model_name,
        model_provider: applyAllModel.provider,
      });
      await loadSummaries();
      await Promise.all(openAgents.map((agentKey) => ensureDetail(agentKey, true)));
    } catch (applyError) {
      console.error('Failed to apply model to all agents:', applyError);
      setError(applyError instanceof Error ? applyError.message : 'Failed to apply settings to all agents.');
    } finally {
      setBusyKey(null);
    }
  };

  return (
    <div className={cn('space-y-6', className)}>
      <div>
        <h2 className="mb-2 text-xl font-semibold text-primary">Agents</h2>
        <p className="text-sm text-muted-foreground">
          Review each agent&apos;s live prompt baseline, model selection, and runtime parameters before saving targeted overrides.
        </p>
      </div>

      {error && (
        <Card className="border-red-500/20 bg-red-500/5">
          <CardContent className="p-4 text-sm text-red-400">{error}</CardContent>
        </Card>
      )}

      <Card className="border-gray-700 bg-panel dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-medium text-primary">
            <Settings2 className="h-4 w-4" />
            Apply to All
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <ModelSelector
            models={models}
            value={applyAllModel ? getModelIdentity(applyAllModel) : ''}
            onChange={setApplyAllModel}
            placeholder="Choose a shared model"
          />
          <Button onClick={() => void handleApplyToAll()} disabled={!applyAllModel || busyKey === 'all'}>
            {busyKey === 'all' ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : null}
            Apply Model to All Agents
          </Button>
        </CardContent>
      </Card>

      {loading ? (
        <Card className="border-gray-700 bg-panel dark:border-gray-700">
          <CardContent className="p-6 text-sm text-muted-foreground">Loading agent settings...</CardContent>
        </Card>
      ) : (
        <Accordion type="multiple" className="space-y-3" value={openAgents} onValueChange={handleAccordionChange}>
          {orderedAgents.map((agent) => {
            const detail = details[agent.agent_key];
            const draft = getDraft(agent.agent_key);
            const selectedModel = draft
              ? findModelByIdentity(models, draft.model_name, draft.model_provider as string | null)
              : null;
            const fallbackModel = draft
              ? findModelByIdentity(models, draft.fallback_model_name, draft.fallback_model_provider as string | null)
              : null;

            return (
              <AccordionItem
                key={agent.agent_key}
                value={agent.agent_key}
                className="rounded-lg border border-border bg-panel px-4"
              >
                <AccordionTrigger className="hover:no-underline">
                  <div className="space-y-1 text-left">
                    <div className="font-medium text-primary">{agent.display_name}</div>
                    <div className="text-xs text-muted-foreground">{agent.description}</div>
                    <div className="flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                      <span>{agent.has_customizations ? 'Customized' : 'Using defaults'}</span>
                      {agent.warnings.length > 0 ? <span>{agent.warnings.length} warning(s)</span> : null}
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-4 pb-4">
                  {!detail || !draft ? (
                    <div className="text-sm text-muted-foreground">
                      {detailLoading[agent.agent_key] ? 'Loading agent baseline...' : 'Open to load agent details.'}
                    </div>
                  ) : (
                    <>
                      <div className="rounded-md border border-border bg-node/60 p-3 text-xs text-muted-foreground">
                        <div>Prompt source: {formatSource(detail.sources.system_prompt_text)}</div>
                        <div>Temperature: {formatSource(detail.sources.temperature)}</div>
                        <div>Max tokens: {formatSource(detail.sources.max_tokens)}</div>
                        <div>Top P: {formatSource(detail.sources.top_p)}</div>
                        {detail.warnings.map((warning) => (
                          <div key={warning} className="text-amber-400">
                            {warning}
                          </div>
                        ))}
                      </div>

                      <div className="space-y-2">
                        <div className="text-xs font-medium text-primary">Primary Model</div>
                        <ModelSelector
                          models={models}
                          value={selectedModel
                            ? getModelIdentity(selectedModel)
                            : createModelIdentity(draft.model_name, draft.model_provider as string | null)}
                          onChange={(model) =>
                            updateDraft(agent.agent_key, {
                              model_name: model?.model_name || null,
                              model_provider: model?.provider || null,
                            })
                          }
                          placeholder="Auto"
                        />
                      </div>

                      <div className="space-y-2">
                        <div className="text-xs font-medium text-primary">Fallback Model</div>
                        <ModelSelector
                          models={models}
                          value={fallbackModel
                            ? getModelIdentity(fallbackModel)
                            : createModelIdentity(draft.fallback_model_name, draft.fallback_model_provider as string | null)}
                          onChange={(model) =>
                            updateDraft(agent.agent_key, {
                              fallback_model_name: model?.model_name || null,
                              fallback_model_provider: model?.provider || null,
                            })
                          }
                          placeholder="Optional fallback"
                        />
                        {draft.model_provider &&
                        draft.fallback_model_provider &&
                        draft.model_provider === draft.fallback_model_provider ? (
                          <p className="text-xs text-amber-400">
                            Fallback uses the same provider as the primary model.
                          </p>
                        ) : null}
                      </div>

                      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                        <div className="space-y-1">
                          <Input
                            placeholder="Auto (provider default)"
                            value={draft.temperature ?? ''}
                            onChange={(event) =>
                              updateDraft(agent.agent_key, {
                                temperature: event.target.value === '' ? null : Number(event.target.value),
                              })
                            }
                          />
                          <p className="text-[11px] text-muted-foreground">{formatSource(detail.sources.temperature)}</p>
                        </div>
                        <div className="space-y-1">
                          <Input
                            placeholder="Auto (provider default)"
                            value={draft.max_tokens ?? ''}
                            onChange={(event) =>
                              updateDraft(agent.agent_key, {
                                max_tokens: event.target.value === '' ? null : Number(event.target.value),
                              })
                            }
                          />
                          <p className="text-[11px] text-muted-foreground">{formatSource(detail.sources.max_tokens)}</p>
                        </div>
                        <div className="space-y-1">
                          <Input
                            placeholder="Auto (provider default)"
                            value={draft.top_p ?? ''}
                            onChange={(event) =>
                              updateDraft(agent.agent_key, {
                                top_p: event.target.value === '' ? null : Number(event.target.value),
                              })
                            }
                          />
                          <p className="text-[11px] text-muted-foreground">{formatSource(detail.sources.top_p)}</p>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="text-xs font-medium text-primary">Prompt Mode</div>
                        <div className="flex flex-wrap gap-2">
                          {(['default', 'append', 'override'] as const).map((mode) => (
                            <Button
                              key={mode}
                              type="button"
                              size="sm"
                              variant={draft.prompt_mode === mode ? 'default' : 'outline'}
                              onClick={() =>
                                updateDraft(agent.agent_key, {
                                  prompt_mode: mode,
                                  system_prompt_text:
                                    mode === 'default'
                                      ? detail.defaults.system_prompt_text
                                      : draft.system_prompt_text,
                                })
                              }
                            >
                              {mode === 'default' ? 'Auto' : mode === 'append' ? 'Append' : 'Override'}
                            </Button>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="text-xs font-medium text-primary">Effective Prompt</div>
                        <textarea
                          className="min-h-[180px] w-full rounded-md border border-border bg-node px-3 py-2 text-sm text-primary md:min-h-[240px]"
                          placeholder="The active prompt baseline appears here"
                          value={draft.system_prompt_text}
                          onChange={(event) =>
                            updateDraft(agent.agent_key, {
                              prompt_mode: draft.prompt_mode === 'default' ? 'override' : draft.prompt_mode,
                              system_prompt_text: event.target.value,
                            })
                          }
                        />
                        <p className="text-[11px] text-muted-foreground">
                          Editing while in Auto mode switches this draft to Override so the saved result matches what you see.
                        </p>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          onClick={() => void handleSave(agent.agent_key)}
                          disabled={busyKey === agent.agent_key}
                        >
                          {busyKey === agent.agent_key ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : null}
                          Save
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => void handleReset(agent.agent_key)}
                          disabled={busyKey === agent.agent_key}
                        >
                          Reset to Auto
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setShowDefaults((prev) => ({
                              ...prev,
                              [agent.agent_key]: !prev[agent.agent_key],
                            }))
                          }
                        >
                          {showDefaults[agent.agent_key] ? 'Hide Default' : 'View Default'}
                        </Button>
                      </div>

                      {showDefaults[agent.agent_key] ? (
                        <textarea
                          readOnly
                          className="min-h-[180px] w-full rounded-md border border-border bg-muted px-3 py-2 text-xs text-muted-foreground"
                          value={detail.defaults.system_prompt_text}
                        />
                      ) : null}
                    </>
                  )}
                </AccordionContent>
              </AccordionItem>
            );
          })}
        </Accordion>
      )}
    </div>
  );
}
