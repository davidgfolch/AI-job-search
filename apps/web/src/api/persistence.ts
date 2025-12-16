import { persistenceDefaults } from '../data/defaults';

export const persistenceApi = {
  getValue: async <T>(key: string): Promise<T | null> => {
    try {
        // 1. Try LocalStorage
        const stored = localStorage.getItem(key);
        if (stored) {
            return JSON.parse(stored);
        }

        // 2. Fallback to Defaults
        if (Object.prototype.hasOwnProperty.call(persistenceDefaults, key)) {
            return persistenceDefaults[key] as T;
        }

        return null;
    } catch (error) {
        console.error("Failed to load persistence data for key:", key, error);
        return null;
    }
  },

  setValue: async <T>(key: string, value: T): Promise<void> => {
    try {
        // 1. Save to LocalStorage
        localStorage.setItem(key, JSON.stringify(value));

        // 2. Provide Developer Feedback (for persisting to GitHub)
        if (import.meta.env.DEV) {
            const exportData = JSON.stringify(value, null, 2);
            console.groupCollapsed(`[Persistence] Saved '${key}' locally.`);
            console.info("To persist this configuration in the repository for all users:");
            console.info(`1. Open 'apps/web/src/data/defaults.ts'`);
            console.info(`2. Update the '${key}' entry with this value:`);
            console.log(exportData);
            console.groupEnd();
        }
    } catch (error) {
        console.error("Failed to save persistence data for key:", key, error);
    }
  },
};
