import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Settings from '../Settings';
import { settingsApi } from '../api/SettingsApi';
import { groupSettingsByKey, getSubgroupTitle } from '../utils/SettingsUtils';
import { setupSettingsMocks, resetTestQueryClient, renderWithClient } from './Settings.mocks';

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
        resetTestQueryClient();
    });

    const expectMessage = async (msg: string) => {
        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent(msg);
        });
    };

    it('renders loading state initially', async () => {
        renderWithClient(<Settings />);
        expect(screen.getByText('Loading settings...')).toBeInTheDocument();
        await waitFor(() => {
            expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
        });
    });

    it('loads and renders settings properly', async () => {
        renderWithClient(<Settings />);

        await waitFor(() => {
            expect(screen.getByTestId('page-header')).toHaveTextContent('Settings');
        });

        expect(settingsApi.getEnvSettings).toHaveBeenCalled();
        expect(settingsApi.getScrapperState).toHaveBeenCalled();

        expect(screen.getByText('Environment Variables (.env)')).toBeInTheDocument();
        expect(screen.getByText('scrapper_state.json')).toBeInTheDocument();
        expect(screen.getByText('System & Base')).toBeInTheDocument();
        expect(screen.getByText('AI Enrichment')).toBeInTheDocument();

        expect(screen.getByDisplayValue('value1')).toBeInTheDocument();
        expect(screen.getByDisplayValue('value2')).toBeInTheDocument();
        expect(screen.getByDisplayValue('value3')).toBeInTheDocument();
        expect(screen.getByDisplayValue('secret')).toHaveAttribute('type', 'password');
    });

    it('handles load errors gracefully', async () => {
        vi.mocked(settingsApi.getEnvSettings).mockRejectedValueOnce(new Error('Load Error'));
        
        renderWithClient(<Settings />);

        await expectMessage('Failed to load settings');
    });


    it('handles env setting update bulk', async () => {
        renderWithClient(<Settings />);

        await waitFor(() => {
            expect(screen.getByText('Environment Variables (.env)')).toBeInTheDocument();
        });

        const saveBtns = screen.getAllByText('Save', { selector: '.env-save-btn' });
        
        await userEvent.click(saveBtns[0]);

        expect(settingsApi.updateEnvSettingsBulk).toHaveBeenCalledTimes(1);
        
        await expectMessage('saved successfully');
    });

    it('handles env setting update bulk error', async () => {
        vi.mocked(settingsApi.updateEnvSettingsBulk).mockRejectedValue(new Error('Save Error'));

        renderWithClient(<Settings />);

        await waitFor(() => {
            expect(screen.getByText('Environment Variables (.env)')).toBeInTheDocument();
        });

        const saveBtns = screen.getAllByText('Save', { selector: '.env-save-btn' });
        
        await userEvent.click(saveBtns[0]);

        await expectMessage('Failed to update');
    });

    it('allows editing an env setting', async () => {
        renderWithClient(<Settings />);

        await waitFor(() => {
            const inputs = screen.getAllByRole('textbox');
            expect(inputs.length).toBeGreaterThan(0);
        });

        const inputs = screen.getAllByRole('textbox');
        const firstInput = inputs[0] as HTMLInputElement;

        await userEvent.clear(firstInput);
        await userEvent.type(firstInput, 'newValue');

        expect(firstInput.value).toBe('newValue');
    });
    
    it('groups 1 item by its key as subgroup and renders inline-item', async () => {
         vi.mocked(groupSettingsByKey).mockReturnValue({
            'Other': ['SINGLE_KEY']
        });
        vi.mocked(getSubgroupTitle).mockReturnValue('SINGLE_SUBGROUP');
         vi.mocked(settingsApi.getEnvSettings).mockResolvedValue({'SINGLE_KEY': 'singlesval'});
         
        renderWithClient(<Settings />);

        await waitFor(() => {
            expect(screen.getByText('SINGLE_KEY')).toBeInTheDocument();
        });

        const singleInput = screen.getByDisplayValue('singlesval');
        
        await userEvent.clear(singleInput);
        await userEvent.type(singleInput, 'newSingle');
        expect(singleInput).toHaveValue('newSingle');
    });


    it('saves env settings from footer button (line 161)', async () => {
        renderWithClient(<Settings />);

        await waitFor(() => {
            const saveBtns = screen.getAllByText('Save', { selector: '.env-save-btn' });
            expect(saveBtns.length).toBeGreaterThan(1);
        });

        const saveBtns = screen.getAllByText('Save', { selector: '.env-save-btn' });
        await userEvent.click(saveBtns[1]);

        expect(settingsApi.updateEnvSettingsBulk).toHaveBeenCalled();
        
        await expectMessage('saved successfully');
    });
});
