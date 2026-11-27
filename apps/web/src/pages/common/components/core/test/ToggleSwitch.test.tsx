import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ToggleSwitch from '../ToggleSwitch';

describe('ToggleSwitch', () => {
    it('renders the checked state', () => {
        render(<ToggleSwitch checked={true} onChange={vi.fn()} label="Enabled" labelText="On" />);
        const toggle = screen.getByRole('switch');
        expect(toggle).toHaveAttribute('aria-checked', 'true');
        expect(toggle).toHaveAttribute('title', 'Enabled');
        expect(screen.getByText('On')).toBeInTheDocument();
    });

    it('renders the unchecked state', () => {
        render(<ToggleSwitch checked={false} onChange={vi.fn()} label="Disabled" labelText="Off" />);
        expect(screen.getByRole('switch')).toHaveAttribute('aria-checked', 'false');
        expect(screen.getByText('Off')).toBeInTheDocument();
    });

    it('calls onChange when clicked', () => {
        const onChange = vi.fn();
        render(<ToggleSwitch checked={true} onChange={onChange} label="Enabled" />);
        fireEvent.click(screen.getByRole('switch'));
        expect(onChange).toHaveBeenCalledOnce();
    });

    it('renders a sliding knob inside the track', () => {
        const { container } = render(<ToggleSwitch checked={false} onChange={vi.fn()} label="Disabled" />);
        expect(container.querySelector('.toggle-switch-track .toggle-switch-knob')).toBeInTheDocument();
    });
});
