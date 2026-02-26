export const getSubgroupTitle = (key: string) => {
    const parts = key.split('_');
    if (parts.length >= 2) {
        return parts.slice(0, 2).join('_');
    }
    return 'General';
};

export const groupSettingsByKey = (envSettings: Record<string, string>) => {
    return Object.keys(envSettings).reduce((acc, key) => {
        const k = key.toUpperCase();
        let group = 'Other';
        
        if (k.startsWith('SCRAPPER_')) {
            group = 'Scrapper';
        } else if (k === 'GLOBAL_TZ' || k.startsWith('GMAIL_')) {
            group = 'System & Base';
        } else if (/^(AI|CLEAN|WHERE|SALARY|SKILL)/.test(k)) {
            group = 'AI Enrichment';
        } else if (/^(APPLY|GROSS|VITE|UI_)/.test(k)) {
            group = 'UI Frontend';
        }

        if (!acc[group]) acc[group] = [];
        acc[group].push(key);
        return acc;
    }, {} as Record<string, string[]>);
};
