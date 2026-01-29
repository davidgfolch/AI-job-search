import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SalaryActions from '../SalaryActions';

describe('SalaryActions', () => {
  it('renders freelance calculator button', () => {
    render(<SalaryActions onToggleCalculator={vi.fn()} />);
    expect(screen.getByRole('button', { name: /Freelance/ })).toBeInTheDocument();
  });

  it('renders gross year calculator button', () => {
    render(<SalaryActions onToggleCalculator={vi.fn()} />);
    expect(screen.getByRole('button', { name: /Gross year/ })).toBeInTheDocument();
  });

  it('calls onToggleCalculator when freelance button clicked', async () => {
    const user = userEvent.setup();
    const onToggle = vi.fn();
    render(<SalaryActions onToggleCalculator={onToggle} />);
    await user.click(screen.getByRole('button', { name: /Freelance/ }));
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it('opens external link when gross year button clicked', async () => {
    const user = userEvent.setup();
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    render(<SalaryActions onToggleCalculator={vi.fn()} />);
    await user.click(screen.getByRole('button', { name: /Gross year/ }));
    expect(openSpy).toHaveBeenCalledWith(
      'https://tecalculo.com/calculadora-de-sueldo-neto',
      '_blank'
    );
    openSpy.mockRestore();
  });

  it('renders delete button when onUpdate provided', () => {
    const onUpdate = vi.fn();
    render(<SalaryActions onToggleCalculator={vi.fn()} onUpdate={onUpdate} />);
    expect(screen.getByRole('button', { name: '🗑️' })).toBeInTheDocument();
  });

  it('calls onUpdate with null salary when delete button clicked', async () => {
    const user = userEvent.setup();
    const onUpdate = vi.fn();
    render(<SalaryActions onToggleCalculator={vi.fn()} onUpdate={onUpdate} />);
    await user.click(screen.getByRole('button', { name: '🗑️' }));
    expect(onUpdate).toHaveBeenCalledWith({ salary: null });
  });

  it('does not render delete button when onUpdate not provided', () => {
    render(<SalaryActions onToggleCalculator={vi.fn()} />);
    expect(screen.queryByRole('button', { name: '🗑️' })).not.toBeInTheDocument();
  });
});
