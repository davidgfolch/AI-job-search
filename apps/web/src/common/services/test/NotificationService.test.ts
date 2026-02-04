import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { notificationService } from '../NotificationService';

describe('NotificationService', () => {
    const MockNotification = vi.fn() as any;
    MockNotification.requestPermission = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        vi.stubGlobal('Notification', MockNotification);
        MockNotification.mockClear();
        MockNotification.requestPermission.mockClear();
        MockNotification.permission = 'default';
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it('should request permission', () => {
        notificationService.requestPermission();
        expect(MockNotification.requestPermission).toHaveBeenCalled();
    });

it.each([
        ['granted', true],
        ['denied', false],
        ['default', false]
    ])('should check permission correctly for %s', (permission, expected) => {
        MockNotification.permission = permission;
        expect(notificationService.hasPermission()).toBe(expected);
    });

    it('should send notification if permission granted', () => {
        MockNotification.permission = 'granted';
        notificationService.notify('Test', { body: 'Content' });
        expect(MockNotification).toHaveBeenCalledWith('Test', { body: 'Content' });
    });

    it('should NOT send notification if permission denied', () => {
        MockNotification.permission = 'denied';
        notificationService.notify('Test');
        expect(MockNotification).not.toHaveBeenCalled();
    });
});
