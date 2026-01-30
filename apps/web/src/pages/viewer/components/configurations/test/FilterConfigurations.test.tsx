import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import FilterConfigurations from '../../FilterConfigurations';
import { createMockFilters } from '../../../test/test-utils';
import { type JobListParams } from '../../../api/ViewerApi';
import { mockLocalStorage } from '../../../../../test/mocks/storageMocks';

// Mock defaults
vi.mock('../../../../common/api/defaults', () => ({ 
    defaultFilterConfigurations: []
}));

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

vi.mock('../../../hooks/FilterConfigService', () => ({
    FilterConfigService: vi.fn(function() { return mockService; })
}));

describe('FilterConfigurations', () => {
    let isLoaded = false;
    const mockFilters = createMockFilters({ search: 'React Developer', flagged: true, like: false, days_old: 7 });

    beforeEach(() => {
        mockLocalStorage();
        vi.clearAllMocks();
        
        // Reset service mock state
        mockService.load.mockImplementation(async (defaults: any) => {
             const stored = JSON.parse(localStorage.getItem('filter_configurations') || '[]');
             isLoaded = true;
             return stored.length ? stored : defaults;
        });
        mockService.save.mockImplementation(async (configs: any) => {
            const limited = configs.slice(0, 30);
            localStorage.setItem('filter_configurations', JSON.stringify(limited));
        });
        
        isLoaded = false;
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    async function setup(configs: { name: string, filters: JobListParams }[] = [], props: any = {}) {
        if (configs.length > 0) {
            localStorage.setItem('filter_configurations', JSON.stringify(configs));
        }
        
        const onLoad = vi.fn();
        const result = render(
            <FilterConfigurations 
                currentFilters={props.currentFilters || mockFilters} 
                onLoadConfig={onLoad} 
                onMessage={props.onMessage || vi.fn()} 
            />
        );
        
        await waitFor(() => {
            if (!isLoaded) throw new Error('Configurations not yet loaded');
        });
        
        return { 
            ...result, 
            input: screen.getByPlaceholderText(/Type to load or enter name to save/i) as HTMLInputElement, 
            onLoad 
        };
    }

    it('renders correctly', async () => {
        await setup();
        expect(screen.getByLabelText(/Filter Configurations/i)).toBeInTheDocument();
        expect(screen.getByText('Save')).toBeInTheDocument();
    });

    it.each([
        ['Button', (el: HTMLElement) => fireEvent.click(el)],
        ['Enter Key', (el: HTMLElement) => fireEvent.keyDown(el, { key: 'Enter', code: 'Enter' })],
    ])('saves configuration using %s', async (_, action) => {
        const onMessage = vi.fn();
        const { input } = await setup([], { onMessage });
        
        fireEvent.change(input, { target: { value: 'My Config' } });
        // Start waiting for the success message to appear which indicates save completion
        action(_ === 'Button' ? screen.getByText('Save') : input);
        
        await waitFor(() => {
            expect(localStorage.getItem('filter_configurations')).toContain('My Config');
            expect(input.value).toBe('');
        });
        
        if (onMessage.mock.calls.length) {
            expect(onMessage).toHaveBeenCalledWith(expect.stringContaining('saved'), 'success');
        }
    });

    it('validates name before saving', async () => {
        const onMessage = vi.fn();
        await setup([], { onMessage });
        fireEvent.click(screen.getByText('Save'));
        expect(localStorage.getItem('filter_configurations')).toBeNull();
        expect(onMessage).toHaveBeenCalledWith('Please enter a name for the configuration', 'error');
    });

    it('replaces existing configuration', async () => {
        const { input } = await setup(
            [{ name: 'Same', filters: { ...mockFilters, search: 'Old' } }], 
            { currentFilters: { ...mockFilters, search: 'New' } }
        );
        
        fireEvent.focus(input);
        await screen.findByText('Same'); // Wait for list to populate
        
        fireEvent.change(input, { target: { value: 'Same' } });
        fireEvent.click(screen.getByText('Save'));
        
        await waitFor(() => {
            const stored = JSON.parse(localStorage.getItem('filter_configurations') || '[]');
            expect(stored[0].filters.search).toBe('New');
        });
    });

    it('limits to MAX_CONFIGS (30)', async () => {
        const configs = Array.from({ length: 30 }, (_, i) => ({ name: `C${i + 1}`, filters: mockFilters }));
        const { input } = await setup(configs);
        
        fireEvent.focus(input);
        await screen.findByText('C1');
        
        fireEvent.change(input, { target: { value: 'C31' } });
        fireEvent.click(screen.getByText('Save'));
        
        await waitFor(() => {
            const stored = JSON.parse(localStorage.getItem('filter_configurations') || '[]');
            expect(stored).toHaveLength(30);
            expect(stored[0].name).toBe('C31');
        });
    });

    it.each([
        ['Focus', undefined, 'Test', true],
        ['Filter Match', 'React', 'React', true],
        ['Filter Mismatch', 'React', 'Python', false],
    ])('visibility check: %s', async (_, typeText, checkName, shouldBeVisible) => {
        const configs = [
            { name: 'Test', filters: mockFilters }, 
            { name: 'React', filters: mockFilters }, 
            { name: 'Python', filters: mockFilters }
        ];
        const { input } = await setup(configs);
        
        fireEvent.focus(input);
        if (typeText) {
             fireEvent.change(input, { target: { value: typeText } });
        }
        
        if (shouldBeVisible) {
             await screen.findByText(checkName, {}, { timeout: 2000 });
        } else {
             await waitFor(() => {
                 expect(screen.queryByText(checkName)).not.toBeInTheDocument();
             });
        }
    });

    it('loads configuration', async () => {
        const saved = { ...mockFilters, search: 'Senior' };
        const { input, onLoad } = await setup([{ name: 'Senior', filters: saved }]);
        
        fireEvent.focus(input);
        fireEvent.click(await screen.findByText('Senior'));
        
        expect(onLoad).toHaveBeenCalledWith(expect.objectContaining(saved), 'Senior');
    });

    it('closes suggestions on outside click', async () => {
        const { input } = await setup([{ name: 'Test', filters: mockFilters }]);
        fireEvent.focus(input);
        await screen.findByText('Test');
        
        fireEvent.mouseDown(document.body);
        await waitFor(() => {
             const list = screen.queryByRole('list');
             expect(list).not.toBeInTheDocument();
        });
    });

    it('sorts suggestions alphabetically', async () => {
        const configs = [{ name: 'Z', filters: mockFilters }, { name: 'A', filters: mockFilters }];
        const { input } = await setup(configs);
        fireEvent.focus(input);
        
        const items = await screen.findAllByRole('listitem');
        const names = items.map(i => i.textContent?.replace('×', '').trim());
        expect(names).toEqual(['A', 'Z']);
    });

    it('resets missing filters', async () => {
        const saved = { search: 'S', days_old: undefined };
        const { input, onLoad } = await setup(
            [{ name: 'R', filters: saved as JobListParams }], 
            { currentFilters: { ...mockFilters, days_old: 7 } }
        );
        
        fireEvent.focus(input);
        fireEvent.click(await screen.findByText('R'));
        
        expect(onLoad).toHaveBeenCalledWith(expect.objectContaining({ search: 'S', days_old: undefined }), 'R');
    });

    it.each([['Confirms', true], ['Cancels', false]])('handles delete when user %s', async (_, confirm) => {
        const { input } = await setup([{ name: 'Del', filters: mockFilters }]);
        
        fireEvent.focus(input);
        const deleteBtn = (await screen.findByText('Del')).closest('li')?.querySelector('.config-delete-btn');
        fireEvent.click(deleteBtn!);
        
        await screen.findByText(/Delete configuration "Del"\?/i);
        
        fireEvent.click(screen.getByText(confirm ? 'Confirm' : 'Cancel', { selector: 'button.modal-button' }));
        
        await waitFor(() => {
            const stored = JSON.parse(localStorage.getItem('filter_configurations') || '[]');
            if (confirm) {
                expect(stored.some((c: any) => c.name === 'Del')).toBe(false);
            } else {
                expect(stored[0].name).toBe('Del');
            }
        });
    });

    it('resets input name if deleted configuration was active', async () => {
        const { input } = await setup([{ name: 'Active', filters: mockFilters }]);
        
        // Select it first
        fireEvent.focus(input);
        fireEvent.click(await screen.findByText('Active'));
        expect(input.value).toBe('Active');

        // Delete it
        fireEvent.focus(input);
        const deleteBtn = (await screen.findByText('Active')).closest('li')?.querySelector('.config-delete-btn');
        fireEvent.click(deleteBtn!);
        
        fireEvent.click(screen.getByText('Confirm', { selector: 'button.modal-button' }));
        
        await waitFor(() => {
            expect(input.value).toBe('');
        });
    });
});

