import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import FilterConfigurations from '../FilterConfigurations';
import { JobListParams } from '../../api/jobs';

describe('FilterConfigurations', () => {
    const mockFilters: JobListParams = {
        page: 1,
        size: 20,
        search: 'React Developer',
        flagged: true,
        like: false,
        days_old: 7,
        order: 'created desc',
    };

    let onLoadConfigMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        onLoadConfigMock = vi.fn();
        localStorage.clear();
        // Mock window.alert and window.confirm
        vi.spyOn(window, 'alert').mockImplementation(() => { });
        vi.spyOn(window, 'confirm').mockImplementation(() => true);
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('renders input and save button correctly', () => {
        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        expect(screen.getByLabelText(/Filter Configurations/i)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Type to load or enter name to save/i)).toBeInTheDocument();
        expect(screen.getByText('Save')).toBeInTheDocument();
    });

    it('saves configuration to localStorage', () => {
        const onMessageMock = vi.fn();
        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} onMessage={onMessageMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
        const saveButton = screen.getByText('Save');

        fireEvent.change(input, { target: { value: 'My Config' } });
        fireEvent.click(saveButton);

        const stored = localStorage.getItem('filter_configurations');
        expect(stored).toBeTruthy();

        const configs = JSON.parse(stored!);
        expect(configs).toHaveLength(1);
        expect(configs[0].name).toBe('My Config');
        expect(configs[0].filters).toEqual(mockFilters);
        expect(onMessageMock).toHaveBeenCalledWith('Configuration "My Config" saved!', 'success');
    });

    it('saves configuration on Enter key press', () => {
        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);

        fireEvent.change(input, { target: { value: 'Quick Config' } });
        fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

        const stored = localStorage.getItem('filter_configurations');
        expect(stored).toBeTruthy();

        const configs = JSON.parse(stored!);
        expect(configs[0].name).toBe('Quick Config');
    });

    it('does not save with empty name', () => {
        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        const saveButton = screen.getByText('Save');
        fireEvent.click(saveButton);

        const stored = localStorage.getItem('filter_configurations');
        expect(stored).toBeNull();
        expect(window.alert).toHaveBeenCalledWith('Please enter a name for the configuration');
    });

    it('clears input after saving', () => {
        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i) as HTMLInputElement;
        const saveButton = screen.getByText('Save');

        fireEvent.change(input, { target: { value: 'Test Config' } });
        fireEvent.click(saveButton);

        expect(input.value).toBe('');
    });

    it('shows suggestions dropdown when input is focused', () => {
        const config = { name: 'Test Config', filters: mockFilters };
        localStorage.setItem('filter_configurations', JSON.stringify([config]));

        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
        fireEvent.focus(input);

        expect(screen.getByText('Test Config')).toBeInTheDocument();
    });

    it('filters suggestions based on input text', () => {
        const configs = [
            { name: 'Senior React Jobs', filters: mockFilters },
            { name: 'Junior Python Jobs', filters: mockFilters },
        ];
        localStorage.setItem('filter_configurations', JSON.stringify(configs));

        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
        fireEvent.change(input, { target: { value: 'React' } });

        expect(screen.getByText('Senior React Jobs')).toBeInTheDocument();
        expect(screen.queryByText('Junior Python Jobs')).not.toBeInTheDocument();
    });

    it('loads configuration when clicking on suggestion', () => {
        const savedFilters: JobListParams = {
            page: 1,
            size: 10,
            search: 'Senior Engineer',
            applied: true,
        };
        const config = { name: 'Senior Jobs', filters: savedFilters };
        localStorage.setItem('filter_configurations', JSON.stringify([config]));

        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
        fireEvent.focus(input);

        const suggestion = screen.getByText('Senior Jobs');
        fireEvent.click(suggestion);

        expect(onLoadConfigMock).toHaveBeenCalledWith(savedFilters);
    });

    it('clears input after loading a configuration', async () => {
        const config = { name: 'Test Config', filters: mockFilters };
        localStorage.setItem('filter_configurations', JSON.stringify([config]));

        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i) as HTMLInputElement;
        fireEvent.focus(input);

        const suggestion = screen.getByText('Test Config');
        fireEvent.click(suggestion);

        // After loading, the config name should be visible in the input
        expect(input.value).toBe('Test Config');
    });

    it('deletes configuration from localStorage', () => {
        const config = { name: 'Delete Me', filters: mockFilters };
        localStorage.setItem('filter_configurations', JSON.stringify([config]));

        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
        fireEvent.focus(input);

        const deleteButton = screen.getByTitle('Delete configuration');
        fireEvent.click(deleteButton);

        const stored = localStorage.getItem('filter_configurations');
        const configs = JSON.parse(stored!);
        expect(configs).toHaveLength(0);
    });

    it('does not delete if user cancels confirmation', () => {
        vi.spyOn(window, 'confirm').mockImplementation(() => false);

        const config = { name: 'Keep Me', filters: mockFilters };
        localStorage.setItem('filter_configurations', JSON.stringify([config]));

        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
        fireEvent.focus(input);

        const deleteButton = screen.getByTitle('Delete configuration');
        fireEvent.click(deleteButton);

        const stored = localStorage.getItem('filter_configurations');
        const configs = JSON.parse(stored!);
        expect(configs).toHaveLength(1);
        expect(configs[0].name).toBe('Keep Me');
    });

    it('loads configurations from localStorage on mount', () => {
        const configs = [
            { name: 'Config 1', filters: mockFilters },
            { name: 'Config 2', filters: mockFilters },
        ];
        localStorage.setItem('filter_configurations', JSON.stringify(configs));

        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
        fireEvent.focus(input);

        expect(screen.getByText('Config 1')).toBeInTheDocument();
        expect(screen.getByText('Config 2')).toBeInTheDocument();
    });

    it('replaces existing configuration with same name', () => {
        const oldFilters: JobListParams = { page: 1, size: 20, search: 'Old' };
        const config = { name: 'Same Name', filters: oldFilters };
        localStorage.setItem('filter_configurations', JSON.stringify([config]));

        const newFilters: JobListParams = { page: 1, size: 20, search: 'New' };
        render(<FilterConfigurations currentFilters={newFilters} onLoadConfig={onLoadConfigMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
        const saveButton = screen.getByText('Save');

        fireEvent.change(input, { target: { value: 'Same Name' } });
        fireEvent.click(saveButton);

        const stored = localStorage.getItem('filter_configurations');
        const configs = JSON.parse(stored!);
        expect(configs).toHaveLength(1);
        expect(configs[0].filters.search).toBe('New');
    });

    it('limits to MAX_CONFIGS (30) configurations', () => {
        const existingConfigs = Array.from({ length: 30 }, (_, i) => ({
            name: `Config ${i + 1}`,
            filters: mockFilters,
        }));
        localStorage.setItem('filter_configurations', JSON.stringify(existingConfigs));

        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
        const saveButton = screen.getByText('Save');

        fireEvent.change(input, { target: { value: 'Config 31' } });
        fireEvent.click(saveButton);

        const stored = localStorage.getItem('filter_configurations');
        const configs = JSON.parse(stored!);
        expect(configs).toHaveLength(30);
        expect(configs[0].name).toBe('Config 31'); // Most recent first
        expect(configs[configs.length - 1].name).toBe('Config 29'); // Config 30 was removed (oldest got bumped off)
    });

    it('closes suggestions when clicking outside', async () => {
        const config = { name: 'Test Config', filters: mockFilters };
        localStorage.setItem('filter_configurations', JSON.stringify([config]));

        render(<FilterConfigurations currentFilters={mockFilters} onLoadConfig={onLoadConfigMock} />);

        const input = screen.getByPlaceholderText(/Type to load or enter name to save/i);
        fireEvent.focus(input);

        expect(screen.getByText('Test Config')).toBeInTheDocument();

        // Click outside
        fireEvent.mouseDown(document.body);

        await waitFor(() => {
            expect(screen.queryByText('Test Config')).not.toBeInTheDocument();
        });
    });
});
