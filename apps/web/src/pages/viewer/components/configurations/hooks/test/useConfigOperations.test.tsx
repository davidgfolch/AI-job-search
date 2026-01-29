import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useConfigOperations } from '../useConfigOperations';
import type { FilterConfig } from '../useFilterConfigurations';

describe('useConfigOperations', () => {
  const mockService = {
    save: vi.fn(),
    export: vi.fn(),
    load: vi.fn(),
  };

  const mockConfirmModal = {
    confirm: vi.fn(),
    isOpen: false,
    message: '',
    close: vi.fn(),
    handleConfirm: vi.fn(),
  };

  const defaultProps = {
    service: mockService,
    savedConfigs: [] as FilterConfig[],
    setSavedConfigs: vi.fn(),
    currentFilters: {},
    configName: 'test',
    setConfigName: vi.fn(),
    setIsOpen: vi.fn(),
    setSavedConfigName: vi.fn(),
    onLoadConfig: vi.fn(),
    notify: vi.fn(),
    confirmModal: mockConfirmModal,
  };

  it('should return operation functions', () => {
    const { result } = renderHook(() => useConfigOperations(defaultProps));
    expect(result.current).toHaveProperty('saveConfiguration');
    expect(result.current).toHaveProperty('loadConfiguration');
    expect(result.current).toHaveProperty('deleteConfiguration');
    expect(result.current).toHaveProperty('exportToDefaults');
  });
});
