import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';
import { calculateLapsedTime, calculateLapsedTimeDetail } from '../dateUtils';

// Helper to get time string HH:MM from a Date object
// This ensures we match the local time output of dateUtils.ts (getHours/getMinutes)
const getTimeString = (dateString: string) => {
    const date = new Date(dateString);
    const hours = date.getHours().toString();
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
};

describe('dateUtils', () => {
    const mockNow = new Date('2023-10-15T12:00:00Z');

    beforeEach(() => {
        vi.useFakeTimers();
        vi.setSystemTime(mockNow);
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    describe('calculateLapsedTime', () => {
        it.each([
            { input: null, expected: '-' },
            { input: undefined, expected: '-' },
            { input: 'invalid-date', expected: '-' },
        ])('returns "$expected" for invalid input: $input', ({ input, expected }) => {
            expect(calculateLapsedTime(input)).toBe(expected);
        });

        it.each([
            {
                desc: 'same day (today)',
                inputDate: '2023-10-15T08:00:00Z',
                // diffDays=0. Implementation returns HH:MM
                expectedFn: (date: string) => getTimeString(date)
            },
            {
                desc: '1 day ago (yesterday)',
                inputDate: '2023-10-14T12:00:00Z',
                // diffDays=1. Implementation returns '1d' + time (because diffDays < 2)
                expectedFn: (date: string) => `1d ${getTimeString(date)}`
            },
            {
                desc: '5 days ago',
                inputDate: '2023-10-10T12:00:00Z',
                // diffDays=5. Implementation returns '5d' (no time because diffDays >= 2)
                expectedFn: () => '5d'
            },
            {
                desc: '8 days ago (1 week)',
                inputDate: '2023-10-07T12:00:00Z',
                // diffDays=8. Implementation returns '1w'
                expectedFn: () => '1w'
            },
            {
                desc: '15 days ago (2 weeks)',
                inputDate: '2023-09-30T12:00:00Z',
                // diffDays=15. Implementation returns '2w'
                expectedFn: () => '2w'
            },
            {
                desc: '31 days ago (1 month)',
                inputDate: '2023-09-14T12:00:00Z',
                // diffDays=31. Implementation returns '1m'
                expectedFn: () => '1m'
            },
            {
                desc: '61 days ago (2 months)',
                inputDate: '2023-08-15T12:00:00Z',
                // diffDays=61. Implementation returns '2m'
                expectedFn: () => '2m'
            }
        ])('returns correct format for $desc', ({ inputDate, expectedFn }) => {
            expect(calculateLapsedTime(inputDate)).toBe(expectedFn(inputDate));
        });
    });

    describe('calculateLapsedTimeDetail', () => {
        it.each([
            { input: null, expected: '-' },
        ])('returns "$expected" for invalid input: $input', ({ input, expected }) => {
            expect(calculateLapsedTimeDetail(input)).toBe(expected);
        });

        it.each([
            {
                desc: 'same day',
                inputDate: '2023-10-15T08:00:00Z',
                // 'today' + time
                expectedFn: (date: string) => `today ${getTimeString(date)}`
            },
            {
                desc: '1 day ago',
                inputDate: '2023-10-14T12:00:00Z',
                // 'yesterday' + time
                expectedFn: (date: string) => `yesterday ${getTimeString(date)}`
            },
            {
                desc: '5 days ago',
                inputDate: '2023-10-10T12:00:00Z',
                // '5 days ago' + time
                expectedFn: (date: string) => `5 days ago ${getTimeString(date)}`
            },
            {
                desc: '15 days ago',
                inputDate: '2023-09-30T12:00:00Z',
                // '2 weeks ago' + time
                expectedFn: (date: string) => `2 weeks ago ${getTimeString(date)}`
            },
            {
                desc: '61 days ago',
                inputDate: '2023-08-15T12:00:00Z',
                // '2 months ago' + time
                expectedFn: (date: string) => `2 months ago ${getTimeString(date)}`
            }
        ])('returns correct detailed format for $desc', ({ inputDate, expectedFn }) => {
            expect(calculateLapsedTimeDetail(inputDate)).toBe(expectedFn(inputDate));
        });
    });
});
