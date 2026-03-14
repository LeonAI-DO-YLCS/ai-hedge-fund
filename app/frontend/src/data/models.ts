import { api } from '@/services/api';

export interface LanguageModel {
  display_name: string;
  model_name: string;
  provider_key?: string;
  source?: string;
  is_enabled?: boolean;
  availability_status?: string | null;
  is_custom?: boolean;
  is_stale?: boolean;
  provider:
    | "Anthropic"
    | "DeepSeek"
    | "Google"
    | "Groq"
    | "OpenAI"
    | "Ollama"
    | "LMStudio"
    | "OpenRouter"
    | "xAI"
    | "Azure OpenAI"
    | string;
}

export const getModelProviderIdentity = (model: LanguageModel): string => {
  return model.provider_key || model.provider;
};

export const createModelIdentity = (
  modelName?: string | null,
  providerIdentity?: string | null
): string => {
  if (!modelName) {
    return '';
  }
  return providerIdentity ? `${providerIdentity}::${modelName}` : modelName;
};

export const getModelIdentity = (model: LanguageModel): string => {
  return createModelIdentity(model.model_name, getModelProviderIdentity(model));
};

export const parseModelIdentity = (
  identity?: string | null
): { model_name: string; provider_identity: string | null } | null => {
  if (!identity) {
    return null;
  }
  const separator = identity.indexOf('::');
  if (separator === -1) {
    return { model_name: identity, provider_identity: null };
  }
  return {
    provider_identity: identity.slice(0, separator) || null,
    model_name: identity.slice(separator + 2),
  };
};

// Cache for models to avoid repeated API calls
let languageModels: LanguageModel[] | null = null;

export const clearModelsCache = (): void => {
  languageModels = null;
};

export const findModelByIdentity = (
  models: LanguageModel[],
  modelName?: string | null,
  providerIdentity?: string | null
): LanguageModel | null => {
  if (!modelName) {
    return null;
  }
  return (
    models.find((model) => {
      if (model.model_name !== modelName) {
        return false;
      }
      if (!providerIdentity) {
        return true;
      }
      return model.provider_key === providerIdentity || model.provider === providerIdentity;
    })
    || models.find((model) => model.model_name === modelName)
    || null
  );
};

/**
 * Get the list of models from the backend API
 * Uses caching to avoid repeated API calls
 */
export const getModels = async (): Promise<LanguageModel[]> => {
  if (languageModels) {
    return languageModels;
  }
  
  try {
    languageModels = await api.getLanguageModels();
    return languageModels;
  } catch (error) {
    console.error('Failed to fetch models:', error);
    throw error; // Let the calling component handle the error
  }
};

/**
 * Get the default model (GPT-4.1) from the models list
 */
export const getDefaultModel = async (): Promise<LanguageModel | null> => {
  try {
    const models = await getModels();
    return models[0] || null;
  } catch (error) {
    console.error('Failed to get default model:', error);
    return null;
  }
};
