import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ConfigurationDropdown } from '../ConfigurationDropdown';

describe('ConfigurationDropdown', () => {
    const defaultProps = {
        isOpen: true,
        filteredConfigs: [{ name: 'Test Config', filters: {} as any }],
        highlightIndex: -1,
        onLoad: vi.fn(),
        onDelete: vi.fn(),
        setHighlightIndex: vi.fn(),
        onTogglewatched: vi.fn(),
        onToggleStats: vi.fn(),
    };

    it('renders nothing when closed', () => {
        const { container } = render(<ConfigurationDropdown {...defaultProps} isOpen={false} />);
        expect(container).toBeEmptyDOMElement();
    });

    it('renders configs when open', () => {
        render(<ConfigurationDropdown {...defaultProps} />);
        expect(screen.getByText('Test Config')).toBeInTheDocument();
        expect(screen.getByText('📈')).toBeInTheDocument();
        expect(screen.getByText('🔕')).toBeInTheDocument();
    });
});
