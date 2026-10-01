import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import SkillTag from '../SkillTag';

type RectInput = { top: number; left: number; width: number; height: number };

const rect = ({ top, left, width, height }: RectInput): DOMRect =>
    ({ top, left, width, height, bottom: top + height, right: left + width, x: left, y: top, toJSON: () => ({}) }) as DOMRect;

const setViewport = (width: number, height: number) => {
    Object.defineProperty(window, 'innerWidth', { value: width, configurable: true });
    Object.defineProperty(window, 'innerHeight', { value: height, configurable: true });
};

/** The layout effect measures the trigger button and the portal card separately. */
const mockRects = (button: RectInput, card: RectInput) => {
    vi.spyOn(Element.prototype, 'getBoundingClientRect').mockImplementation(function (this: Element) {
        const cls = typeof this.className === 'string' ? this.className : '';
        if (cls.includes('skill-detail-btn')) return rect(button);
        if (cls.includes('skill-description-card')) return rect(card);
        return rect({ top: 0, left: 0, width: 0, height: 0 });
    });
};

const showCard = () => fireEvent.mouseEnter(screen.getByLabelText('View skill details'));
const cardStyle = () => (document.querySelector('.skill-description-card') as HTMLElement).style;

describe('SkillTag description card', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        setViewport(1024, 768);
    });

    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
    });

    const renderTag = () => render(<SkillTag skill="Rust" description="A systems language" isInLearnList onToggle={vi.fn()} onViewDetail={vi.fn()} />);

    it('hides the card 300ms after the pointer leaves the trigger', () => {
        vi.useFakeTimers();
        renderTag();
        showCard();
        expect(document.querySelector('.skill-description-card')).toBeInTheDocument();
        fireEvent.mouseLeave(screen.getByLabelText('View skill details'));
        expect(document.querySelector('.skill-description-card')).toBeInTheDocument();
        act(() => { vi.advanceTimersByTime(300); });
        expect(document.querySelector('.skill-description-card')).toBeNull();
    });

    it('cancels the pending hide when the pointer comes back before the timer fires', () => {
        vi.useFakeTimers();
        renderTag();
        const trigger = screen.getByLabelText('View skill details');
        showCard();
        fireEvent.mouseLeave(trigger);
        fireEvent.mouseEnter(trigger);
        act(() => { vi.advanceTimersByTime(300); });
        expect(document.querySelector('.skill-description-card')).toBeInTheDocument();
    });

    it('keeps the card open while the pointer moves onto the card itself', () => {
        vi.useFakeTimers();
        renderTag();
        showCard();
        fireEvent.mouseLeave(screen.getByLabelText('View skill details'));
        fireEvent.mouseEnter(document.querySelector('.skill-description-card') as HTMLElement);
        act(() => { vi.advanceTimersByTime(300); });
        expect(document.querySelector('.skill-description-card')).toBeInTheDocument();
    });

    it('centres the card under the button when there is room below', () => {
        mockRects({ top: 100, left: 100, width: 40, height: 20 }, { top: 0, left: 0, width: 200, height: 100 });
        renderTag();
        showCard();
        expect(cardStyle().top).toBe('128px');
        expect(cardStyle().left).toBe('20px');
        expect(cardStyle().position).toBe('fixed');
        expect(cardStyle().zIndex).toBe('10000');
    });

    it('flips the card above the button when it would overflow the viewport bottom', () => {
        setViewport(1024, 300);
        mockRects({ top: 250, left: 100, width: 40, height: 20 }, { top: 0, left: 0, width: 200, height: 100 });
        renderTag();
        showCard();
        expect(cardStyle().top).toBe('142px');
    });

    it('pins the card to the top when it does not fit below or above', () => {
        setViewport(1024, 200);
        mockRects({ top: 100, left: 100, width: 40, height: 20 }, { top: 0, left: 0, width: 200, height: 300 });
        renderTag();
        showCard();
        expect(cardStyle().top).toBe('10px');
    });

    it('clamps the card to the left viewport edge', () => {
        mockRects({ top: 100, left: 0, width: 20, height: 20 }, { top: 0, left: 0, width: 200, height: 100 });
        renderTag();
        showCard();
        expect(cardStyle().left).toBe('10px');
    });

    it('clamps the card to the right viewport edge', () => {
        mockRects({ top: 100, left: 900, width: 20, height: 20 }, { top: 0, left: 0, width: 300, height: 100 });
        renderTag();
        showCard();
        expect(cardStyle().left).toBe('714px');
    });

    it('does not render a card when the skill has no description', () => {
        render(<SkillTag skill="Rust" isInLearnList onToggle={vi.fn()} onViewDetail={vi.fn()} />);
        showCard();
        expect(document.querySelector('.skill-description-card')).toBeNull();
    });
});