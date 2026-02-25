import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Settings from '../Settings';
import { settingsApi } from '../api/SettingsApi';
import { mockScrapperState } from './Settings.fixtures';
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

describe('Settings Scrapper State', () => {
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

    it('handles scrapper state refresh', async () => {
        await renderSettingsAndWait();
        const refreshBtn = screen.getByText('↻ Refresh');
        await userEvent.click(refreshBtn);
        expect(settingsApi.getScrapperState).toHaveBeenCalledTimes(2);
        await expectMessage('Scrapper state refreshed');
    });

    it('handles scrapper state refresh error', async () => {
        await renderSettingsAndWait();
        vi.mocked(settingsApi.getScrapperState).mockRejectedValueOnce(new Error('Refresh Error'));
        const refreshBtn = screen.getByText('↻ Refresh');
        await userEvent.click(refreshBtn);
        await expectMessage('Failed to refresh scrapper state');
    });

    it('handles scrapper state save', async () => {
        await renderSettingsAndWait();
        const saveBtn = screen.getByText('Save', { selector: '.scrapper-save-btn' });
        await userEvent.click(saveBtn);
        expect(settingsApi.updateScrapperState).toHaveBeenCalledWith(mockScrapperState);
        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent('Scrapper state saved successfully');
        });
    });

    it('handles scrapper state invalid JSON error', async () => {
        await renderSettingsAndWait();
        const textarea = document.querySelector('.scrapper-editor textarea') as HTMLTextAreaElement;
        await userEvent.clear(textarea);
        await userEvent.type(textarea, 'invalid json');
        const saveBtn = screen.getByText('Save', { selector: '.scrapper-save-btn' });
        await act(async () => {
            await userEvent.click(saveBtn);
        });
        await expectMessage('Invalid JSON format for scrapper state');
    });

    it('dismisses message container', async () => {
        await renderSettingsAndWait();
        const saveBtn = screen.getByText('Save', { selector: '.scrapper-save-btn' });
        await userEvent.click(saveBtn);
        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent('Scrapper state saved successfully');
        });
        await userEvent.click(screen.getByTestId('message-container'));
        await waitFor(() => {
            expect(screen.queryByTestId('message-container')).not.toBeInTheDocument();
        });
    });
});
