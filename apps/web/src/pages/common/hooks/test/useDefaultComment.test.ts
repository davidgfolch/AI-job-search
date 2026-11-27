import { describe, it, expect, vi, beforeEach, afterEach, type MockInstance } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDefaultComment } from '../useDefaultComment';
import { settingsApi } from '../../../settings/api/SettingsApi';

vi.mock('../../../settings/api/SettingsApi', () => ({
    settingsApi: {
        getEnvSettings: vi.fn(),
        updateEnvSetting: vi.fn(),
    },
}));

vi.mock('../useEnvSettings', () => ({
    useEnvSettings: vi.fn(),
}));

import { useEnvSettings } from '../useEnvSettings';

describe('useDefaultComment', () => {
    let consoleSpy: MockInstance;
    
    beforeEach(() => {
        vi.clearAllMocks();
        consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
        consoleSpy?.mockRestore();
    });

    it('should load default comment from settingsApi on mount', async () => {
        const mockStoredComment = '- custom applied text';
        vi.mocked(useEnvSettings).mockReturnValue({
            data: { UI_APPLY_MODAL_DEFAULT_TEXT: mockStoredComment },
            isLoading: false,
        } as unknown as ReturnType<typeof useEnvSettings>);

        const { result } = renderHook(() => useDefaultComment());

        expect(result.current.isLoading).toBe(false);
        expect(result.current.comment).toBe(mockStoredComment);
    });

    it('should save comment to settingsApi', async () => {
        vi.mocked(useEnvSettings).mockReturnValue({
            data: { UI_APPLY_MODAL_DEFAULT_TEXT: '' },
            isLoading: false,
        } as unknown as ReturnType<typeof useEnvSettings>);
        vi.mocked(settingsApi.updateEnvSetting).mockResolvedValue(undefined as unknown as Record<string, string>);

        const { result } = renderHook(() => useDefaultComment());

        expect(result.current.isLoading).toBe(false);

        const newComment = '- new custom comment';
        await result.current.saveComment(newComment);

        expect(settingsApi.updateEnvSetting).toHaveBeenCalledWith('UI_APPLY_MODAL_DEFAULT_TEXT', newComment);
        await waitFor(() => {
            expect(result.current.comment).toBe(newComment);
        });
    });

    it('should not save empty comment', async () => {
        vi.mocked(useEnvSettings).mockReturnValue({
            data: { UI_APPLY_MODAL_DEFAULT_TEXT: '' },
            isLoading: false,
        } as unknown as ReturnType<typeof useEnvSettings>);

        const { result } = renderHook(() => useDefaultComment());

        expect(result.current.isLoading).toBe(false);

        await waitFor(() => {
            result.current.saveComment('   ');
        });

        expect(settingsApi.updateEnvSetting).not.toHaveBeenCalled();
    });

});