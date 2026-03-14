import { api } from '@/services/api';

export interface LanguageModel {
  display_name: string;
  model_name: string;
  source?: string;
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
    | "GigaChat"
    | "Azure OpenAI"
    | string;
}

// Cache for models to avoid repeated API calls
let languageModels: LanguageModel[] | null = null;

export const clearModelsCache = (): void => {
  languageModels = null;
};

export const findModelByIdentity = (
  models: LanguageModel[],
  modelName?: string | null,
  provider?: string | null
): LanguageModel | null => {
  if (!modelName) {
    return null;
  }
  return (
    models.find((model) => model.model_name === modelName && (!provider || model.provider === provider))
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
    return models.find(model => model.model_name === "gpt-4.1") || models[0] || null;
  } catch (error) {
    console.error('Failed to get default model:', error);
    return null;
  }
};
