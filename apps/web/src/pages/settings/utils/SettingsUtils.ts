export const getSubgroupTitle = (key: string) => {
    return key.includes('_') ? key.split('_')[0] : 'General';
};

export const groupSettingsByKey = (envSettings: Record<string, string>) => {
    return Object.keys(envSettings).reduce((acc, key) => {
        const k = key.toUpperCase();
        let group = 'System & Base';
        
        if (/^(INFOJOBS|LINKEDIN|GLASSDOOR|TECNOEMPLEO|INDEED|SHAKERS)/.test(k)) {
            group = 'Scrapper';
        } else if (/^(AI|CLEAN|WHERE|SALARY|SKILL)/.test(k)) {
            group = 'AI Enrichment';
        } else if (/^(APPLY|GROSS|VITE)/.test(k)) {
            group = 'UI Frontend';
        }

        if (!acc[group]) acc[group] = [];
        acc[group].push(key);
        return acc;
    }, {} as Record<string, string[]>);
};
