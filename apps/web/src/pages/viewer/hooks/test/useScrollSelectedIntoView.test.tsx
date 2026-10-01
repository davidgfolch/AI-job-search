import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { useRef } from 'react';
import { useScrollSelectedIntoView } from '../useScrollSelectedIntoView';
import { stubElementRect } from '../../test/test-utils';

const LIST = { top: 100, bottom: 200, left: 0, right: 200 };
const HEADER = { top: 100, bottom: 130 }; // The sticky header floats over the top of the scroll port

const Harness = ({ selectedId }: { selectedId?: number }) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const rowRef = useRef<HTMLTableRowElement>(null);
    useScrollSelectedIntoView({ containerRef, rowRef, selectedId });
    return (
        <div ref={containerRef}>
            <table>
                <thead><tr><th>Header</th></tr></thead>
                <tbody><tr id="job-row-1" ref={rowRef} /></tbody>
            </table>
        </div>
    );
};

/** Publishes the geometry of the list, of its sticky header and of the row, then selects the row. */
const selectRow = ({ row, list = LIST, header = HEADER }) => {
    const { container: rendered, rerender } = render(<Harness />);
    const container = rendered.firstElementChild as HTMLDivElement;
    stubElementRect(container, list);
    stubElementRect(container.querySelector('thead')!, header);
    stubElementRect(container.querySelector('#job-row-1')!, row);
    rerender(<Harness selectedId={1} />);
    return container;
};

describe('useScrollSelectedIntoView', () => {
    it.each([
        { name: 'below the frame', row: { top: 210, bottom: 230 }, expected: 30 },
        { name: 'above the frame, clearing the sticky header', row: { top: 105, bottom: 125 }, expected: -25 },
        { name: 'taller than the frame, anchored under the header', row: { top: 140, bottom: 220 }, expected: 10 },
    ])('scrolls the list to reach a row $name', ({ row, expected }) => {
        const container = selectRow({ row });

        expect(container.scrollTop).toBe(expected);
    });

    it.each([
        { name: 'between the header and the bottom edge', row: { top: 140, bottom: 160 } },
        { name: 'flush with the bottom edge', row: { top: 180, bottom: 200 } },
    ])('does not move a row that is already readable $name', ({ row }) => {
        const container = selectRow({ row });

        expect(container.scrollTop).toBe(0);
    });

    it('does not scroll horizontally a row that fits the width of the list', () => {
        const container = selectRow({ row: { top: 140, bottom: 160, left: 20, right: 120 } });

        expect(container.scrollLeft).toBe(0);
    });

    it('scrolls horizontally a row that runs past the right edge', () => {
        const container = selectRow({ row: { top: 140, bottom: 160, left: 150, right: 250 } });

        expect(container.scrollLeft).toBe(50);
        expect(container.scrollTop).toBe(0);
    });

    it('leaves a row alone when there is no sticky header covering it', () => {
        const container = selectRow({ row: { top: 105, bottom: 125 }, header: { top: 100, bottom: 100 } });

        expect(container.scrollTop).toBe(0);
    });

    it('does not scroll a list that is not laid out, such as a hidden tab', () => {
        const container = selectRow({ row: { top: 210, bottom: 230 }, list: { top: 100, bottom: 100 } });

        expect(container.scrollTop).toBe(0);
    });

    it('does not scroll when nothing is selected', () => {
        const { container: rendered, rerender } = render(<Harness />);
        const container = rendered.firstElementChild as HTMLDivElement;
        stubElementRect(container, LIST);
        stubElementRect(container.querySelector('#job-row-1')!, { top: 210, bottom: 230 });

        rerender(<Harness selectedId={undefined} />);

        expect(container.scrollTop).toBe(0);
    });
});
