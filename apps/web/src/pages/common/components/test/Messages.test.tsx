import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Messages from '../Messages';

describe('Messages', () => {
  const testCases = [
    { type: 'success' as const, message: 'Operation successful' },
    { type: 'error' as const, message: 'Operation failed' },
  ];

  it.each(testCases)('renders $type message with correct text', ({ type, message }) => {
    const onDismiss = vi.fn();
    render(<Messages message={message} type={type} onDismiss={onDismiss} />);
    expect(screen.getByText(message)).toBeInTheDocument();
  });

  it.each(testCases)('applies correct CSS class for $type', ({ type, message }) => {
    const onDismiss = vi.fn();
    const { container } = render(<Messages message={message} type={type} onDismiss={onDismiss} />);
    const messageElement = container.querySelector('.message');
    expect(messageElement).toHaveClass('message', type);
  });

  it('calls onDismiss when clicked', async () => {
    const user = userEvent.setup();
    const onDismiss = vi.fn();
    render(<Messages message="Test message" type="success" onDismiss={onDismiss} />);
    await user.click(screen.getByText('Test message'));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });
});
