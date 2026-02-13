import { vi } from 'vitest';

export const createRouterMocks = () => ({
  useSearchParams: vi.fn(),
  useParams: vi.fn(),
  useNavigate: vi.fn(),
  useLocation: vi.fn(),
});

export const setupRouterMocks = (overrides = {}) => {
  const mocks = {
    useSearchParams: vi.fn(() => [new URLSearchParams()]),
    useParams: vi.fn(() => ({})),
    useNavigate: vi.fn(() => vi.fn()),
    useLocation: vi.fn(() => ({ pathname: '/', search: '', hash: '', state: null, key: 'test' })),
    ...overrides,
  };
  
  vi.mock('react-router-dom', () => ({
    useSearchParams: mocks.useSearchParams,
    useParams: mocks.useParams,
    useNavigate: mocks.useNavigate,
    useLocation: mocks.useLocation,
  }));
  
  return mocks;
};