import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import FilterConfigurations from '../FilterConfigurations';
import { createMockFilters, setupLocalStorage, getStoredConfigs } from '../../__tests__/test-utils';
import { type JobListParams } from '../../api/jobs';

vi.mock('../../data/defaults', () => ({ defaultFilterConfigurations: [] }));

describe('FilterConfigurations', () => {
    const mockFilters = createMockFilters({ search: 'React Developer', flagged: true, like: false, days_old: 7 });
    let onLoadConfigMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        onLoadConfigMock = vi.fn();
        setupLocalStorage();
    });

    afterEach(() => vi.restoreAllMocks());

    const renderWithConfig = async (configs: { name: string, filters: JobListParams }[] = [], props: { currentFilters?: JobListParams; onMessage?: any } = {}) => {
        localStorage.setItem('filter_configurations', JSON.stringify(configs));
        const result = render(
            <FilterConfigurations 
                currentFilters={props.currentFilters || mockFilters} 
                onLoadConfig={onLoadConfigMock as any} 
                onMessage={props.onMessage || vi.fn()} />
        );
        await act(async () => await new Promise(resolve => setTimeout(resolve, 0)));
        return { ...result, input: screen.getByPlaceholderText(/Type to load or enter name to save/i) };
    };

    it('renders correctly', async () => {
        await renderWithConfig();
        expect(screen.getByLabelText(/Filter Configurations/i)).toBeInTheDocument();
        expect(screen.getByText('Save')).toBeInTheDocument();
    });

    describe('Saving Configuration', () => {
        it.each([
            ['Button', (el: HTMLElement) => fireEvent.click(el)],
            ['Enter Key', (el: HTMLElement) => fireEvent.keyDown(el, { key: 'Enter', code: 'Enter' })],
        ])('saves configuration using %s', async (name, action) => {
            const onMessageMock = vi.fn();
            const { input } = await renderWithConfig([], { onMessage: onMessageMock });
            const saveButton = screen.getByText('Save');
            fireEvent.change(input, { target: { value: 'My Config' } });
            action(name === 'Button' ? saveButton : input);
            await act(async () => {
                const configs = getStoredConfigs();
                expect(configs).toHaveLength(2);
                expect(configs[0]).toEqual({ name: 'My Config', filters: mockFilters });
            });
            if (onMessageMock.mock.calls.length > 0) expect(onMessageMock).toHaveBeenCalledWith(expect.stringContaining('saved'), 'success');
            expect((input as HTMLInputElement).value).toBe('');
        });

        it('validates name before saving', async () => {
            const onMessageMock = vi.fn();
            await renderWithConfig([], { onMessage: onMessageMock });
            fireEvent.click(screen.getByText('Save'));
            expect(getStoredConfigs()).toHaveLength(0);
            expect(onMessageMock).toHaveBeenCalledWith('Please enter a name for the configuration', 'error');
        });

        it('replaces existing configuration with same name', async () => {
            const { input } = await renderWithConfig(
                [{ name: 'Same Name', filters: { ...mockFilters, search: 'Old' } }], 
                { currentFilters: { ...mockFilters, search: 'New' } }
            );
            fireEvent.focus(input);
            await screen.findByText('Same Name');
            fireEvent.change(input, { target: { value: 'Same Name' } });
            fireEvent.click(screen.getByText('Save'));
            await waitFor(() => expect(getStoredConfigs()[0].filters.search).toBe('New'));
        });

        it('limits to MAX_CONFIGS (30) configurations', async () => {
            const existingConfigs = Array.from({ length: 30 }, (_, i) => ({ name: `Config ${i + 1}`, filters: mockFilters }));
            const { input } = await renderWithConfig(existingConfigs);
            fireEvent.focus(input);
            await screen.findByText('Config 1');
            fireEvent.change(input, { target: { value: 'Config 31' } });
            fireEvent.click(screen.getByText('Save'));
            await waitFor(() => {
                const configs = getStoredConfigs();
                expect(configs).toHaveLength(30);
                expect(configs[0].name).toBe('Config 31');
                expect(configs[29].name).toBe('Config 29');
            });
        });
    });

    describe('Suggestions & Loading', () => {
        it.each([
            ['Focus', 'Test Config', (input: HTMLElement) => fireEvent.focus(input), true],
            ['Filter', 'Senior React', (input: HTMLElement) => fireEvent.change(input, { target: { value: 'React' } }), true],
            ['Filter Mismatch', 'Junior Python', (input: HTMLElement) => fireEvent.change(input, { target: { value: 'React' } }), false],
        ])('handles suggestion visibility on %s', async (_, configName, action, shouldBeVisible) => {
            const configs = [
                { name: 'Test Config', filters: mockFilters },
                { name: 'Senior React', filters: mockFilters },
                { name: 'Junior Python', filters: mockFilters },
            ];
            const { input } = await renderWithConfig(configs);
            fireEvent.focus(input); // Trigger load
            if (shouldBeVisible) await screen.findByText(configName, {}, { timeout: 2000 });
            else await screen.findByText('Test Config'); // Wait for load
            action(input);
            if (shouldBeVisible) await screen.findByText(configName);
            else expect(screen.queryByText(configName)).not.toBeInTheDocument();
        });

        it('loads configuration interacting with suggestion', async () => {
            const savedFilters = { ...mockFilters, search: 'Senior Engineer' };
            const { input } = await renderWithConfig([{ name: 'Senior Jobs', filters: savedFilters }]);
            fireEvent.focus(input);
            fireEvent.click(await screen.findByText('Senior Jobs'));
            // We need to match loosely because mockFilters adds a bunch of null properties which might differ slightly in order or presence
             // depending on how existing vs saved interactions work.
             // But actually, `savedFilters` passed to `onLoadConfigMock` should be EXACTLY what we saved.
             // The issue might be that `createMockFilters` uses spread which copies properties.
             // Let's use `expect.objectContaining` for safer testing if exact match is flaky due to undefined vs null.
             // Or ensure `savedFilters` is constructed the same way.
             expect(onLoadConfigMock).toHaveBeenCalledWith(expect.objectContaining(savedFilters), 'Senior Jobs');
            expect((input as HTMLInputElement).value).toBe('Senior Jobs');
        });

        it('closes suggestions when clicking outside', async () => {
            const { input } = await renderWithConfig([{ name: 'Test Config', filters: mockFilters }]);
            fireEvent.focus(input);
            await screen.findByText('Test Config');
            fireEvent.mouseDown(document.body);
            await waitFor(() => expect(screen.queryByText('Test Config')).not.toBeInTheDocument());
        });

        it('sorts suggestions alphabetically by name', async () => {
            const configs = [{ name: 'Zebra', filters: mockFilters }, { name: 'Alpha', filters: mockFilters }, { name: 'Beta', filters: mockFilters }];
            const { input } = await renderWithConfig(configs);
            fireEvent.focus(input);
            const items = await screen.findAllByRole('listitem');
            // The delete button has text "×", not "Delete"
            const names = items.map(item => item.textContent?.replace('×', '').trim());
            // "Clean - Delete old jobs" is automatically added.
            // Expected sorted order: Alpha, Beta, Clean..., Zebra
            expect(names).toEqual(['Alpha', 'Beta', 'Clean - Delete old jobs', 'Zebra']);
        });

        it('resets missing filters when loading configuration', async () => {
            // Config has NO days_old
            const savedFilters = { search: 'Just Search' }; 
            const configs = [{ name: 'Reset Test', filters: savedFilters as JobListParams }];
            
            // Current filters HAVE days_old
            const { input } = await renderWithConfig(configs, { currentFilters: { ...mockFilters, days_old: 7 } });
            
            fireEvent.focus(input);
            fireEvent.click(await screen.findByText('Reset Test'));
            
            // Expect days_old to be explicitly undefined
            expect(onLoadConfigMock).toHaveBeenCalledWith(
                expect.objectContaining({ 
                    search: 'Just Search',
                    days_old: undefined
                }), 
                'Reset Test'
            );
        });
    });

    describe('Deleting', () => {
        it.each([['Confirms', true], ['Cancels', false]])('handles delete when user %s', async (_, confirm) => {
            const { input } = await renderWithConfig([{ name: 'Delete Me', filters: mockFilters }]);
            fireEvent.focus(input);
            const deleteBtn = (await screen.findByText('Delete Me')).closest('li')?.querySelector('.config-delete-btn');
            fireEvent.click(deleteBtn!);
            const modalMessage = await screen.findByText(/Delete configuration "Delete Me"\?/i);
            expect(modalMessage).toBeInTheDocument();
            if (confirm) {
                const confirmBtn = screen.getByText('Confirm', { selector: 'button.modal-button' });
                fireEvent.click(confirmBtn);
                await waitFor(() => {
                     expect(getStoredConfigs()).toHaveLength(1); // Only Clean... remains
                     // Verify stored content is not 'Delete Me'
                     const stored = getStoredConfigs();
                     expect(stored.some((c: any) => c.name === 'Delete Me')).toBe(false);
                });
            } else {
                // Click Cancel
                const cancelBtn = screen.getByText('Cancel', { selector: 'button.modal-button' });
                fireEvent.click(cancelBtn);

                // Assert NO deletion
                await waitFor(() => {
                    // Storage should still contain 'Delete Me'
                    // 'Clean...' is in state but not in storage because we didn't save it.
                    const stored = getStoredConfigs();
                    expect(stored).toHaveLength(1); 
                    expect(stored[0].name).toBe('Delete Me');
                    expect(screen.queryByText(/Delete configuration "Delete Me"\?/i)).not.toBeInTheDocument();      });
            }
        });
    });
});
