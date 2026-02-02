// @vitest-environment jsdom
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import React from 'react';
import type { JobListParams } from '../api/ViewerApi.ts';

// Mocks first
// Default mocks
vi.mock('../../../../resources/defaultFilterConfigurations.json', () => ({ 
    default: []
}));

// Service mock
const { mockService } = vi.hoisted(() => {
    return {
        mockService: {
            load: vi.fn(),
            save: vi.fn(),
            delete: vi.fn(),
            export: vi.fn().mockResolvedValue([]),
        }
    };
});

export { mockService };

vi.mock('../hooks/FilterConfigService.ts', () => ({
    FilterConfigService: class { constructor() { return mockService; } }
}));

// Imports after mocks
import FilterConfigurations from '../components/FilterConfigurations.tsx';
import { createMockFilters } from './test-utils.tsx';
import { mockLocalStorage } from '../../../test/mocks/storageMocks.ts';

export const mockFilters = createMockFilters({ search: 'React Developer', flagged: true, like: false, days_old: 7 });

export const waitForLoad = async (isLoaded: { value: boolean }) => {
    await waitFor(() => {
        if (!isLoaded.value) throw new Error('Configurations not yet loaded');
    });
};

export async function setup(
    configs: { name: string, filters: JobListParams }[] = [], 
    props: any = {},
    isLoadedRef: { value: boolean }
) {
    if (configs.length > 0) {
        localStorage.setItem('filter_configurations', JSON.stringify(configs));
    }
    
    const onLoad = vi.fn();
    const curFilters = props.currentFilters || mockFilters;
    const onMsg = props.onMessage || vi.fn();

    const result = render(
        <FilterConfigurations 
            currentFilters={curFilters} 
            onLoadConfig={onLoad} 
            onMessage={onMsg} 
        />
    );
    
    await waitForLoad(isLoadedRef);
    
    return { 
        ...result, 
        input: screen.getByPlaceholderText(/Type to load or enter name to save/i) as HTMLInputElement, 
        onLoad 
    };
}

export const configureMockServiceBehavior = (isLoadedRef: { value: boolean }) => {
     mockLocalStorage();
     vi.clearAllMocks();
     
     const load = mockService.load as any;
     load.mockImplementation(async (defaults: any) => {
         const stored = JSON.parse(localStorage.getItem('filter_configurations') || '[]');
         isLoadedRef.value = true;
         return stored.length ? stored : defaults;
     });
     
     const save = mockService.save as any;
     save.mockImplementation(async (configs: any) => {
         const limited = configs.slice(0, 30);
         localStorage.setItem('filter_configurations', JSON.stringify(limited));
     });
     
     isLoadedRef.value = false;
};
