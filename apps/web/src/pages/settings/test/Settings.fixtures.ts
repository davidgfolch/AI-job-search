export const mockEnvSettings = {
    'PREFIX_KEY1': 'value1',
    'PREFIX_KEY2': 'value2',
    'OTHER_KEY': 'value3',
    'PASSWORD_KEY': 'secret',
    'SCRAPPER_TEST_KEY': 'scrapper_value',
    'AI_SKILL_ENABLED': 'true'
};

export const mockGroupedSettings = {
    'System & Base': ['GLOBAL_TZ'],
    'UI Frontend': ['UI_KEY'],
    'Scrapper': ['SCRAPPER_TEST_KEY'],
    'AI Enrichment': ['AI_SKILL_ENABLED'],
    'Other': ['PREFIX_KEY1', 'PREFIX_KEY2', 'OTHER_KEY', 'PASSWORD_KEY']
};

export const mockScrapperState = { lastExecution: 'now' };
