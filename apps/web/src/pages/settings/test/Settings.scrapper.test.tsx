import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Settings from '../Settings';
import { settingsApi } from '../api/SettingsApi';
import { mockScrapperState } from './Settings.fixtures';
import { setupSettingsMocks, resetTestQueryClient, renderWithClient } from './Settings.mocks';

vi.mock('prismjs/components/prism-json', () => ({}));
vi.mock('prismjs', () => ({
    default: {
        highlight: vi.fn((code) => code),
        languages: { json: {} },
    },
}));

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
        resetTestQueryClient();
    });

    const expectMessage = async (msg: string) => {
        await waitFor(() => {
            expect(screen.getByTestId('message-container')).toHaveTextContent(msg);
        });
    };

    it('handles scrapper state refresh', async () => {
        renderWithClient(<Settings />);

        await waitFor(() => {
            expect(screen.getByText('↻ Refresh')).toBeInTheDocument();
        });

        const refreshBtn = screen.getByText('↻ Refresh');
        await userEvent.click(refreshBtn);
        expect(settingsApi.getScrapperState).toHaveBeenCalledTimes(2);
        await expectMessage('Scrapper state refreshed');
    });

    it('handles scrapper state refresh error', async () => {
        vi.mocked(settingsApi.getScrapperState).mockImplementation(() => Promise.reject(new Error('Refresh Error')));

        renderWithClient(<Settings />);

        await waitFor(() => {
            expect(screen.getByText('↻ Refresh')).toBeInTheDocument();
        });

        const refreshBtn = screen.getByText('↻ Refresh');
        await userEvent.click(refreshBtn);
        await expectMessage('Failed to refresh scrapper state');
    });

    it('handles scrapper state save', async () => {
        renderWithClient(<Settings />);

        await waitFor(() => {
            expect(screen.getByText('Save', { selector: '.scrapper-save-btn' })).toBeInTheDocument();
        });

        const saveBtn = screen.getByText('Save', { selector: '.scrapper-save-btn' });
        await userEvent.click(saveBtn);
        expect(settingsApi.updateScrapperState).toHaveBeenCalledWith(mockScrapperState);
        await expectMessage('Scrapper state saved successfully');
    });

    it('handles scrapper state invalid JSON error', async () => {
        renderWithClient(<Settings />);

        await waitFor(() => {
            expect(screen.getByText('Save', { selector: '.scrapper-save-btn' })).toBeInTheDocument();
        });

        const textarea = document.querySelector('.scrapper-editor textarea') as HTMLTextAreaElement;
        await userEvent.clear(textarea);
        await userEvent.type(textarea, 'invalid json');
        const saveBtn = screen.getByText('Save', { selector: '.scrapper-save-btn' });
        await userEvent.click(saveBtn);
        await expectMessage('Invalid JSON format for scrapper state');
    });

    it('dismisses message container', async () => {
        renderWithClient(<Settings />);

        await waitFor(() => {
            expect(screen.getByText('Save', { selector: '.scrapper-save-btn' })).toBeInTheDocument();
        });

        const saveBtn = screen.getByText('Save', { selector: '.scrapper-save-btn' });
        await userEvent.click(saveBtn);
        await expectMessage('Scrapper state saved successfully');
        await userEvent.click(screen.getByTestId('message-container'));
        await waitFor(() => {
            expect(screen.queryByTestId('message-container')).not.toBeInTheDocument();
        });
    });
});
