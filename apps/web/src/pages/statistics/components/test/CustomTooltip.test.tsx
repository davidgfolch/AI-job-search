import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import CustomTooltip from '../CustomTooltip';

const mockPayload = [
    { color: '#0000ff', name: 'LinkedIn', value: 10, payload: {} },
    { color: '#ff0000', name: 'Indeed', value: 5, payload: {} },
];

describe('CustomTooltip', () => {
    describe('showDateLabel', () => {
        it('shows date label when showDateLabel is true', () => {
            render(
                <CustomTooltip
                    active={true}
                    payload={mockPayload}
                    label="2024-01-15"
                    showDateLabel={true}
                />
            );
            expect(screen.getByText(/Jan 15, 2024/)).toBeDefined();
        });

        it('shows date label when showDateLabel is undefined (default)', () => {
            render(
                <CustomTooltip
                    active={true}
                    payload={mockPayload}
                    label="2024-01-15"
                />
            );
            expect(screen.getByText(/Jan 15, 2024/)).toBeDefined();
        });

        it('hides date label when showDateLabel is false', () => {
            render(
                <CustomTooltip
                    active={true}
                    payload={mockPayload}
                    label="2024-01-15"
                    showDateLabel={false}
                />
            );
            expect(screen.queryByText(/Jan 15, 2024/)).toBeNull();
        });
    });

    describe('rendering', () => {
        it('returns null when not active', () => {
            const { container } = render(
                <CustomTooltip
                    active={false}
                    payload={mockPayload}
                    label="2024-01-15"
                />
            );
            expect(container.firstChild).toBeNull();
        });

        it('returns null when payload is empty', () => {
            const { container } = render(
                <CustomTooltip
                    active={true}
                    payload={[]}
                    label="2024-01-15"
                />
            );
            expect(container.firstChild).toBeNull();
        });

        it('renders payload entries correctly', () => {
            render(
                <CustomTooltip
                    active={true}
                    payload={mockPayload}
                    label="2024-01-15"
                />
            );
            expect(screen.getByText('LinkedIn: 10')).toBeDefined();
            expect(screen.getByText('Indeed: 5')).toBeDefined();
        });

        it('renders Other details when present', () => {
            const payloadWithOther = [
                {
                    color: '#888888',
                    name: 'Other',
                    value: 15,
                    payload: {
                        otherDetails: {
                            'Source1': 10,
                            'Source2': 5,
                        }
                    }
                }
            ];
            render(
                <CustomTooltip
                    active={true}
                    payload={payloadWithOther}
                    label="2024-01-15"
                />
            );
            expect(screen.getByText('Source1: 10')).toBeDefined();
            expect(screen.getByText('Source2: 5')).toBeDefined();
        });
    });

    describe('formatDate', () => {
        it('formats date string correctly', () => {
            render(
                <CustomTooltip
                    active={true}
                    payload={mockPayload}
                    label="2024-03-18"
                />
            );
            expect(screen.getByText(/Mar 18, 2024/)).toBeDefined();
        });

        it('handles numeric timestamp', () => {
            render(
                <CustomTooltip
                    active={true}
                    payload={mockPayload}
                    label={1710806400000}
                />
            );
            // Timestamp converts to local time, check that any date in March 2024 is shown
            expect(screen.getByText(/Mar .*, 2024/)).toBeDefined();
        });

        it('handles undefined label gracefully', () => {
            render(
                <CustomTooltip
                    active={true}
                    payload={mockPayload}
                    label={undefined}
                />
            );
            // With showDateLabel defaulting to true, p element renders but with empty text
            const pElement = document.querySelector('p');
            expect(pElement).toBeDefined();
            expect(pElement?.textContent).toBe('');
        });
    });
});