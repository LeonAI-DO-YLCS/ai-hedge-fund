import { type NodeProps } from '@xyflow/react';
import { Brain } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ModelSelector } from '@/components/ui/llm-selector';
import { useFlowContext } from '@/contexts/flow-context';
import { AgentNodeConfig, useNodeContext } from '@/contexts/node-context';
import { extractBaseAgentKey } from '@/data/node-mappings';
import { findModelByIdentity, getDefaultModel, getModels, LanguageModel } from '@/data/models';
import { useNodeState } from '@/hooks/use-node-state';
import { useOutputNodeConnection } from '@/hooks/use-output-node-connection';
import { cn } from '@/lib/utils';
import { agentConfigApi } from '@/services/agent-config-api';
import { type PortfolioManagerNode } from '../types';
import { getStatusColor } from '../utils';
import { InvestmentReportDialog } from './investment-report-dialog';
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

export function PortfolioManagerNode({
  data,
  selected,
  id,
  isConnectable,
}: NodeProps<PortfolioManagerNode>) {
  const { currentFlowId } = useFlowContext();
  const { getAgentNodeDataForFlow, setAgentConfig, getAgentConfig, getOutputNodeDataForFlow } = useNodeContext();

  // Get agent node data for the current flow
  const agentNodeData = getAgentNodeDataForFlow(currentFlowId?.toString() || null);
  const nodeData = agentNodeData[id] || {
    status: 'IDLE',
    ticker: null,
    message: '',
    messages: [],
    lastUpdated: 0,
  };
  const status = nodeData.status;
  const isInProgress = status === 'IN_PROGRESS';
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [showDefaultPrompt, setShowDefaultPrompt] = useState(false);
  const [defaultPrompt, setDefaultPrompt] = useState('');

  // Use persistent state hooks
  const [availableModels, setAvailableModels] = useNodeState<LanguageModel[]>(
    id,
    'availableModels',
    []
  );
  const [agentConfig, setAgentConfigState] = useNodeState<AgentNodeConfig>(id, 'agentConfig', DEFAULT_AGENT_CONFIG);
  const baseAgentKey = extractBaseAgentKey(id);

  // Load models on mount
  useEffect(() => {
    const syncConfig = async (models: LanguageModel[]) => {
      try {
        const persistedConfig = await agentConfigApi.getOne(baseAgentKey);
        setAgentConfigState({
          model: findModelByIdentity(models, persistedConfig.model_name, persistedConfig.model_provider as string | null),
          fallbackModel: findModelByIdentity(models, persistedConfig.fallback_model_name, persistedConfig.fallback_model_provider as string | null),
          systemPromptOverride: persistedConfig.system_prompt_override || '',
          systemPromptAppend: persistedConfig.system_prompt_append || '',
          temperature: persistedConfig.temperature ?? null,
          maxTokens: persistedConfig.max_tokens ?? null,
          topP: persistedConfig.top_p ?? null,
        });
      } catch (error) {
        console.warn(`Failed to sync config for ${baseAgentKey}:`, error);
      }
    };

    const loadModels = async () => {
      try {
        const [models, defaultModel] = await Promise.all([
          getModels(),
          getDefaultModel()
        ]);
        setAvailableModels(models);

        await syncConfig(models);

        if (!agentConfig.model && defaultModel) {
          setAgentConfigState((prev) => ({ ...prev, model: defaultModel }));
        }
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
  }, [agentConfig.model, baseAgentKey, setAgentConfigState, setAvailableModels]);

  // Update the node context when the model changes
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
    setAgentConfigState(DEFAULT_AGENT_CONFIG);
  };

  const handleViewDefaultPrompt = async () => {
    try {
      const prompt = await agentConfigApi.getDefaultPrompt(baseAgentKey);
      setDefaultPrompt(prompt);
      setShowDefaultPrompt(true);
    } catch (error) {
      console.error(`Failed to load default prompt for ${baseAgentKey}:`, error);
    }
  };
  
  const outputNodeData = getOutputNodeDataForFlow(currentFlowId?.toString() || null);

  // Get connected agent IDs
  const { connectedAgentIds } = useOutputNodeConnection(id);

  return (
    <>
      <NodeShell
        id={id}
        selected={selected}
        isConnectable={isConnectable}
        icon={<Brain className="h-5 w-5" />}
        iconColor={getStatusColor(status)}
        name={data.name || 'Portfolio Manager'}
        description={data.description}
        hasRightHandle={false}
        status={status}
      >
        <CardContent className="p-0">
          <div className="border-t border-border p-3">
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <div className="text-subtitle text-primary flex items-center gap-1">
                  Status
                </div>

                <div
                  className={cn(
                    'text-foreground text-xs rounded p-2 border border-status',
                    isInProgress ? 'gradient-animation' : getStatusColor(status)
                  )}
                >
                  <span className="capitalize">
                    {status.toLowerCase().replace(/_/g, ' ')}
                  </span>
                </div>
              </div>
              <div className='flex flex-col gap-2'>
                {outputNodeData && (
                  <Button
                    size="sm"
                    onClick={() => setIsDialogOpen(true)}
                  >
                    View Investment Report
                  </Button>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <div className="text-subtitle text-primary flex items-center gap-1">
                  Model
                </div>
                <ModelSelector
                  models={availableModels}
                  value={agentConfig.model?.model_name || ''}
                  onChange={handleModelChange}
                  placeholder="Auto"
                />
                <div className="text-subtitle text-primary flex items-center gap-1 mt-2">
                  Fallback Model
                </div>
                <ModelSelector
                  models={availableModels}
                  value={agentConfig.fallbackModel?.model_name || ''}
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
                  Prompt Override
                </div>
                <textarea
                  className="min-h-24 rounded-md border border-border bg-node px-3 py-2 text-sm text-primary"
                  placeholder="Replace the default system prompt for this node"
                  value={agentConfig.systemPromptOverride}
                  onChange={(event) => setAgentConfigState((prev) => ({ ...prev, systemPromptOverride: event.target.value }))}
                />
                <div className="text-subtitle text-primary flex items-center gap-1 mt-2">
                  Prompt Append
                </div>
                <textarea
                  className="min-h-20 rounded-md border border-border bg-node px-3 py-2 text-sm text-primary"
                  placeholder="Append extra instructions to the default system prompt"
                  value={agentConfig.systemPromptAppend}
                  onChange={(event) => setAgentConfigState((prev) => ({ ...prev, systemPromptAppend: event.target.value }))}
                />
                <div className="flex flex-wrap gap-2 mt-2">
                  <Button variant="outline" size="sm" onClick={() => void handleViewDefaultPrompt()}>
                    View Default
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
            </div>
          </div>
          <InvestmentReportDialog
            isOpen={isDialogOpen}
            onOpenChange={setIsDialogOpen}
            outputNodeData={outputNodeData}
            connectedAgentIds={connectedAgentIds}
          />
        </CardContent>
      </NodeShell>
    </>
  );
}
