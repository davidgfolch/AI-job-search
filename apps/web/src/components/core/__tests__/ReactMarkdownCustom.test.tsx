import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ReactMarkdownCustom from '../../core/ReactMarkdownCustom';

describe('ReactMarkdownCustom', () => {
    it('renders plain text correctly', () => {
        render(<ReactMarkdownCustom>Hello World</ReactMarkdownCustom>);
        expect(screen.getByText('Hello World')).toBeInTheDocument();
    });

    it('renders standard markdown links correctly', () => {
        render(<ReactMarkdownCustom>[Link](http://example.com)</ReactMarkdownCustom>);
        const link = screen.getByText('Link');
        expect(link).toHaveAttribute('href', 'http://example.com');
        expect(link.tagName).toBe('A');
    });

    const assertTextTobe = (text: string, htmlTag: string) => {
        const element = screen.getByText(text);
        expect(element.tagName).toBe(htmlTag);
        return element;
    };

    it('renders color syntax as styled span', () => {
        render(<ReactMarkdownCustom>:red[Red Text]</ReactMarkdownCustom>);
        const coloredSpan = assertTextTobe('Red Text', 'SPAN');
        // Check inline style to avoid RGB conversion issues
        expect(coloredSpan.style.color).toBe('red');
    });

    it('renders complex color syntax', () => {
        render(<ReactMarkdownCustom>:green[Green text] and :blue[Blue text]</ReactMarkdownCustom>);
        const greenSpan = assertTextTobe('Green text', 'SPAN');
        expect(greenSpan.style.color).toBe('green');
        const blueSpan = assertTextTobe('Blue text', 'SPAN');
        expect(blueSpan.style.color).toBe('blue');
    });

    it('handles null children gracefully', () => {
        const { container } = render(<ReactMarkdownCustom>{null}</ReactMarkdownCustom>);
        expect(container).toBeEmptyDOMElement();
    });

    it('generates IDs for headings', () => {
        render(
            <ReactMarkdownCustom>
                {`
# Main Title
## Sub Title
### Start & Stop
                `}
            </ReactMarkdownCustom>
        );

        const h1 = screen.getByRole('heading', { level: 1 });
        expect(h1).toHaveAttribute('id', 'main-title');

        const h2 = screen.getByRole('heading', { level: 2 });
        expect(h2).toHaveAttribute('id', 'sub-title');

        const h3 = screen.getByRole('heading', { level: 3 });
        expect(h3).toHaveAttribute('id', 'start-stop');
    });

    it('scrolls to element when clicking internal link', () => {
        // Setup mocks
        const scrollIntoViewMock = vi.fn();
        const pushStateMock = vi.fn();
        const originalPushState = window.history.pushState;
        window.history.pushState = pushStateMock;

        // Mock document.getElementById to return an element with scrollIntoView
        const mockElement = document.createElement('div');
        mockElement.scrollIntoView = scrollIntoViewMock;
        vi.spyOn(document, 'getElementById').mockReturnValue(mockElement);

        render(<ReactMarkdownCustom>[Go to section](#my-section)</ReactMarkdownCustom>);

        const link = screen.getByText('Go to section');
        fireEvent.click(link);

        expect(document.getElementById).toHaveBeenCalledWith('my-section');
        expect(scrollIntoViewMock).toHaveBeenCalledWith({ behavior: 'smooth' });
        expect(pushStateMock).toHaveBeenCalledWith(null, '', '#my-section');

        // Cleanup
        window.history.pushState = originalPushState;
        vi.restoreAllMocks();
    });
});
