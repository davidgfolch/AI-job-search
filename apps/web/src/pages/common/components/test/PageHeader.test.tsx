import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import PageHeader from '../PageHeader';

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('PageHeader', () => {
    it('renders the title correctly', () => {
        renderWithRouter(<PageHeader title="Test Title" />);
        expect(screen.getByText('AI Job Search - Test Title')).toBeInTheDocument();
    });

    it('renders children when provided', () => {
        renderWithRouter(
            <PageHeader title="Test Title">
                <button>Action Button</button>
            </PageHeader>
        );
        expect(screen.getByText('Action Button')).toBeInTheDocument();
    });

    it('always renders the HeaderMenu', () => {
        renderWithRouter(<PageHeader title="Test Title" />);
        expect(screen.getByText('Menu')).toBeInTheDocument();
    });

    it('updates the document title', () => {
        renderWithRouter(<PageHeader title="Test Title" />);
        expect(document.title).toBe('AI Job Search - Test Title');
    });
});
