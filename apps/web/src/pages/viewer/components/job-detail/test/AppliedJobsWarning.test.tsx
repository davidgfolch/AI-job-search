import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import AppliedJobsWarning from '../AppliedJobsWarning';
import type { AppliedCompanyJob } from '../../../api/jobs';

describe('AppliedJobsWarning', () => {
  it('renders nothing when loading', () => {
    const { container } = render(
      <AppliedJobsWarning appliedJobs={[]} loadingApplied={true} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when no applied jobs', () => {
    const { container } = render(
      <AppliedJobsWarning appliedJobs={[]} loadingApplied={false} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders warning with job count', () => {
    const appliedJobs: AppliedCompanyJob[] = [
      { id: 1, created: '2024-01-01' },
      { id: 2, created: '2024-01-02' },
    ];
    render(<AppliedJobsWarning appliedJobs={appliedJobs} loadingApplied={false} />);
    expect(screen.getByText(/already applied to 2/)).toBeInTheDocument();
  });

  it('renders link with correct job IDs', () => {
    const appliedJobs: AppliedCompanyJob[] = [
      { id: 1, created: '2024-01-01' },
      { id: 2, created: '2024-01-02' },
    ];
    render(<AppliedJobsWarning appliedJobs={appliedJobs} loadingApplied={false} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/?ids=1,2');
  });

  it('formats dates correctly', () => {
    const appliedJobs: AppliedCompanyJob[] = [
      { id: 1, created: '2024-01-15' },
    ];
    render(<AppliedJobsWarning appliedJobs={appliedJobs} loadingApplied={false} />);
    expect(screen.getByText(/15-01-24/)).toBeInTheDocument();
  });
});
