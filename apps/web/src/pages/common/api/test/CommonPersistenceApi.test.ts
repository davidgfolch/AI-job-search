import { describe, it, expect, beforeEach, vi } from 'vitest';
import { persistenceApi } from '../CommonPersistenceApi';
import { defaultFilterConfigurations } from '../defaults';

describe('persistenceApi', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('getValue', () => {
    it('returns value from localStorage when available', async () => {
      const testData = { test: 'data' };
      localStorage.setItem('test_key', JSON.stringify(testData));
      const result = await persistenceApi.getValue('test_key');
      expect(result).toEqual(testData);
    });

    it('returns default filter configurations when key matches and localStorage is empty', async () => {
      const result = await persistenceApi.getValue('filter_configurations');
      expect(result).toEqual(defaultFilterConfigurations);
    });

    it('returns null when key not found in localStorage or defaults', async () => {
      const result = await persistenceApi.getValue('non_existent_key');
      expect(result).toBeNull();
    });

    it('returns null and logs error when JSON parsing fails', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      localStorage.setItem('invalid_json', 'invalid{json}');
      const result = await persistenceApi.getValue('invalid_json');
      expect(result).toBeNull();
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to load persistence data for key:',
        'invalid_json',
        expect.any(Error)
      );
      consoleSpy.mockRestore();
    });
  });

  describe('setValue', () => {
    it('saves value to localStorage', async () => {
      const testData = { key: 'value' };
      await persistenceApi.setValue('test_key', testData);
      const stored = localStorage.getItem('test_key');
      expect(stored).toBe(JSON.stringify(testData));
    });

    it('handles errors when localStorage is unavailable', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      // Save original implementation
      const originalSetItem = localStorage.setItem;
      
      // Mock setItem to throw
      const setItemMock = vi.fn(() => {
        throw new Error('Storage full');
      });
      localStorage.setItem = setItemMock;

      try {
        await persistenceApi.setValue('test_key', { data: 'test' });
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to save persistence data for key:',
          'test_key',
          expect.any(Error)
        );
      } finally {
        // Restore original implementation
        localStorage.setItem = originalSetItem;
        consoleSpy.mockRestore();
      }
    });
  });
});
