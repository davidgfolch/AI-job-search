import { vi } from 'vitest';

export const createNotificationServiceMock = () => ({
  notificationService: {
    requestPermission: vi.fn().mockResolvedValue(true),
    notify: vi.fn(),
    hasPermission: vi.fn().mockReturnValue(true),
  }
});

export const createBroadcastChannelMock = () => ({
  BroadcastChannel: vi.fn().mockImplementation(() => ({
    postMessage: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    close: vi.fn(),
  })),
});

export const setupServiceMocks = () => {
  const notificationServiceMock = createNotificationServiceMock();
  const broadcastChannelMock = createBroadcastChannelMock();
  
  vi.mock('@/common/services/NotificationService', () => notificationServiceMock);
  
  if (typeof globalThis.BroadcastChannel === 'undefined') {
    globalThis.BroadcastChannel = broadcastChannelMock.BroadcastChannel as any;
  }
  
  return {
    notificationServiceMock,
    broadcastChannelMock,
  };
};