export class NotificationService {
    private isSupported(): boolean {
        return 'Notification' in window;
    }

    public requestPermission(): void {
        if (this.isSupported()) {
            Notification.requestPermission();
        }
    }

    public hasPermission(): boolean {
        return this.isSupported() && Notification.permission === 'granted';
    }

    public notify(title: string, options?: NotificationOptions): void {
        if (this.hasPermission()) {
            try {
                new Notification(title, options);
            } catch (e) {
                console.error('Error showing notification', e);
            }
        }
    }
}

export const notificationService = new NotificationService();
