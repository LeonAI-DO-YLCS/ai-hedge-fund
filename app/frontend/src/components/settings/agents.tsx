import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ModelSelector } from '@/components/ui/llm-selector';
import { findModelByIdentity, getModels, LanguageModel } from '@/data/models';
import { cn } from '@/lib/utils';
import { agentConfigApi, AgentConfigurationResponse, AgentConfigurationUpdateRequest } from '@/services/agent-config-api';
import { RefreshCw, Settings2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

interface AgentsSettingsProps {
  className?: string;
}

type DraftMap = Record<string, AgentConfigurationUpdateRequest>;

const toDraft = (config: AgentConfigurationResponse): AgentConfigurationUpdateRequest => ({
  model_name: config.model_name || null,
  model_provider: config.model_provider || null,
  fallback_model_name: config.fallback_model_name || null,
  fallback_model_provider: config.fallback_model_provider || null,
  system_prompt_override: config.system_prompt_override || '',
  system_prompt_append: config.system_prompt_append || '',
  temperature: config.temperature ?? null,
  max_tokens: config.max_tokens ?? null,
  top_p: config.top_p ?? null,
});

export function AgentsSettings({ className }: AgentsSettingsProps) {
  const [agents, setAgents] = useState<AgentConfigurationResponse[]>([]);
  const [models, setModels] = useState<LanguageModel[]>([]);
  const [drafts, setDrafts] = useState<DraftMap>({});
  const [defaultPrompts, setDefaultPrompts] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [applyAllModel, setApplyAllModel] = useState<LanguageModel | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [configs, availableModels] = await Promise.all([
        agentConfigApi.getAll(),
        getModels(),
      ]);
      setAgents(configs);
      setModels(availableModels);
      setDrafts(Object.fromEntries(configs.map((config) => [config.agent_key, toDraft(config)])));
    } catch (fetchError) {
      console.error('Failed to load agent settings:', fetchError);
      setError('Failed to load agent settings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const orderedAgents = useMemo(() => [...agents].sort((a, b) => a.display_name.localeCompare(b.display_name)), [agents]);

  const getDraft = (agentKey: string): AgentConfigurationUpdateRequest => drafts[agentKey] || {};

  const updateDraft = (agentKey: string, patch: Partial<AgentConfigurationUpdateRequest>) => {
    setDrafts((prev) => ({
      ...prev,
      [agentKey]: {
        ...getDraft(agentKey),
        ...patch,
      },
    }));
  };

  const handleSave = async (agentKey: string) => {
    setBusyKey(agentKey);
    try {
      const updated = await agentConfigApi.update(agentKey, getDraft(agentKey));
      setAgents((prev) => prev.map((agent) => (agent.agent_key === agentKey ? updated : agent)));
      setDrafts((prev) => ({ ...prev, [agentKey]: toDraft(updated) }));
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
      await load();
    } catch (resetError) {
      console.error(`Failed to reset agent config for ${agentKey}:`, resetError);
      setError(resetError instanceof Error ? resetError.message : 'Failed to reset agent config.');
    } finally {
      setBusyKey(null);
    }
  };

  const handleViewDefault = async (agentKey: string) => {
    if (defaultPrompts[agentKey]) {
      setDefaultPrompts((prev) => ({ ...prev, [agentKey]: '' }));
      return;
    }
    try {
      const prompt = await agentConfigApi.getDefaultPrompt(agentKey);
      setDefaultPrompts((prev) => ({ ...prev, [agentKey]: prompt }));
    } catch (promptError) {
      console.error(`Failed to load default prompt for ${agentKey}:`, promptError);
      setError(promptError instanceof Error ? promptError.message : 'Failed to load default prompt.');
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
      await load();
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
        <h2 className="text-xl font-semibold text-primary mb-2">Agents</h2>
        <p className="text-sm text-muted-foreground">
          Configure primary models, fallbacks, prompts, and runtime parameters for all agents from one place.
        </p>
      </div>

      {error && (
        <Card className="bg-red-500/5 border-red-500/20">
          <CardContent className="p-4 text-sm text-red-400">{error}</CardContent>
        </Card>
      )}

      <Card className="bg-panel border-gray-700 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="text-lg font-medium text-primary flex items-center gap-2">
            <Settings2 className="h-4 w-4" />
            Apply to All
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <ModelSelector models={models} value={applyAllModel?.model_name || ''} onChange={setApplyAllModel} placeholder="Choose a shared model" />
          <Button onClick={() => void handleApplyToAll()} disabled={!applyAllModel || busyKey === 'all'}>
            {busyKey === 'all' ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : null}
            Apply Model to All Agents
          </Button>
        </CardContent>
      </Card>

      {loading ? (
        <Card className="bg-panel border-gray-700 dark:border-gray-700">
          <CardContent className="p-6 text-sm text-muted-foreground">Loading agent settings...</CardContent>
        </Card>
      ) : (
        <Accordion type="multiple" className="space-y-3">
          {orderedAgents.map((agent) => {
            const draft = getDraft(agent.agent_key);
            const selectedModel = findModelByIdentity(models, draft.model_name, draft.model_provider as string | null);
            const fallbackModel = findModelByIdentity(models, draft.fallback_model_name, draft.fallback_model_provider as string | null);
            return (
              <AccordionItem key={agent.agent_key} value={agent.agent_key} className="rounded-lg border border-border bg-panel px-4">
                <AccordionTrigger className="hover:no-underline">
                  <div className="text-left">
                    <div className="font-medium text-primary">{agent.display_name}</div>
                    <div className="text-xs text-muted-foreground">{agent.description}</div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-4 pb-4">
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-primary">Primary Model</div>
                    <ModelSelector
                      models={models}
                      value={selectedModel?.model_name || ''}
                      onChange={(model) => updateDraft(agent.agent_key, { model_name: model?.model_name || null, model_provider: model?.provider || null })}
                      placeholder="Auto"
                    />
                  </div>
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-primary">Fallback Model</div>
                    <ModelSelector
                      models={models}
                      value={fallbackModel?.model_name || ''}
                      onChange={(model) => updateDraft(agent.agent_key, { fallback_model_name: model?.model_name || null, fallback_model_provider: model?.provider || null })}
                      placeholder="Optional fallback"
                    />
                    {draft.model_provider && draft.fallback_model_provider && draft.model_provider === draft.fallback_model_provider && (
                      <p className="text-xs text-amber-400">Fallback uses the same provider as the primary model.</p>
                    )}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <Input placeholder="Temperature" value={draft.temperature ?? ''} onChange={(event) => updateDraft(agent.agent_key, { temperature: event.target.value === '' ? null : Number(event.target.value) })} />
                    <Input placeholder="Max tokens" value={draft.max_tokens ?? ''} onChange={(event) => updateDraft(agent.agent_key, { max_tokens: event.target.value === '' ? null : Number(event.target.value) })} />
                    <Input placeholder="Top P" value={draft.top_p ?? ''} onChange={(event) => updateDraft(agent.agent_key, { top_p: event.target.value === '' ? null : Number(event.target.value) })} />
                  </div>
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-primary">Prompt Override</div>
                    <textarea
                      className="min-h-28 w-full rounded-md border border-border bg-node px-3 py-2 text-sm text-primary"
                      placeholder="Replace the default system prompt"
                      value={draft.system_prompt_override || ''}
                      onChange={(event) => updateDraft(agent.agent_key, { system_prompt_override: event.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-primary">Prompt Append</div>
                    <textarea
                      className="min-h-24 w-full rounded-md border border-border bg-node px-3 py-2 text-sm text-primary"
                      placeholder="Append extra instructions to the default system prompt"
                      value={draft.system_prompt_append || ''}
                      onChange={(event) => updateDraft(agent.agent_key, { system_prompt_append: event.target.value })}
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" onClick={() => void handleSave(agent.agent_key)} disabled={busyKey === agent.agent_key}>
                      {busyKey === agent.agent_key ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : null}
                      Save
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => void handleReset(agent.agent_key)} disabled={busyKey === agent.agent_key}>
                      Reset to Default
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => void handleViewDefault(agent.agent_key)}>
                      {defaultPrompts[agent.agent_key] ? 'Hide Default' : 'View Default'}
                    </Button>
                  </div>
                  {defaultPrompts[agent.agent_key] && (
                    <textarea readOnly className="min-h-32 w-full rounded-md border border-border bg-muted px-3 py-2 text-xs text-muted-foreground" value={defaultPrompts[agent.agent_key]} />
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
