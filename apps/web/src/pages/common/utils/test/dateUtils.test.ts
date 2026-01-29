
import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';
import { calculateLapsedTime } from '../dateUtils';

describe('calculateLapsedTime', () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('returns "-" for null or undefined', () => {
        expect(calculateLapsedTime(null)).toBe('-');
        expect(calculateLapsedTime(undefined)).toBe('-');
    });

    it('returns "-" for invalid date string', () => {
        expect(calculateLapsedTime('invalid-date')).toBe('-');
    });

    it('returns time for same day', () => {
        const now = new Date('2023-10-10T12:00:00Z');
        vi.setSystemTime(now);
        // 2023-10-10T08:00:00Z is 8:00 UTC (assuming test runs in UTC or controlled timezone, but here we mock system time).
        // Wait, Date.getHours() uses local time. If the test environment is not controlled for timezone, this might be flaky.
        // However, standard CI/Vitest behavior usually defaults to UTC or we can rely on how `vi.setSystemTime` works with `new Date`.
        // Let's assume the constructed Date objects work predictably.
        // '2023-10-10T08:00:00Z' -> The Date object is created.
        // getHours() will return the local hour.
        
        // To be safe and matching the implementation which uses .getHours(), we should verify what that returns.
        const testDate = new Date('2023-10-10T08:00:00Z');
        const hours = testDate.getHours().toString();
        const minutes = testDate.getMinutes().toString().padStart(2, '0');
        
        expect(calculateLapsedTime('2023-10-10T08:00:00Z')).toBe(`${hours}:${minutes}`);
    });

    it('returns "yesterday" for 1 day ago', () => {
        const now = new Date('2023-10-11T12:00:00Z');
        vi.setSystemTime(now);
        expect(calculateLapsedTime('2023-10-10T12:00:00Z')).toBe('yesterday');
    });

    it('returns "X days" for less than 7 days', () => {
        const now = new Date('2023-10-15T12:00:00Z');
        vi.setSystemTime(now);
        // 5 days ago
        expect(calculateLapsedTime('2023-10-10T12:00:00Z')).toBe('5d ago');
    });

    it('returns "X weeks" for less than 30 days', () => {
        const now = new Date('2023-10-25T12:00:00Z');
        vi.setSystemTime(now);
        // 15 days ago -> 2 weeks
        expect(calculateLapsedTime('2023-10-10T12:00:00Z')).toBe('2w ago');
        
        // 8 days ago -> 1 week
        const now2 = new Date('2023-10-18T12:00:00Z');
        vi.setSystemTime(now2);
        expect(calculateLapsedTime('2023-10-10T12:00:00Z')).toBe('1w ago');
    });

    it('returns "X months" for 30 days or passed', () => {
        const now = new Date('2023-12-10T12:00:00Z');
        vi.setSystemTime(now);
        // 61 days ago -> 2 months
        expect(calculateLapsedTime('2023-10-10T12:00:00Z')).toBe('2m ago');

        const now2 = new Date('2023-11-10T12:00:00Z');
        vi.setSystemTime(now2);
        // 31 days ago -> 1 month
        expect(calculateLapsedTime('2023-10-10T12:00:00Z')).toBe('1m ago');
    });
});

import { calculateLapsedTimeDetail } from '../dateUtils';

describe('calculateLapsedTimeDetail', () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('returns "-" for null or undefined', () => {
        expect(calculateLapsedTimeDetail(null)).toBe('-');
    });

    it('returns "today" for same day', () => {
        const now = new Date('2023-10-10T12:00:00Z');
        vi.setSystemTime(now);
        expect(calculateLapsedTimeDetail('2023-10-10T08:00:00Z')).toBe('today');
    });
    
    it('returns long format for days', () => {
        const now = new Date('2023-10-15T12:00:00Z');
        vi.setSystemTime(now);
        // 5 days ago
        expect(calculateLapsedTimeDetail('2023-10-10T12:00:00Z')).toBe('5 days ago');
        
        // 1 day ago
        const now2 = new Date('2023-10-11T12:00:00Z');
        vi.setSystemTime(now2);
        expect(calculateLapsedTimeDetail('2023-10-10T12:00:00Z')).toBe('yesterday');
    });

    it('returns long format for weeks', () => {
        const now = new Date('2023-10-25T12:00:00Z');
        vi.setSystemTime(now);
        // 15 days ago -> 2 weeks
        expect(calculateLapsedTimeDetail('2023-10-10T12:00:00Z')).toBe('2 weeks ago');
    });

    it('returns long format for months', () => {
        const now = new Date('2023-12-10T12:00:00Z');
        vi.setSystemTime(now);
        // 61 days ago -> 2 months
        expect(calculateLapsedTimeDetail('2023-10-10T12:00:00Z')).toBe('2 months ago');
    });
});
