import { describe, it, expect } from 'vitest';
import { getSubgroupTitle, groupSettingsByKey } from '../utils/SettingsUtils';

describe('SettingsUtils', () => {
    describe('getSubgroupTitle', () => {
        it('should extract prefix if underscore exists', () => {
            expect(getSubgroupTitle('SHAKERS_API_KEY')).toBe('SHAKERS');
        });

        it('should return General if no underscore', () => {
            expect(getSubgroupTitle('SOMEVAR')).toBe('General');
        });
    });

    describe('groupSettingsByKey', () => {
        it('should group scrapper settings correctly', () => {
            const result = groupSettingsByKey({
                'INFOJOBS_KEY': '123',
                'LINKEDIN_URL': 'abc',
                'OTHER_VAR': '000'
            });
            expect(result['Scrapper']).toEqual(['INFOJOBS_KEY', 'LINKEDIN_URL']);
            expect(result['System & Base']).toEqual(['OTHER_VAR']);
        });

        it('should group AI enrichment settings', () => {
            const result = groupSettingsByKey({ 'AI_MODEL': 'gpt-4' });
            expect(result['AI Enrichment']).toEqual(['AI_MODEL']);
        });

        it('should group UI Frontend settings', () => {
            const result = groupSettingsByKey({ 'VITE_URL': 'localhost' });
            expect(result['UI Frontend']).toEqual(['VITE_URL']);
        });
    });
});
