export const mockEnvSettings = {
    'PREFIX_KEY1': 'value1',
    'PREFIX_KEY2': 'value2',
    'OTHER_KEY': 'value3',
    'PASSWORD_KEY': 'secret',
    'SCRAPPER_TEST_KEY': 'scrapper_value',
    'AI_SKILL_ENABLED': 'true',
    'AI_ENRICH_LLM_BACKEND': 'ollama',
    'AI_ENRICHSKILL_BACKEND': 'ollama',
    'AI_FORM_PROVIDER': 'local',
    'AI_ENRICH_OLLAMA_MODEL': 'ollama/qwen2.5:3b',
    'AI_ENRICHSKILL_OLLAMA_MODEL': 'ollama/qwen2.5:3b',
    'AI_FORM_HF_MODEL': 'Qwen/Qwen2.5-1.5B-Instruct',
    'OPENAI_API_KEY': 'sk-openai-test',
    'OPENROUTER_API_KEY': 'sk-or-test'
};

export const mockGroupedSettings = {
    'System & Base': ['GLOBAL_TZ'],
    'UI Frontend': ['UI_KEY'],
    'Scrapper': ['SCRAPPER_TEST_KEY'],
    'AI Enrichment': ['AI_SKILL_ENABLED'],
    'Other': ['PREFIX_KEY1', 'PREFIX_KEY2', 'OTHER_KEY', 'PASSWORD_KEY']
};

export const mockScrapperState = { lastExecution: 'now' };
