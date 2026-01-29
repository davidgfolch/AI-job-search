import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import JobList from '../JobList';
import type { Job } from '../../api/jobs';

vi.mock('../JobTable', () => ({
  default: vi.fn(() => <div data-testid="job-table">JobTable</div>),
}));

describe('JobList', () => {
  const mockProps = {
    isLoading: false,
    error: null,
    jobs: [],
    selectedJob: null,
    onJobSelect: vi.fn(),
    onLoadMore: vi.fn(),
    hasMore: false,
    selectedIds: new Set<number>(),
    selectionMode: 'none' as const,
    onToggleSelectJob: vi.fn(),
    onToggleSelectAll: vi.fn(),
  };

  it('renders loading state', () => {
    render(<JobList {...mockProps} isLoading={true} />);
    expect(screen.getByText('Loading jobs...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    render(<JobList {...mockProps} error={new Error('Test error')} />);
    expect(screen.getByText(/Unable to load jobs/)).toBeInTheDocument();
  });

  it('renders JobTable when data is loaded', () => {
    const jobs: Job[] = [{ id: 1, title: 'Test Job' } as Job];
    render(<JobList {...mockProps} jobs={jobs} />);
    expect(screen.getByTestId('job-table')).toBeInTheDocument();
  });

  it('renders JobTable with empty jobs array', () => {
    render(<JobList {...mockProps} />);
    expect(screen.getByTestId('job-table')).toBeInTheDocument();
  });
});
