export type ProviderOption = { value: string; label: string };
export type LlmProviderGroup = { key: string; label: string; options: ProviderOption[]; fields: string[] };

const OLLAMA: ProviderOption = { value: 'ollama', label: 'Ollama (local/LAN)' };
const LOCAL_HF: ProviderOption = { value: 'huggingface', label: 'HuggingFace (local)' };
const LOCAL_FORM: ProviderOption = { value: 'local', label: 'Local (HuggingFace)' };
const OPENAI: ProviderOption = { value: 'openai', label: 'OpenAI (cloud)' };

export const CLOUD_OPTIONS: ProviderOption[] = [
    { value: 'openrouter', label: 'OpenRouter (free tier)' },
    { value: 'gemini', label: 'Gemini (free tier)' },
    { value: 'groq', label: 'Groq (free tier)' },
    { value: 'cerebras', label: 'Cerebras (free tier)' },
    { value: 'hf-inference', label: 'HuggingFace Inference (free tier)' },
];

export const LLM_PROVIDERS: LlmProviderGroup[] = [
    { key: 'AI_ENRICH_LLM_BACKEND', label: 'aiEnrich', fields: [], options: [OLLAMA, ...CLOUD_OPTIONS] },
    { key: 'AI_ENRICHSKILL_BACKEND', label: 'aiEnrichSkill', fields: [], options: [OLLAMA, LOCAL_HF, ...CLOUD_OPTIONS] },
    { key: 'AI_FORM_PROVIDER', label: 'aiFormFiller', fields: ['OPENAI_API_KEY', 'OPENROUTER_MODEL'], options: [LOCAL_FORM, ...CLOUD_OPTIONS, OPENAI] }
];

export const SHARED_PROVIDER_FIELDS = [
    'OPENROUTER_API_KEY', 'GEMINI_API_KEY', 'GROQ_API_KEY', 'CEREBRAS_API_KEY', 'HF_TOKEN',
    'GEMINI_MODEL', 'GROQ_MODEL', 'CEREBRAS_MODEL', 'HF_INFERENCE_MODEL',
];
