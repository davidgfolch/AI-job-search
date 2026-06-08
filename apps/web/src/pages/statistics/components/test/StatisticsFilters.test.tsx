import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import StatisticsFilters from '../StatisticsFilters';
import '@testing-library/jest-dom';

const defaultProps = {
    timeRange: 'Last 3 months',
    onTimeRangeChange: vi.fn(),
    includeOldJobs: true,
    onIncludeOldJobsChange: vi.fn(),
};

describe('StatisticsFilters', () => {
    it('renders date range select with current value', () => {
        render(<StatisticsFilters {...defaultProps} />);
        expect(screen.getByRole('combobox')).toHaveValue('Last 3 months');
    });

    it('renders all time range options', () => {
        render(<StatisticsFilters {...defaultProps} />);
        expect(screen.getByText('All')).toBeInTheDocument();
        expect(screen.getByText('Last year')).toBeInTheDocument();
        expect(screen.getByText('Last 6 months')).toBeInTheDocument();
        expect(screen.getByText('Last 3 months')).toBeInTheDocument();
        expect(screen.getByText('Last month')).toBeInTheDocument();
        expect(screen.getByText('Last week')).toBeInTheDocument();
        expect(screen.getByText('Last day')).toBeInTheDocument();
    });

    it('renders include old jobs checkbox', () => {
        render(<StatisticsFilters {...defaultProps} />);
        expect(screen.getByText('Include old jobs')).toBeInTheDocument();
        expect(screen.getByRole('checkbox')).toBeChecked();
    });

    it('calls onTimeRangeChange when select changes', () => {
        const onTimeRangeChange = vi.fn();
        render(<StatisticsFilters {...defaultProps} onTimeRangeChange={onTimeRangeChange} />);
        fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Last week' } });
        expect(onTimeRangeChange).toHaveBeenCalledWith('Last week');
    });

    it('calls onIncludeOldJobsChange when checkbox toggled', () => {
        const onIncludeOldJobsChange = vi.fn();
        render(<StatisticsFilters {...defaultProps} onIncludeOldJobsChange={onIncludeOldJobsChange} />);
        fireEvent.click(screen.getByRole('checkbox'));
        expect(onIncludeOldJobsChange).toHaveBeenCalledWith(false);
    });

    it('applies className and style props', () => {
        const { container } = render(
            <StatisticsFilters {...defaultProps} className="test-class" style={{ marginLeft: '20px' }} />
        );
        const wrapper = container.firstChild as HTMLElement;
        expect(wrapper.className).toContain('test-class');
        expect(wrapper.style.marginLeft).toBe('20px');
    });
});
