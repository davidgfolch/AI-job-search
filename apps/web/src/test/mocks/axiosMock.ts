import { vi } from 'vitest';

export const createAxiosInstanceMock = () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  patch: vi.fn(),
  interceptors: {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  },
});

export const createAxiosMock = () => {
  const axiosCreateConfig = { value: null };
  const axiosInstance = createAxiosInstanceMock();
  
  return {
    default: {
      create: vi.fn((config) => {
        axiosCreateConfig.value = config;
        return axiosInstance;
      }),
    },
    axiosInstance,
    axiosCreateConfig,
  };
};

export const mockAxios = createAxiosMock();

export const setupAxiosMock = () => {
  vi.mock('axios', () => mockAxios);
  return mockAxios;
};