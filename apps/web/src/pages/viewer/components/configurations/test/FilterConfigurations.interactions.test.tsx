// @vitest-environment jsdom
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { type JobListParams } from '../../../api/ViewerApi';
import { mockFilters, setup, configureMockServiceBehavior } from '../../../test/FilterConfigurationsTestUtils.tsx';

describe('FilterConfigurations Interactions', () => {
    const isLoadedRef = { value: false };

    beforeEach(() => {
        configureMockServiceBehavior(isLoadedRef);
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('replaces existing configuration', async () => {
        const { input } = await setup(
            [{ name: 'Same', filters: { ...mockFilters, search: 'Old' } }], 
            { currentFilters: { ...mockFilters, search: 'New' } },
            isLoadedRef
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
        const { input } = await setup(configs, {}, isLoadedRef);
        
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
        const { input, onLoad } = await setup([{ name: 'Senior', filters: saved }], {}, isLoadedRef);
        
        fireEvent.focus(input);
        fireEvent.click(await screen.findByText('Senior'));
        
        expect(onLoad).toHaveBeenCalledWith(expect.objectContaining(saved), 'Senior');
    });

    it('closes suggestions on outside click', async () => {
        const { input } = await setup([{ name: 'Test', filters: mockFilters }], {}, isLoadedRef);
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
        const { input } = await setup(configs, {}, isLoadedRef);
        fireEvent.focus(input);
        
        const items = await screen.findAllByRole('listitem');
        const names = items.map(i => i.textContent?.replace(/[\+\d+\📈📉🔔🔕×]/g, '').trim());
        expect(names).toEqual(['A', 'Z']);
    });

    it('resets missing filters', async () => {
        const saved = { search: 'S', days_old: undefined };
        const { input, onLoad } = await setup(
            [{ name: 'R', filters: saved as JobListParams }], 
            { currentFilters: { ...mockFilters, days_old: 7 } },
            isLoadedRef
        );
        
        fireEvent.focus(input);
        fireEvent.click(await screen.findByText('R'));
        
        expect(onLoad).toHaveBeenCalledWith(expect.objectContaining({ search: 'S', days_old: undefined }), 'R');
    });

    it.each([['Confirms', true], ['Cancels', false]])('handles delete when user %s', async (_, confirm) => {
        const { input } = await setup([{ name: 'Del', filters: mockFilters }], {}, isLoadedRef);
        
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
        const { input } = await setup([{ name: 'Active', filters: mockFilters }], {}, isLoadedRef);
        
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
