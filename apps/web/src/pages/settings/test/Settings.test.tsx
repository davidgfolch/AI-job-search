import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Settings from '../Settings';
import { settingsApi } from '../api/SettingsApi';
import { groupSettingsByKey } from '../utils/SettingsUtils';
import { setupSettingsMocks } from './Settings.mocks';

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

describe('Settings', () => {
    beforeEach(() => {
        setupSettingsMocks();
    });

    const renderSettingsAndWait = async () => {
        render(<Settings />);
        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });
    };

    const expectMessage = async (msg: string) => {
        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent(msg);
        });
    };

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

        await expectMessage('Failed to load settings');
    });


    it('handles env setting update bulk', async () => {
        await renderSettingsAndWait();

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
        await renderSettingsAndWait();

        vi.mocked(settingsApi.updateEnvSettingsBulk).mockRejectedValue(new Error('Save Error'));

        const saveBtns = screen.getAllByText('Save', { selector: '.env-save-btn' });
        
        await userEvent.click(saveBtns[0]);

        await expectMessage('Failed to update');
    });

    it('allows editing an env setting', async () => {
        await renderSettingsAndWait();

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
        
        await renderSettingsAndWait();

        expect(screen.getByText('SINGLE_KEY')).toBeInTheDocument();
        const singleInput = screen.getByDisplayValue('singlesval');
        
        // Target single inline item (line 129)
        await userEvent.clear(singleInput);
        await userEvent.type(singleInput, 'newSingle');
        expect(singleInput).toHaveValue('newSingle');
    });


    it('saves env settings from footer button (line 161)', async () => {
        await renderSettingsAndWait();

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
