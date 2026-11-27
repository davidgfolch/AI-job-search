export type ProviderOption = { value: string; label: string };
export type LlmProviderGroup = { key: string; label: string; options: ProviderOption[]; modelKeys: Record<string, string> };
export type ProviderKeyLink = { label: string; url: string };

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
    { key: 'AI_ENRICH_LLM_BACKEND', label: 'aiEnrich', options: [OLLAMA, ...CLOUD_OPTIONS], modelKeys: {
        ollama: 'AI_ENRICH_OLLAMA_MODEL', openrouter: 'AI_ENRICH_OPENROUTER_MODEL', gemini: 'AI_ENRICH_GEMINI_MODEL',
        groq: 'AI_ENRICH_GROQ_MODEL', cerebras: 'AI_ENRICH_CEREBRAS_MODEL', 'hf-inference': 'AI_ENRICH_HF_INFERENCE_MODEL',
    } },
    { key: 'AI_ENRICHSKILL_BACKEND', label: 'aiEnrichSkill', options: [OLLAMA, LOCAL_HF, ...CLOUD_OPTIONS], modelKeys: {
        ollama: 'AI_ENRICHSKILL_OLLAMA_MODEL', huggingface: 'AI_ENRICHSKILL_HF_MODEL_ID', openrouter: 'AI_ENRICHSKILL_OPENROUTER_MODEL',
        gemini: 'AI_ENRICHSKILL_GEMINI_MODEL', groq: 'AI_ENRICHSKILL_GROQ_MODEL', cerebras: 'AI_ENRICHSKILL_CEREBRAS_MODEL',
        'hf-inference': 'AI_ENRICHSKILL_HF_INFERENCE_MODEL',
    } },
    { key: 'AI_FORM_PROVIDER', label: 'aiFormFiller', options: [LOCAL_FORM, ...CLOUD_OPTIONS, OPENAI], modelKeys: {
        local: 'AI_FORM_HF_MODEL', openai: 'AI_FORM_OPENAI_MODEL', openrouter: 'AI_FORM_OPENROUTER_MODEL',
        gemini: 'AI_FORM_GEMINI_MODEL', groq: 'AI_FORM_GROQ_MODEL', cerebras: 'AI_FORM_CEREBRAS_MODEL',
        'hf-inference': 'AI_FORM_HF_INFERENCE_MODEL',
    } },
];

export const API_KEY_FIELDS = ['OPENROUTER_API_KEY', 'GEMINI_API_KEY', 'GROQ_API_KEY', 'CEREBRAS_API_KEY', 'HF_TOKEN', 'OPENAI_API_KEY'];

export const PROVIDER_KEY_LINKS: Record<string, ProviderKeyLink> = {
    OPENROUTER_API_KEY: { label: 'Get a key', url: 'https://openrouter.ai/keys' },
    GEMINI_API_KEY: { label: 'Get a key', url: 'https://aistudio.google.com/apikey' },
    GROQ_API_KEY: { label: 'Get a key', url: 'https://console.groq.com/keys' },
    CEREBRAS_API_KEY: { label: 'Get a key', url: 'https://cloud.cerebras.ai/' },
    HF_TOKEN: { label: 'Get a token', url: 'https://huggingface.co/settings/tokens' },
    OPENAI_API_KEY: { label: 'Get a key', url: 'https://platform.openai.com/api-keys' },
};

export const MODEL_OPTIONS: Record<string, string[]> = {
    ollama: ['ollama/qwen2.5:3b', 'ollama/phi3.5:3b', 'ollama/llama3.2:1b'],
    huggingface: ['Qwen/Qwen2.5-1.5B-Instruct'],
    local: ['Qwen/Qwen2.5-1.5B-Instruct'],
    openrouter: ['openrouter/free', 'nex-agi/nex-n2.5-pro:free', 'nvidia/nemotron-3.5-lightning:free', 'google/gemini-2.5-flash-lite'],
    gemini: ['gemini-2.5-flash-lite', 'gemini-2.5-flash'],
    groq: ['openai/gpt-oss-20b'],
    cerebras: ['llama-3.3-70b'],
    'hf-inference': ['Qwen/Qwen2.5-1.5B-Instruct'],
    openai: ['gpt-4o-mini', 'gpt-4o'],
};

export const LLM_CONFIG_KEYS = [...new Set([
    ...LLM_PROVIDERS.flatMap(group => [group.key, ...Object.values(group.modelKeys)]),
    ...API_KEY_FIELDS,
])];
