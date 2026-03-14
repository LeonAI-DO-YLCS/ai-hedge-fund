import { type NodeProps } from '@xyflow/react';
import { Bot } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ModelSelector } from '@/components/ui/llm-selector';
import { useFlowContext } from '@/contexts/flow-context';
import { AgentNodeConfig, useNodeContext } from '@/contexts/node-context';
import { extractBaseAgentKey } from '@/data/node-mappings';
import {
  createModelIdentity,
  findModelByIdentity,
  getModelIdentity,
  getModels,
  LanguageModel,
} from '@/data/models';
import { useNodeState } from '@/hooks/use-node-state';
import { cn } from '@/lib/utils';
import { agentConfigApi, AgentConfigurationDetail } from '@/services/agent-config-api';
import { type AgentNode } from '../types';
import { getStatusColor } from '../utils';
import { AgentOutputDialog } from './agent-output-dialog';
import { NodeShell } from './node-shell';

const DEFAULT_AGENT_CONFIG: AgentNodeConfig = {
  model: null,
  fallbackModel: null,
  systemPromptOverride: '',
  systemPromptAppend: '',
  temperature: null,
  maxTokens: null,
  topP: null,
};

const buildNodeConfig = (
  detail: AgentConfigurationDetail,
  models: LanguageModel[]
): AgentNodeConfig => ({
  model: findModelByIdentity(models, detail.effective.model_name, detail.effective.model_provider as string | null),
  fallbackModel: findModelByIdentity(
    models,
    detail.effective.fallback_model_name,
    detail.effective.fallback_model_provider as string | null
  ),
  systemPromptOverride: detail.effective.system_prompt_text || '',
  systemPromptAppend: '',
  temperature: detail.effective.temperature ?? null,
  maxTokens: detail.effective.max_tokens ?? null,
  topP: detail.effective.top_p ?? null,
});

export function AgentNode({
  data,
  selected,
  id,
  isConnectable,
}: NodeProps<AgentNode>) {
  const { currentFlowId } = useFlowContext();
  const { getAgentNodeDataForFlow, setAgentConfig, getAgentConfig } = useNodeContext();
  
  // Get agent node data for the current flow
  const agentNodeData = getAgentNodeDataForFlow(currentFlowId?.toString() || null);
  const nodeData = agentNodeData[id] || { 
    status: 'IDLE', 
    ticker: null, 
    message: '', 
    messages: [],
    lastUpdated: 0
  };
  const status = nodeData.status;
  const isInProgress = status === 'IN_PROGRESS';
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [showDefaultPrompt, setShowDefaultPrompt] = useState(false);
  const [defaultPrompt, setDefaultPrompt] = useState('');
  const [detail, setDetail] = useState<AgentConfigurationDetail | null>(null);
  
  // Use persistent state hooks
  const [availableModels, setAvailableModels] = useNodeState<LanguageModel[]>(id, 'availableModels', []);
  const [agentConfig, setAgentConfigState] = useNodeState<AgentNodeConfig>(id, 'agentConfig', DEFAULT_AGENT_CONFIG);
  const baseAgentKey = extractBaseAgentKey(id);

  // Load models on mount
  useEffect(() => {
    const syncConfig = async (models: LanguageModel[]) => {
      try {
        const effectiveDetail = await agentConfigApi.getOne(baseAgentKey);
        setDetail(effectiveDetail);
        setDefaultPrompt(effectiveDetail.defaults.system_prompt_text || '');
        setAgentConfigState(buildNodeConfig(effectiveDetail, models));
      } catch (error) {
        console.warn(`Failed to sync config for ${baseAgentKey}:`, error);
      }
    };

    const loadModels = async () => {
      try {
        const models = await getModels();
        setAvailableModels(models);
        await syncConfig(models);
      } catch (error) {
        console.error('Failed to load models:', error);
        // Keep empty array as fallback
      }
    };

    const handleConfigUpdated = (event: Event) => {
      const detail = (event as CustomEvent<{ agentKey?: string }>).detail;
      if (!detail?.agentKey || detail.agentKey === 'all' || detail.agentKey === baseAgentKey) {
        void loadModels();
      }
    };

    void loadModels();
    window.addEventListener('agent-config-updated', handleConfigUpdated as EventListener);
    return () => window.removeEventListener('agent-config-updated', handleConfigUpdated as EventListener);
  }, [baseAgentKey, setAvailableModels, setAgentConfigState]);

  // Update the node context when config changes
  useEffect(() => {
    const flowId = currentFlowId?.toString() || null;
    const currentContextConfig = getAgentConfig(flowId, id);
    if (JSON.stringify(agentConfig) !== JSON.stringify(currentContextConfig)) {
      setAgentConfig(flowId, id, agentConfig);
    }
  }, [agentConfig, id, currentFlowId, setAgentConfig, getAgentConfig]);

  const handleModelChange = (model: LanguageModel | null) => {
    setAgentConfigState((prev) => ({ ...prev, model }));
  };

  const handleFallbackChange = (model: LanguageModel | null) => {
    setAgentConfigState((prev) => ({ ...prev, fallbackModel: model }));
  };

  const handleNumberChange = (key: 'temperature' | 'maxTokens' | 'topP', value: string) => {
    const parsed = value.trim() === '' ? null : Number(value);
    setAgentConfigState((prev) => ({
      ...prev,
      [key]: Number.isNaN(parsed) ? null : parsed,
    }));
  };

  const handleUseDefaults = () => {
    if (!detail) {
      setAgentConfigState(DEFAULT_AGENT_CONFIG);
      return;
    }
    setAgentConfigState(buildNodeConfig(detail, availableModels));
  };

  const handleViewDefaultPrompt = async () => {
    try {
      const prompt = detail?.defaults.system_prompt_text || await agentConfigApi.getDefaultPrompt(baseAgentKey);
      setDefaultPrompt(prompt);
      setShowDefaultPrompt((prev) => !prev);
    } catch (error) {
      console.error(`Failed to load default prompt for ${baseAgentKey}:`, error);
    }
  };

  return (
    <NodeShell
      id={id}
      selected={selected}
      isConnectable={isConnectable}
      icon={<Bot className="h-5 w-5" />}
      iconColor={getStatusColor(status)}
      name={data.name || "Agent"}
      description={data.description}
      status={status}
    >
      <CardContent className="p-0">
        <div className="border-t border-border p-3">
          <div className="flex flex-col gap-2">
            <div className="text-subtitle text-primary flex items-center gap-1">
              Status
            </div>

            <div className={cn(
              "text-foreground text-xs rounded p-2 border border-status",
              isInProgress ? "gradient-animation" : getStatusColor(status)
            )}>
              <span className="capitalize">{status.toLowerCase().replace(/_/g, ' ')}</span>
            </div>
            
            {nodeData.message && (
              <div className="text-foreground text-subtitle">
                {nodeData.message !== "Done" && nodeData.message}
                {nodeData.ticker && <span className="ml-1">({nodeData.ticker})</span>}
              </div>
            )}
            <Accordion type="single" collapsible>
              <AccordionItem value="advanced" className="border-none">
                <AccordionTrigger className="!text-subtitle text-primary">
                  Advanced
                </AccordionTrigger>
                <AccordionContent className="pt-2">
                  <div className="flex flex-col gap-2">
                    <div className="text-subtitle text-primary flex items-center gap-1">
                      Model
                    </div>
                    <ModelSelector
                      models={availableModels}
                      value={agentConfig.model
                        ? getModelIdentity(agentConfig.model)
                        : createModelIdentity(detail?.effective.model_name, detail?.effective.model_provider as string | null)}
                      onChange={handleModelChange}
                      placeholder="Auto"
                    />
                    <div className="text-subtitle text-primary flex items-center gap-1 mt-2">
                      Fallback Model
                    </div>
                    <ModelSelector
                      models={availableModels}
                      value={agentConfig.fallbackModel
                        ? getModelIdentity(agentConfig.fallbackModel)
                        : createModelIdentity(detail?.effective.fallback_model_name, detail?.effective.fallback_model_provider as string | null)}
                      onChange={handleFallbackChange}
                      placeholder="Optional fallback"
                    />
                    {agentConfig.model?.provider && agentConfig.fallbackModel?.provider && agentConfig.model.provider === agentConfig.fallbackModel.provider && (
                      <p className="text-xs text-amber-400">Fallback uses the same provider as the primary model.</p>
                    )}
                    <div className="grid grid-cols-1 gap-2 mt-2">
                      <Input
                        placeholder="Temperature"
                        value={agentConfig.temperature ?? ''}
                        onChange={(event) => handleNumberChange('temperature', event.target.value)}
                      />
                      <Input
                        placeholder="Max tokens"
                        value={agentConfig.maxTokens ?? ''}
                        onChange={(event) => handleNumberChange('maxTokens', event.target.value)}
                      />
                      <Input
                        placeholder="Top P"
                        value={agentConfig.topP ?? ''}
                        onChange={(event) => handleNumberChange('topP', event.target.value)}
                      />
                    </div>
                    <div className="text-subtitle text-primary flex items-center gap-1 mt-2">
                      Effective Prompt
                    </div>
                    <textarea
                      className="min-h-32 rounded-md border border-border bg-node px-3 py-2 text-sm text-primary md:min-h-40"
                      placeholder="Edit the prompt baseline for this node"
                      value={agentConfig.systemPromptOverride}
                      onChange={(event) => setAgentConfigState((prev) => ({ ...prev, systemPromptOverride: event.target.value }))}
                    />
                    {detail && (
                      <p className="text-[11px] text-muted-foreground">
                        Prompt source: {detail.sources.system_prompt_text.replace(/_/g, ' ')}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-2 mt-2">
                      <Button variant="outline" size="sm" onClick={() => void handleViewDefaultPrompt()}>
                        {showDefaultPrompt ? 'Hide Default' : 'View Default'}
                      </Button>
                      <Button variant="ghost" size="sm" onClick={handleUseDefaults}>
                        Reset to Auto
                      </Button>
                    </div>
                    {showDefaultPrompt && defaultPrompt && (
                      <textarea
                        readOnly
                        className="mt-2 min-h-28 rounded-md border border-border bg-muted px-3 py-2 text-xs text-muted-foreground"
                        value={defaultPrompt}
                      />
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>
        </div>
        <AgentOutputDialog
          isOpen={isDialogOpen}
          onOpenChange={setIsDialogOpen}
          name={data.name || "Agent"}
          nodeId={id}
          flowId={currentFlowId?.toString() || null}
        />
      </CardContent>
    </NodeShell>
  );
}
