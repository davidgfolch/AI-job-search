import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDefaultComment } from '../useDefaultComment';
import { persistenceApi } from '../../api/CommonPersistenceApi';

// Mock the persistenceApi
vi.mock('../../api/CommonPersistenceApi', () => ({
    persistenceApi: {
        getValue: vi.fn(),
        setValue: vi.fn(),
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

    it('should load default comment from localStorage on mount', async () => {
        const mockStoredComment = '- custom applied text';
        (persistenceApi.getValue as any).mockResolvedValue(mockStoredComment);

        const { result } = renderHook(() => useDefaultComment());

        expect(result.current.isLoading).toBe(true);
        expect(result.current.comment).toBe('');

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(persistenceApi.getValue).toHaveBeenCalledWith('default_comment_text');
        expect(result.current.comment).toBe(mockStoredComment);
    });

    it('should save comment to localStorage', async () => {
        (persistenceApi.getValue as any).mockResolvedValue('- applied by 45k');
        (persistenceApi.setValue as any).mockResolvedValue(undefined);

        const { result } = renderHook(() => useDefaultComment());

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        const newComment = '- new custom comment';
        await waitFor(() => {
            result.current.saveComment(newComment);
        });

        expect(persistenceApi.setValue).toHaveBeenCalledWith('default_comment_text', newComment);
        expect(result.current.comment).toBe(newComment);
    });

    it('should not save empty comment', async () => {
        (persistenceApi.getValue as any).mockResolvedValue('- applied by 45k');

        const { result } = renderHook(() => useDefaultComment());

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await waitFor(() => {
            result.current.saveComment('   ');
        });

        expect(persistenceApi.setValue).not.toHaveBeenCalled();
    });

});