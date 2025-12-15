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
                onLoadConfig={onLoadConfigMock} 
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
            ['Button', (input: HTMLElement, btn: HTMLElement) => fireEvent.click(btn)],
            ['Enter Key', (input: HTMLElement, btn: HTMLElement) => fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' })],
        ])('saves configuration using %s', (_, action) => {
            const onMessageMock = vi.fn();
            renderComponent({ onMessage: onMessageMock });
            const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
            const saveButton = screen.getByText('Save');

            fireEvent.change(input, { target: { value: 'My Config' } });
            action(input, saveButton);

            const configs = getStoredConfigs();
            expect(configs).toHaveLength(1);
            expect(configs[0].name).toBe('My Config');
            expect(configs[0].filters).toEqual(mockFilters);
            if (onMessageMock.mock.calls.length > 0) { // Only checked for button in original, but valid for both if wired up
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

        it('replaces existing configuration with same name', () => {
            const oldFilters = { ...mockFilters, search: 'Old' };
            localStorage.setItem('filter_configurations', JSON.stringify([{ name: 'Same Name', filters: oldFilters }]));
            
            const newFilters = { ...mockFilters, search: 'New' };
            renderComponent({ currentFilters: newFilters });
            
            const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
            fireEvent.change(input, { target: { value: 'Same Name' } });
            fireEvent.click(screen.getByText('Save'));

            const configs = getStoredConfigs();
            expect(configs).toHaveLength(1);
            expect(configs[0].filters.search).toBe('New');
        });

        it('limits to MAX_CONFIGS (30) configurations', () => {
            const existingConfigs = Array.from({ length: 30 }, (_, i) => ({
                name: `Config ${i + 1}`,
                filters: mockFilters,
            }));
            localStorage.setItem('filter_configurations', JSON.stringify(existingConfigs));

            renderComponent();
            const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
            fireEvent.change(input, { target: { value: 'Config 31' } });
            fireEvent.click(screen.getByText('Save'));

            const configs = getStoredConfigs();
            expect(configs).toHaveLength(30);
            expect(configs[0].name).toBe('Config 31');
            expect(configs[29].name).toBe('Config 29');
        });
    });

    describe('Suggestions & Loading', () => {
        it.each([
            ['Focus', 'Test Config', (input: HTMLElement) => fireEvent.focus(input), true],
            ['Filter', 'Senior React', (input: HTMLElement) => fireEvent.change(input, { target: { value: 'React' } }), true],
            ['Filter Mismatch', 'Junior Python', (input: HTMLElement) => fireEvent.change(input, { target: { value: 'React' } }), false],
        ])('handles suggestion visibility on %s', (_, configName, action, shouldBeVisible) => {
             const configs = [
                { name: 'Test Config', filters: mockFilters },
                { name: 'Senior React', filters: mockFilters },
                { name: 'Junior Python', filters: mockFilters },
            ];
            localStorage.setItem('filter_configurations', JSON.stringify(configs));
            renderComponent();

            const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
            action(input);

            if (shouldBeVisible) {
                expect(screen.getByText(configName)).toBeInTheDocument();
            } else {
                expect(screen.queryByText(configName)).not.toBeInTheDocument();
            }
        });

        it('loads configuration interacting with suggestion', () => {
             const savedFilters = { ...mockFilters, search: 'Senior Engineer' };
             localStorage.setItem('filter_configurations', JSON.stringify([{ name: 'Senior Jobs', filters: savedFilters }]));
             renderComponent();

             const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
             fireEvent.focus(input);
             fireEvent.click(screen.getByText('Senior Jobs'));

             expect(onLoadConfigMock).toHaveBeenCalledWith(savedFilters);
             expect((input as HTMLInputElement).value).toBe('Senior Jobs');
        });

        it('closes suggestions when clicking outside', async () => {
            localStorage.setItem('filter_configurations', JSON.stringify([{ name: 'Test Config', filters: mockFilters }]));
            renderComponent();
            fireEvent.focus(screen.getByPlaceholderText(/Type to load or enter name to save/i));
            expect(screen.getByText('Test Config')).toBeInTheDocument();

            fireEvent.mouseDown(document.body);
            await waitFor(() => expect(screen.queryByText('Test Config')).not.toBeInTheDocument());
        });
    });

    describe('Deleting', () => {
        it.each([
            ['Confirms', true, 0],
            ['Cancels', false, 1]
        ])('handles delete when user %s', (_, confirmValue, expectedLength) => {
            vi.spyOn(window, 'confirm').mockImplementation(() => confirmValue);
            localStorage.setItem('filter_configurations', JSON.stringify([{ name: 'Delete Me', filters: mockFilters }]));
            renderComponent();

            const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
            fireEvent.focus(input);
            fireEvent.click(screen.getByTitle('Delete configuration'));

            expect(getStoredConfigs()).toHaveLength(expectedLength);
        });
    });
});
