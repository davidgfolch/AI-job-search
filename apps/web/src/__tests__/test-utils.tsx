import { render, type RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import type { Job, JobListParams } from '../api/jobs';
import { BOOLEAN_FILTERS } from '../config/filterConfig';

// ============================================================================
// Mock Data Factories
// ============================================================================

export function createMockJob(overrides?: Partial<Job>): Job {
    return {
        id: 1,
        title: 'Software Engineer',
        company: 'Tech Corp',
        salary: '100k',
        location: 'Remote',
        url: 'http://example.com',
        markdown: 'Job Description',
        web_page: 'LinkedIn',
        created: '2023-01-01',
        modified: null,
        flagged: false,
        like: false,
        ignored: false,
        seen: false,
        applied: false,
        discarded: false,
        closed: false,
        interview_rh: false,
        interview: false,
        interview_tech: false,
        interview_technical_test: false,
        interview_technical_test_done: false,
        ai_enriched: true,
        easy_apply: false,
        required_technologies: 'React',
        optional_technologies: 'Python',
        client: 'Client A',
        comments: 'Test comment',
        cv_match_percentage: 90,
        ...overrides,
    };
}

export function createMockJobs(count: number, baseOverrides?: Partial<Job>): Job[] {
    return Array.from({ length: count }, (_, index) =>
        createMockJob({
            id: index + 1,
            title: `Job ${index + 1}`,
            company: `Company ${index + 1}`,
            salary: `${100 + index * 20}k`,
            url: `http://example.com/${index + 1}`,
            markdown: `Description ${index + 1}`,
            ...baseOverrides,
        })
    );
}

export function createMockFilters(overrides?: Partial<JobListParams>): JobListParams {
    const params = overrides;
    if (overrides) {
        BOOLEAN_FILTERS
                    .filter(entry => !(entry.key in overrides))
                    .forEach(entry => (params as any)[entry.key] = null);
    }
    return {
        page: 1,
        size: 20,
        search: '',
        order: 'created desc',
        ...params,
    };
}

// ============================================================================
// Test Wrappers
// ============================================================================

export function createTestQueryClient(): QueryClient {
    return new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    });
}

interface RenderWithProvidersOptions extends Omit<RenderOptions, 'wrapper'> {
    queryClient?: QueryClient;
}

export function renderWithProviders(
    ui: React.ReactElement,
    { queryClient = createTestQueryClient(), ...renderOptions }: RenderWithProvidersOptions = {}
) {
    return render(
        <BrowserRouter>
            <QueryClientProvider client={queryClient}>
                {ui}
            </QueryClientProvider>
        </BrowserRouter>,
        renderOptions
    );
}

// ============================================================================
// Timer Utilities
// ============================================================================

export function setupFakeTimers() {
    vi.clearAllTimers();
    vi.useFakeTimers();
}

export function cleanupFakeTimers() {
    vi.restoreAllMocks();
    vi.useRealTimers();
}

// ============================================================================
// LocalStorage Utilities
// ============================================================================

export function setupLocalStorage() {
    localStorage.clear();
}

export function getStoredConfigs() {
    const stored = localStorage.getItem('filter_configurations');
    return stored ? JSON.parse(stored) : [];
}

// ============================================================================
// Mock Setup
// ============================================================================

export function setupJobsApiMock() {
    return {
        getJobs: vi.fn(),
        getJob: vi.fn(),
        updateJob: vi.fn(),
        getAppliedJobsByCompany: vi.fn(),
    };
}

// ============================================================================
// Common Mock Setup
// ============================================================================

export function setupWindowMocks() {
    vi.spyOn(window, 'alert').mockImplementation(() => { });
    vi.spyOn(window, 'confirm').mockImplementation(() => true);
}

export function setupIntersectionObserver() {
    globalThis.IntersectionObserver = vi.fn().mockImplementation(() => ({
        observe: vi.fn(),
        unobserve: vi.fn(),
        disconnect: vi.fn(),
    })) as any;
}
