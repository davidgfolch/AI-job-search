import { vi } from 'vitest';
import type { FilterConfig } from '../../pages/viewer/components/configurations/hooks/useFilterConfigurations';

export const createFilterConfigServiceMock = (defaults: FilterConfig[] = []) => {
    let mockValues = JSON.parse(JSON.stringify(defaults));
    
    return {
        load: vi.fn().mockImplementation(async (defaultConfigs) => {
            return mockValues.length > 0 ? mockValues : defaultConfigs;
        }),
        save: vi.fn().mockImplementation(async (configs) => {
            mockValues = configs.slice(0, 30);
        }),
        delete: vi.fn(),
        export: vi.fn().mockResolvedValue([]),
        // Helper to inspect current state in tests
        _getStored: () => mockValues
    };
};
