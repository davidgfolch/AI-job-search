import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import JobDetailHeader from '../JobDetailHeader';
import type { Job } from '../../../api/ViewerApi';

describe('JobDetailHeader', () => {
  const mockJob: Job = {
    id: 1,
    title: 'Software Engineer',
    url: 'https://example.com/job',
  } as Job;

  it('renders job title as link', () => {
    render(<JobDetailHeader job={mockJob} />);
    const link = screen.getByRole('link', { name: 'Software Engineer' });
    expect(link).toHaveAttribute('href', 'https://example.com/job');
  });





  it('does not render buttons when callbacks not provided', () => {
    render(<JobDetailHeader job={mockJob} />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
