import defaultFilterConfigurations from '../../../resources/defaultFilterConfigurations.json';

const persistenceDefaults: Record<string, any> = {
    'filter_configurations': defaultFilterConfigurations,
    'default_comment_text': '- applied by 45k',
};

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
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.error("Failed to save persistence data for key:", key, error);
    }
  },
};
