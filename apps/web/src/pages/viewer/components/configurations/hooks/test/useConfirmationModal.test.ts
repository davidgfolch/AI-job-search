import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useConfirmationModal } from '../useConfirmationModal';

describe('useConfirmationModal', () => {
    it('should initialize with default closed state', () => {
        const { result } = renderHook(() => useConfirmationModal());
        expect(result.current.isOpen).toBe(false);
        expect(result.current.message).toBe('');
    });

    it('should open modal with message and callback', () => {
        const { result } = renderHook(() => useConfirmationModal());
        const onConfirmMock = vi.fn();

        act(() => {
            result.current.confirm('Are you sure?', onConfirmMock);
        });

        expect(result.current.isOpen).toBe(true);
        expect(result.current.message).toBe('Are you sure?');

        act(() => {
            result.current.handleConfirm();
        });

        expect(onConfirmMock).toHaveBeenCalled();
        expect(result.current.isOpen).toBe(false);
    });

    it('should close without confirming', () => {
        const { result } = renderHook(() => useConfirmationModal());
        const onConfirmMock = vi.fn();

        act(() => {
            result.current.confirm('Are you sure?', onConfirmMock);
        });

        act(() => {
            result.current.close();
        });

        expect(result.current.isOpen).toBe(false);
        expect(onConfirmMock).not.toHaveBeenCalled();
    });
});
