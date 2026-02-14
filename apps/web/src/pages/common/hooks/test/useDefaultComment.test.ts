import { renderHook, act } from '@testing-library/react';
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

        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 0));
        });

        expect(persistenceApi.getValue).toHaveBeenCalledWith('default_comment_text');
        expect(result.current.isLoading).toBe(false);
        expect(result.current.comment).toBe(mockStoredComment);
    });

    it('should use hardcoded default when localStorage is empty', async () => {
        (persistenceApi.getValue as any).mockResolvedValue(null);

        const { result } = renderHook(() => useDefaultComment());

        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 0));
        });

        expect(result.current.comment).toBe('- applied by 45k');
    });

    it('should use hardcoded default when localStorage throws error', async () => {
        (persistenceApi.getValue as any).mockRejectedValue(new Error('Storage error'));

        const { result } = renderHook(() => useDefaultComment());

        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 0));
        });

        expect(result.current.comment).toBe('- applied by 45k');
        expect(result.current.isLoading).toBe(false);
    });

    it('should save comment to localStorage', async () => {
        (persistenceApi.getValue as any).mockResolvedValue('- applied by 45k');
        (persistenceApi.setValue as any).mockResolvedValue(undefined);

        const { result } = renderHook(() => useDefaultComment());

        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 0));
        });

        const newComment = '- new custom comment';
        await act(async () => {
            await result.current.saveComment(newComment);
        });

        expect(persistenceApi.setValue).toHaveBeenCalledWith('default_comment_text', newComment);
        expect(result.current.comment).toBe(newComment);
    });

    it('should not save empty comment', async () => {
        (persistenceApi.getValue as any).mockResolvedValue('- applied by 45k');

        const { result } = renderHook(() => useDefaultComment());

        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 0));
        });

        await act(async () => {
            await result.current.saveComment('   ');
        });

        expect(persistenceApi.setValue).not.toHaveBeenCalled();
    });

    it('should handle save error gracefully', async () => {
        (persistenceApi.getValue as any).mockResolvedValue('- original comment');
        (persistenceApi.setValue as any).mockRejectedValue(new Error('Save failed'));

        const { result } = renderHook(() => useDefaultComment());

        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 0));
        });

        const originalComment = result.current.comment;
        
        await act(async () => {
            await result.current.saveComment('- new comment');
        });

        // Comment should revert to original on error
        expect(result.current.comment).toBe(originalComment);
    });
});