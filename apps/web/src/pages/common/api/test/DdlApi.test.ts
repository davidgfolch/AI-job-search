import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchDdlSchema } from '../DdlApi';
import type { DdlSchemaResponse } from '../DdlApi';

const mockAxios = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock('axios', () => ({
  default: mockAxios,
}));

describe('DdlApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetchDdlSchema', () => {
    it('fetches DDL schema successfully', async () => {
      const mockSchema: DdlSchemaResponse = {
        tables: {
          jobs: ['id', 'title', 'company'],
          skills: ['id', 'name'],
        },
        keywords: ['SELECT', 'FROM', 'WHERE'],
      };
      mockAxios.get.mockResolvedValue({ data: mockSchema });
      const result = await fetchDdlSchema();
      expect(mockAxios.get).toHaveBeenCalledWith('http://localhost:8000/api/ddl/schema');
      expect(result).toEqual(mockSchema);
    });

    it('propagates errors when API call fails', async () => {
      const error = new Error('Network error');
      mockAxios.get.mockRejectedValue(error);
      await expect(fetchDdlSchema()).rejects.toThrow('Network error');
    });
  });
});
