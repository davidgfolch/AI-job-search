import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

export const createTestQueryClient = (additionalOptions = {}) => {
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
    },
    ...additionalOptions
  });
};

export const createHookTestWrapper = (additionalOptions = {}) => {
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