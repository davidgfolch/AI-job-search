import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
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
});
