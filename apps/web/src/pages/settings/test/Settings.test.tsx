import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Settings from '../Settings';
import { settingsApi } from '../api/SettingsApi';
import { groupSettingsByKey, getSubgroupTitle } from '../utils/SettingsUtils';

vi.mock('../api/SettingsApi');
vi.mock('../utils/SettingsUtils');
vi.mock('../../common/components/PageHeader', () => ({
    default: ({ title }: { title: string }) => <div data-testid="page-header">{title}</div>
}));
vi.mock('../../common/components/core/MessageContainer', () => ({
    default: ({ message, onDismissMessage }: any) => {
        if (!message) return null;
        return (
            <div data-testid="message-container" onClick={onDismissMessage}>
                {message.text}
            </div>
        );
    }
}));

const mockEnvSettings = {
    'PREFIX_KEY1': 'value1',
    'PREFIX_KEY2': 'value2',
    'OTHER_KEY': 'value3',
    'PASSWORD_KEY': 'secret'
};

const mockGroupedSettings = {
    'PREFIX': ['PREFIX_KEY1', 'PREFIX_KEY2'],
    'OTHER': ['OTHER_KEY', 'PASSWORD_KEY']
};

const mockScrapperState = { lastExecution: 'now' };

describe('Settings', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(groupSettingsByKey).mockReturnValue(mockGroupedSettings);
        vi.mocked(getSubgroupTitle).mockImplementation((key) => {
            if (key.startsWith('PREFIX_')) return 'PREFIX_SUBGROUP';
            return key;
        });
        vi.mocked(settingsApi.getEnvSettings).mockResolvedValue(mockEnvSettings);
        vi.mocked(settingsApi.getScrapperState).mockResolvedValue(mockScrapperState);
        vi.mocked(settingsApi.updateEnvSettingsBulk).mockImplementation(async (settings) => settings);
        vi.mocked(settingsApi.updateScrapperState).mockImplementation(async (state) => state);
    });

    it('renders loading state initially', async () => {
        render(<Settings />);
        expect(screen.getByText('Loading settings...')).toBeInTheDocument();
        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });
    });

    it('loads and renders settings properly', async () => {
        render(<Settings />);

        await waitFor(() => {
            expect(screen.getByTestId('page-header')).toHaveTextContent('Settings');
        });

        expect(settingsApi.getEnvSettings).toHaveBeenCalled();
        expect(settingsApi.getScrapperState).toHaveBeenCalled();

        expect(screen.getByText('Environment Variables (.env)')).toBeInTheDocument();
        expect(screen.getByText('Scrapper State (scrapper_state.json)')).toBeInTheDocument();
        expect(screen.getByText('PREFIX')).toBeInTheDocument();
        expect(screen.getByText('OTHER')).toBeInTheDocument();

        // Values are rendered
        expect(screen.getByDisplayValue('value1')).toBeInTheDocument();
        expect(screen.getByDisplayValue('value2')).toBeInTheDocument();
        expect(screen.getByDisplayValue('value3')).toBeInTheDocument();
        expect(screen.getByDisplayValue('secret')).toHaveAttribute('type', 'password');
    });

    it('handles load errors gracefully', async () => {
        vi.mocked(settingsApi.getEnvSettings).mockRejectedValueOnce(new Error('Load Error'));
        
        render(<Settings />);

        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent('Failed to load settings');
        });
    });

    it('handles scrapper state refresh', async () => {
        render(<Settings />);

        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });

        const refreshBtn = screen.getByText('↻ Refresh');
        await userEvent.click(refreshBtn);

        expect(settingsApi.getScrapperState).toHaveBeenCalledTimes(2); // Initial loader + refresh
        
        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent('Scrapper state refreshed');
        });
    });

    it('handles scrapper state refresh error', async () => {
        render(<Settings />);

        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });

        vi.mocked(settingsApi.getScrapperState).mockRejectedValueOnce(new Error('Refresh Error'));

        const refreshBtn = screen.getByText('↻ Refresh');
        await userEvent.click(refreshBtn);

        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent('Failed to refresh scrapper state');
        });
    });

    it('handles scrapper state save', async () => {
        render(<Settings />);

        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });

        const saveBtn = screen.getByText('Save', { selector: '.scrapper-save-btn' });
        await userEvent.click(saveBtn);

        expect(settingsApi.updateScrapperState).toHaveBeenCalledWith(mockScrapperState);

        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent('Scrapper state saved successfully');
        });
    });

    it('handles scrapper state invalid JSON error', async () => {
        render(<Settings />);

        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });

        const textarea = document.querySelector('.scrapper-textarea') as HTMLTextAreaElement;
        
        await userEvent.clear(textarea);
        await userEvent.type(textarea, 'invalid json');

        const saveBtn = screen.getByText('Save', { selector: '.scrapper-save-btn' });
        await act(async () => {
            await userEvent.click(saveBtn);
        });

        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent('Invalid JSON format for scrapper state');
        });
    });

    it('handles env setting update bulk', async () => {
        render(<Settings />);

        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });

        // the component binds handleEnvUpdateBulk to the Save buttons in env header and footer
        const saveBtns = screen.getAllByText('Save', { selector: '.env-save-btn' });
        
        await userEvent.click(saveBtns[0]);

        // called twice because groupedSettings has 2 groups
        expect(settingsApi.updateEnvSettingsBulk).toHaveBeenCalledTimes(2);
        
        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent('saved successfully');
        });
    });

    it('handles env setting update bulk error', async () => {
        render(<Settings />);

        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });

        vi.mocked(settingsApi.updateEnvSettingsBulk).mockRejectedValue(new Error('Save Error'));

        const saveBtns = screen.getAllByText('Save', { selector: '.env-save-btn' });
        
        await userEvent.click(saveBtns[0]);

        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent('Failed to update');
        });
    });

    it('allows editing an env setting', async () => {
        render(<Settings />);

        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });

        const inputs = screen.getAllByRole('textbox');
        const firstInput = inputs[0] as HTMLInputElement;

        await userEvent.clear(firstInput);
        await userEvent.type(firstInput, 'newValue');

        expect(firstInput.value).toBe('newValue');
    });
    
    it('groups 1 item by its key as subgroup and renders inline-item', async () => {
         vi.mocked(groupSettingsByKey).mockReturnValue({
            'SINGLE': ['SINGLE_KEY']
        });
        vi.mocked(settingsApi.getEnvSettings).mockResolvedValue({'SINGLE_KEY': 'singlesval'});
        
        render(<Settings />);

        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });

        expect(screen.getByText('SINGLE_KEY')).toBeInTheDocument();
        const singleInput = screen.getByDisplayValue('singlesval');
        
        // Target single inline item (line 129)
        await userEvent.clear(singleInput);
        await userEvent.type(singleInput, 'newSingle');
        expect(singleInput).toHaveValue('newSingle');
    });

    it('dismisses message container (line 90)', async () => {
        render(<Settings />);

        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });

        // Trigger a success message
        const saveBtn = screen.getByText('Save', { selector: '.scrapper-save-btn' });
        await userEvent.click(saveBtn);

        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent('Scrapper state saved successfully');
        });

        // Click the message container to dismiss it
        await userEvent.click(screen.getByTestId('message-container'));
        
        // Wait for it to disappear
        await waitFor(() => {
            expect(screen.queryByTestId('message-container')).not.toBeInTheDocument();
        });
    });

    it('saves env settings from footer button (line 161)', async () => {
        render(<Settings />);

        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });

        // The second save button is usually the footer one in the env settings container
        const saveBtns = screen.getAllByText('Save', { selector: '.env-save-btn' });
        expect(saveBtns.length).toBeGreaterThan(1);
        
        await userEvent.click(saveBtns[1]);

        expect(settingsApi.updateEnvSettingsBulk).toHaveBeenCalled();
        
        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent('saved successfully');
        });
    });
});
