import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useConfirmationModal } from '../useConfirmationModal';

describe('useConfirmationModal', () => {
  it('initializes with closed state', () => {
    const { result } = renderHook(() => useConfirmationModal());
    expect(result.current.isOpen).toBe(false);
    expect(result.current.message).toBe('');
  });

  it('opens modal with message when confirm is called', () => {
    const { result } = renderHook(() => useConfirmationModal());
    const onConfirm = vi.fn();
    act(() => {
      result.current.confirm('Are you sure?', onConfirm);
    });
    expect(result.current.isOpen).toBe(true);
    expect(result.current.message).toBe('Are you sure?');
  });

  it('closes modal when close is called', () => {
    const { result } = renderHook(() => useConfirmationModal());
    act(() => {
      result.current.confirm('Test message', vi.fn());
    });
    expect(result.current.isOpen).toBe(true);
    act(() => {
      result.current.close();
    });
    expect(result.current.isOpen).toBe(false);
  });

  it('calls onConfirm callback and closes modal when handleConfirm is called', () => {
    const { result } = renderHook(() => useConfirmationModal());
    const onConfirm = vi.fn();
    act(() => {
      result.current.confirm('Confirm action?', onConfirm);
    });
    act(() => {
      result.current.handleConfirm();
    });
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(result.current.isOpen).toBe(false);
  });

  it('maintains message after closing', () => {
    const { result } = renderHook(() => useConfirmationModal());
    act(() => {
      result.current.confirm('Message to keep', vi.fn());
    });
    const message = result.current.message;
    act(() => {
      result.current.close();
    });
    expect(result.current.message).toBe(message);
  });
});
