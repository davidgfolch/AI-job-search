import { describe, it, expect } from 'vitest';
import { getSubgroupTitle, groupSettingsByKey } from '../utils/SettingsUtils';

describe('SettingsUtils', () => {
    describe('getSubgroupTitle', () => {
        it('should extract prefix and subprefix if underscore exists', () => {
            expect(getSubgroupTitle('SCRAPPER_INFOJOBS_API_KEY')).toBe('SCRAPPER_INFOJOBS');
        });

        it('should return General if no underscore', () => {
            expect(getSubgroupTitle('SOMEVAR')).toBe('General');
        });
    });

    describe('groupSettingsByKey', () => {
        it('should group scrapper settings correctly', () => {
            const result = groupSettingsByKey({
                'SCRAPPER_INFOJOBS_KEY': '123',
                'SCRAPPER_LINKEDIN_URL': 'abc',
                'GMAIL_EMAIL': 'email@test.com',
                'GLOBAL_TZ': 'UTC',
                'OTHER_VAR': '000'
            });
            expect(result['Scrapper']).toEqual(['SCRAPPER_INFOJOBS_KEY', 'SCRAPPER_LINKEDIN_URL']);
            expect(result['System & Base']).toEqual(['GMAIL_EMAIL', 'GLOBAL_TZ']);
            expect(result['Other']).toEqual(['OTHER_VAR']);
        });

        it('should group AI enrichment settings', () => {
            const result = groupSettingsByKey({ 'AI_MODEL': 'gpt-4' });
            expect(result['AI Enrichment']).toEqual(['AI_MODEL']);
        });

        it('should group UI Frontend settings', () => {
            const result = groupSettingsByKey({ 'VITE_URL': 'localhost', 'UI_APPLY': 'test' });
            expect(result['UI Frontend']).toEqual(['VITE_URL', 'UI_APPLY']);
        });
    });
});
