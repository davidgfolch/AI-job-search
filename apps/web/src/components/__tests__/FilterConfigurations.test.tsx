import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import FilterConfigurations from '../FilterConfigurations';
import { createMockFilters, setupLocalStorage, setupWindowMocks, getStoredConfigs } from '../../__tests__/test-utils';
import { type JobListParams } from '../../api/jobs';

describe('FilterConfigurations', () => {
    const mockFilters = createMockFilters({
        search: 'React Developer',
        flagged: true,
        like: false,
        days_old: 7,
    });

    let onLoadConfigMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        onLoadConfigMock = vi.fn();
        setupLocalStorage();
        setupWindowMocks();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    const renderComponent = (props: { currentFilters?: JobListParams; onMessage?: any } = {}) => {
        return render(
            <FilterConfigurations 
                currentFilters={props.currentFilters || mockFilters} 
                onLoadConfig={onLoadConfigMock as any} 
                onMessage={props.onMessage} 
            />
        );
    };

    it('renders correctly', () => {
        renderComponent();
        expect(screen.getByLabelText(/Filter Configurations/i)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Type to load or enter name to save/i)).toBeInTheDocument();
        expect(screen.getByText('Save')).toBeInTheDocument();
    });

    describe('Saving Configuration', () => {
        it.each([
            ['Button', (_input: HTMLElement, btn: HTMLElement) => fireEvent.click(btn)],
            ['Enter Key', (input: HTMLElement, _btn: HTMLElement) => fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' })],
        ])('saves configuration using %s', async (_, action) => {
            const onMessageMock = vi.fn();
            renderComponent({ onMessage: onMessageMock });
            const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
            const saveButton = screen.getByText('Save');

            fireEvent.change(input, { target: { value: 'My Config' } });
            action(input, saveButton);

            await waitFor(() => {
                const configs = getStoredConfigs();
                expect(configs).toHaveLength(1);
                expect(configs[0].name).toBe('My Config');
                expect(configs[0].filters).toEqual(mockFilters);
            });

            if (onMessageMock.mock.calls.length > 0) { 
                 expect(onMessageMock).toHaveBeenCalledWith(expect.stringContaining('saved'), 'success');
            }
            expect((input as HTMLInputElement).value).toBe(''); // Clears input
        });

        it('validates name before saving', () => {
            renderComponent();
            fireEvent.click(screen.getByText('Save'));
            expect(localStorage.getItem('filter_configurations')).toBeNull();
            expect(window.alert).toHaveBeenCalledWith('Please enter a name for the configuration');
        });

        it('replaces existing configuration with same name', async () => {
            const oldFilters = { ...mockFilters, search: 'Old' };
            localStorage.setItem('filter_configurations', JSON.stringify([{ name: 'Same Name', filters: oldFilters }]));
            
            const newFilters = { ...mockFilters, search: 'New' };
            renderComponent({ currentFilters: newFilters });
            
            // Wait for initial load to avoid overwriting state with empty if effect runs late (though here we are saving new state based on props)
            // Actually saveConfiguration uses `savedConfigs` state to append/replace. 
            // So we MUST wait for initial load, otherwise savedConfigs is empty and we might duplicate or lose history if we had logic for that.
            // But here we just replace or add. Logic: `savedConfigs.filter(...)`. If empty, we just add. 
            // If the goal is to replace, we must know about existing ones.
            // So YES, we must wait for load.
            
            // Trigger load by just waiting? No visual indicator unless we open dropdown.
            // But checking persistence requires correct state update. The useEffect updates state.
            // We can wait for state to be populated? We can't see state easily.
            // But we can check if the dropdown would have items.
            const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
            fireEvent.focus(input);
            await screen.findByText('Same Name'); // Wait for it to be loaded

            fireEvent.change(input, { target: { value: 'Same Name' } });
            fireEvent.click(screen.getByText('Save'));

            await waitFor(() => {
                const configs = getStoredConfigs();
                expect(configs).toHaveLength(1);
                expect(configs[0].filters.search).toBe('New');
            });
        });

        it('limits to MAX_CONFIGS (30) configurations', async () => {
            const existingConfigs = Array.from({ length: 30 }, (_, i) => ({
                name: `Config ${i + 1}`,
                filters: mockFilters,
            }));
            localStorage.setItem('filter_configurations', JSON.stringify(existingConfigs));

            renderComponent();

            // Wait for load
            const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
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
            localStorage.setItem('filter_configurations', JSON.stringify(configs));
            renderComponent();

            const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
            // We need to wait for data load before interacting for filter check
            // Open first to trigger wait
            fireEvent.focus(input);
            if (shouldBeVisible) {
                await screen.findByText(configName, {}, { timeout: 2000 });
            } else {
                 // checking for absence is trickier if we need to wait for load first. 
                 // We can wait for one that SHOULD be there (like Test Config) then check absence?
                 // Or just wait for "Test Config" to appear (load complete) then filter
                 await screen.findByText('Test Config');
            }

            action(input); // Now perform the specific action (focus again or change)

            if (shouldBeVisible) {
                await screen.findByText(configName); // Should still be there or appear
            } else {
                expect(screen.queryByText(configName)).not.toBeInTheDocument();
            }
        });

        it('loads configuration interacting with suggestion', async () => {
             const savedFilters = { ...mockFilters, search: 'Senior Engineer' };
             localStorage.setItem('filter_configurations', JSON.stringify([{ name: 'Senior Jobs', filters: savedFilters }]));
             renderComponent();

             const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
             fireEvent.focus(input);
             
             const suggestion = await screen.findByText('Senior Jobs');
             fireEvent.click(suggestion);

             expect(onLoadConfigMock).toHaveBeenCalledWith(savedFilters);
             expect((input as HTMLInputElement).value).toBe('Senior Jobs');
        });

        it('closes suggestions when clicking outside', async () => {
            localStorage.setItem('filter_configurations', JSON.stringify([{ name: 'Test Config', filters: mockFilters }]));
            renderComponent();
            fireEvent.focus(screen.getByPlaceholderText(/Type to load or enter name to save/i));
            
            await screen.findByText('Test Config');

            fireEvent.mouseDown(document.body);
            await waitFor(() => expect(screen.queryByText('Test Config')).not.toBeInTheDocument());
        });
    });

    describe('Deleting', () => {
        it.each([
            ['Confirms', true, 0],
            ['Cancels', false, 1]
        ])('handles delete when user %s', async (_, confirmValue, expectedLength) => {
            vi.spyOn(window, 'confirm').mockImplementation(() => confirmValue);
            localStorage.setItem('filter_configurations', JSON.stringify([{ name: 'Delete Me', filters: mockFilters }]));
            renderComponent();

            const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
            fireEvent.focus(input);
            
            // Wait for item
            const item = await screen.findByText('Delete Me');
            // Find delete button within the item
            // The item text is "Delete Me", but the button is sibling or child.
            // Using closest li might be safer
            const li = item.closest('li');
            const deleteBtn = li?.querySelector('.config-delete-btn');
            
            fireEvent.click(deleteBtn!);

            await waitFor(() => {
                expect(getStoredConfigs()).toHaveLength(expectedLength);
            });
        });
    });
});
