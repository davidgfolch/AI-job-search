import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ConfigurationInput } from '../ConfigurationInput';

describe('ConfigurationInput', () => {
    const defaultProps = {
        configName: '',
        onChange: vi.fn(),
        onKeyDown: vi.fn(),
        onFocus: vi.fn(),
        onClick: vi.fn(),
        onBlur: vi.fn(),
        onSave: vi.fn(),
        onExport: vi.fn(),
    };

    it('renders input and buttons', () => {
        render(<ConfigurationInput {...defaultProps} />);
        expect(screen.getByPlaceholderText(/Type to load/i)).toBeInTheDocument();
        expect(screen.getByText('Save')).toBeInTheDocument();
        expect(screen.getByText('Export')).toBeInTheDocument();
    });
});
