import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useFilterDropdown } from '../useFilterDropdown';

describe('useFilterDropdown Ordering', () => {
    it('respects explicit ordering field over smart sorting', () => {
        const mockConfigs = [
            { name: 'Config A', filters: {}, statistics: true, notify: true, ordering: 2 },
            { name: 'Config B', filters: {}, statistics: false, notify: false, ordering: 0 },
            { name: 'Config C', filters: {}, statistics: true, notify: true, ordering: 1 },
        ];

        const { result } = renderHook(() => useFilterDropdown({
            configs: mockConfigs as any,
            configName: '',
            onLoad: vi.fn(),
            onSave: vi.fn(),
            onDelete: vi.fn(),
            setIsOpen: vi.fn(),
            isOpen: true,
        }));

        const sortedNames = result.current.filteredConfigs.map(c => c.name);
        
        expect(sortedNames).toEqual([
            'Config B',
            'Config C',
            'Config A'
        ]);
    });

    it('falls back to smart sorting when no ordering field exists', () => {
        const mockConfigs = [
            { name: 'C Normal', filters: {}, statistics: true, notify: false },
            { name: 'B Notify', filters: {}, statistics: true, notify: true },
            { name: 'A NoStats', filters: {}, statistics: false, notify: false },
        ];

        const { result } = renderHook(() => useFilterDropdown({
            configs: mockConfigs as any,
            configName: '',
            onLoad: vi.fn(),
            onSave: vi.fn(),
            onDelete: vi.fn(),
            setIsOpen: vi.fn(),
            isOpen: true,
        }));

        const sortedNames = result.current.filteredConfigs.map(c => c.name);
        
        expect(sortedNames).toEqual([
            'B Notify',
            'C Normal',
            'A NoStats'
        ]);
    });

    it('handles mixed configs with and without ordering', () => {
        const mockConfigs = [
            { name: 'With Order 1', filters: {}, ordering: 1 },
            { name: 'No Order A', filters: {}, notify: true },
            { name: 'With Order 0', filters: {}, ordering: 0 },
            { name: 'No Order B', filters: {} },
        ];

        const { result } = renderHook(() => useFilterDropdown({
            configs: mockConfigs as any,
            configName: '',
            onLoad: vi.fn(),
            onSave: vi.fn(),
            onDelete: vi.fn(),
            setIsOpen: vi.fn(),
            isOpen: true,
        }));

        const sortedNames = result.current.filteredConfigs.map(c => c.name);
        
        expect(sortedNames).toEqual([
            'With Order 0',
            'With Order 1',
            'No Order A',
            'No Order B'
        ]);
    });
});
