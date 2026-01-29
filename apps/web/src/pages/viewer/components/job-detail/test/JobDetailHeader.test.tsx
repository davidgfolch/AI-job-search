import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import JobDetailHeader from '../JobDetailHeader';
import type { Job } from '../../../api/jobs';

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

  it('renders create button when onCreateNew provided', () => {
    const onCreateNew = vi.fn();
    render(<JobDetailHeader job={mockJob} onCreateNew={onCreateNew} />);
    expect(screen.getByRole('button', { name: /Create/ })).toBeInTheDocument();
  });

  it('renders delete button when onDelete provided', () => {
    const onDelete = vi.fn();
    render(<JobDetailHeader job={mockJob} onDelete={onDelete} />);
    expect(screen.getByRole('button', { name: /Delete/ })).toBeInTheDocument();
  });

  it('calls onCreateNew when create button clicked', async () => {
    const user = userEvent.setup();
    const onCreateNew = vi.fn();
    render(<JobDetailHeader job={mockJob} onCreateNew={onCreateNew} />);
    await user.click(screen.getByRole('button', { name: /Create/ }));
    expect(onCreateNew).toHaveBeenCalledTimes(1);
  });

  it('calls onDelete when delete button clicked', async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    render(<JobDetailHeader job={mockJob} onDelete={onDelete} />);
    await user.click(screen.getByRole('button', { name: /Delete/ }));
    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  it('does not render buttons when callbacks not provided', () => {
    render(<JobDetailHeader job={mockJob} />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
