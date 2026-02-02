import { describe, it, expect } from 'vitest';
import defaultFilterConfigurations from '../../../../resources/defaultFilterConfigurations.json';

describe('defaults', () => {
  describe('defaultFilterConfigurations', () => {
    it('is an array of filter configurations', () => {
      expect(Array.isArray(defaultFilterConfigurations)).toBe(true);
      expect(defaultFilterConfigurations.length).toBeGreaterThan(0);
    });

    it('each configuration has name and filters properties', () => {
      defaultFilterConfigurations.forEach(config => {
        expect(config).toHaveProperty('name');
        expect(config).toHaveProperty('filters');
        expect(typeof config.name).toBe('string');
        expect(typeof config.filters).toBe('object');
      });
    });

    it('configurations have expected filter properties', () => {
      const firstConfig = defaultFilterConfigurations[0];
      expect(firstConfig.filters).toHaveProperty('page');
      expect(firstConfig.filters).toHaveProperty('size');
      expect(firstConfig.filters).toHaveProperty('order');
    });

    it('contains specific default configurations', () => {
      const configNames = defaultFilterConfigurations.map(c => c.name);
      expect(configNames).toContain('By company');
      expect(configNames).toContain('Java backend only');
    });
  });
});
