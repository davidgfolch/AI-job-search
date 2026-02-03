import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useFilterDropdown } from '../useFilterDropdown';

describe('useFilterDropdown Sorting', () => {
    const mockConfigs = [
        { name: 'C NoStats', filters: {}, statistics: false, notify: false },
        { name: 'B Notify', filters: {}, statistics: true, notify: true },
        { name: 'A Normal', filters: {}, statistics: true, notify: false },
        { name: 'D NewItems', filters: {}, statistics: true, notify: false },
    ];

    const mockResults = {
        'D NewItems': { newItems: 10, total: 20 },
        'A Normal': { newItems: 0, total: 20 },
    };

    it('sorts by new items, then notify, then statistics, then name', () => {
        const { result } = renderHook(() => useFilterDropdown({
            configs: mockConfigs as any,
            configName: '',
            onLoad: vi.fn(),
            onSave: vi.fn(),
            onDelete: vi.fn(),
            setIsOpen: vi.fn(),
            isOpen: true,
            results: mockResults as any
        }));

        const sortedNames = result.current.filteredConfigs.map(c => c.name);
        
        expect(sortedNames).toEqual([
            'D NewItems',
            'B Notify',
            'A Normal',
            'C NoStats'
        ]);
    });
});
