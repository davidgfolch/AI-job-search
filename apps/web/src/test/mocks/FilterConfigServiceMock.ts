import { vi } from 'vitest';

export const createFilterConfigServiceMock = (defaults: any[] = []) => {
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
