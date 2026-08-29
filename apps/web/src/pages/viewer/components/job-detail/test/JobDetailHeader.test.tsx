import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import JobDetailHeader from '../JobDetailHeader';
import type { Job } from '../../../api/ViewerApi';
import { ShortcutsContext, defaultValue } from '../../../shortcutsContext';

describe('JobDetailHeader', () => {
  const mockJob: Job = {
    id: 1,
    title: 'Software Engineer',
    url: 'https://example.com/job',
  } as Job;

  const renderWithContext = (modifierPressed = false) =>
    render(
      <ShortcutsContext.Provider value={{ ...defaultValue(), modifierPressed }}>
        <JobDetailHeader job={mockJob} />
      </ShortcutsContext.Provider>
    );

  it('renders job title as link', () => {
    render(<JobDetailHeader job={mockJob} />);
    const link = screen.getByRole('link', { name: 'Software Engineer' });
    expect(link).toHaveAttribute('href', 'https://example.com/job');
  });

  it('includes the open URL shortcut in the link tooltip', () => {
    render(<JobDetailHeader job={mockJob} />);
    expect(screen.getByRole('link', { name: 'Software Engineer' })).toHaveAttribute('title', 'Open job URL — Alt+O');
  });

  it('shows open URL shortcut badge when modifier is held', () => {
    renderWithContext(true);
    expect(screen.getByText('Alt+O')).toBeInTheDocument();
  });

  it('does not show open URL shortcut badge by default', () => {
    renderWithContext(false);
    expect(screen.queryByText('Alt+O')).not.toBeInTheDocument();
  });

  it('shows detail focus shortcut badge when modifier is held', () => {
    renderWithContext(true);
    expect(screen.getByText('Alt+J')).toBeInTheDocument();
  });

  it('does not show detail focus shortcut badge by default', () => {
    renderWithContext(false);
    expect(screen.queryByText('Alt+J')).not.toBeInTheDocument();
  });

  it('does not render buttons when callbacks not provided', () => {
    render(<JobDetailHeader job={mockJob} />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});