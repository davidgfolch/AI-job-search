import { vi } from 'vitest';
import { setupDOMMocks, cleanupDOMMocks } from '../mocks/domMocks';
import { setupAxiosMock } from '../mocks/axiosMock';
import { setupServiceMocks } from '../mocks/serviceMocks';

export const setupStandardTestEnvironment = () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    setupDOMMocks();
  });
  
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    cleanupDOMMocks();
  });
};

export const setupApiTestEnvironment = () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupAxiosMock();
  });
  
  afterEach(() => {
    vi.restoreAllMocks();
  });
};

export const setupComponentTestEnvironment = () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    setupDOMMocks();
  });
  
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    cleanupDOMMocks();
  });
};

export const setupHookTestEnvironment = () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });
  
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });
};