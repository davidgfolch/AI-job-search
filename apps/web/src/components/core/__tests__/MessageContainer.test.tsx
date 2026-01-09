import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import MessageContainer from '../MessageContainer';

describe('MessageContainer', () => {
    it('renders message', () => {
        render(<MessageContainer message={{ text: 'Hello', type: 'success' }} error={null} onDismissMessage={vi.fn()} />);
        expect(screen.getByText('Hello')).toBeInTheDocument();
    });

    it('renders error', () => {
        render(<MessageContainer message={null} error={new Error('Boom')} onDismissMessage={vi.fn()} />);
        expect(screen.getByText('Boom')).toBeInTheDocument();
    });
});
