import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

type TestQueryClientOptions = {
  queries?: Record<string, unknown>;
  mutations?: Record<string, unknown>;
};

export const createTestQueryClient = (additionalOptions: TestQueryClientOptions = {}) => {
  return new QueryClient({
    defaultOptions: { 
      queries: { 
        retry: false,
        gcTime: 0,
        ...additionalOptions.queries 
      },
      mutations: {
        retry: false,
        ...additionalOptions.mutations
      }
    }
  });
};

export const createHookTestWrapper = (additionalOptions: TestQueryClientOptions = {}) => {
  const queryClient = createTestQueryClient(additionalOptions);
  
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
};

export const wrapper = createHookTestWrapper();