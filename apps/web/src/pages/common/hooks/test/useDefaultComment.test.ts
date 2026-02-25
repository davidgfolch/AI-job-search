import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDefaultComment } from '../useDefaultComment';
import { settingsApi } from '../../../settings/api/SettingsApi';

// Mock settingsApi
vi.mock('../../../settings/api/SettingsApi', () => ({
    settingsApi: {
        getEnvSettings: vi.fn(),
        updateEnvSetting: vi.fn(),
    },
}));

describe('useDefaultComment', () => {
    let consoleSpy: any;
    
    beforeEach(() => {
        vi.clearAllMocks();
        consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
        consoleSpy?.mockRestore();
    });

    it('should load default comment from settingsApi on mount', async () => {
        const mockStoredComment = '- custom applied text';
        (settingsApi.getEnvSettings as any).mockResolvedValue({
            APPLY_MODAL_DEFAULT_TEXT: mockStoredComment
        });

        const { result } = renderHook(() => useDefaultComment());

        expect(result.current.isLoading).toBe(true);
        expect(result.current.comment).toBe('');

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(settingsApi.getEnvSettings).toHaveBeenCalled();
        expect(result.current.comment).toBe(mockStoredComment);
    });

    it('should save comment to settingsApi', async () => {
        (settingsApi.getEnvSettings as any).mockResolvedValue({
            APPLY_MODAL_DEFAULT_TEXT: ''
        });
        (settingsApi.updateEnvSetting as any).mockResolvedValue(undefined);

        const { result } = renderHook(() => useDefaultComment());

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        const newComment = '- new custom comment';
        await result.current.saveComment(newComment);

        expect(settingsApi.updateEnvSetting).toHaveBeenCalledWith('APPLY_MODAL_DEFAULT_TEXT', newComment);
        await waitFor(() => {
            expect(result.current.comment).toBe(newComment);
        });
    });

    it('should not save empty comment', async () => {
        (settingsApi.getEnvSettings as any).mockResolvedValue({
            APPLY_MODAL_DEFAULT_TEXT: ''
        });

        const { result } = renderHook(() => useDefaultComment());

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await waitFor(() => {
            result.current.saveComment('   ');
        });

        expect(settingsApi.updateEnvSetting).not.toHaveBeenCalled();
    });

});