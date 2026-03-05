import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchDdlSchema, getModalityValues } from '../DdlApi';
import type { DdlSchemaResponse } from '../DdlApi';

const mockAxios = vi.hoisted(() => ({
  get: vi.fn(),
}));

const mockApiClient = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock('axios', () => ({
  default: mockAxios,
}));

vi.mock('../ApiClient', () => ({
  default: mockApiClient,
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

  describe('getModalityValues', () => {
    it('fetches modality values successfully', async () => {
      const mockResult = ['REMOTE', 'HYBRID', 'ON_SITE'];
      mockApiClient.get.mockResolvedValue({ data: mockResult });
      const result = await getModalityValues();
      expect(mockApiClient.get).toHaveBeenCalledWith('/ddl/schema/enum-values/jobs/modality');
      expect(result).toEqual(mockResult);
    });

    it('propagates errors when API call fails', async () => {
      const error = new Error('API error');
      mockApiClient.get.mockRejectedValue(error);
      await expect(getModalityValues()).rejects.toThrow('API error');
    });
  });
});
