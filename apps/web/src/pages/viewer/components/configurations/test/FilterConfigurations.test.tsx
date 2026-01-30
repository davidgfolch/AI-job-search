// @vitest-environment jsdom
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mockFilters, setup, configureMockServiceBehavior } from '../../../test/FilterConfigurationsTestUtils.tsx';

describe('FilterConfigurations Saving', () => {
    const isLoadedRef = { value: false };

    beforeEach(() => {
        configureMockServiceBehavior(isLoadedRef);
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('renders correctly', async () => {
        await setup([], {}, isLoadedRef);
        expect(screen.getByLabelText(/Filter Configurations/i)).toBeInTheDocument();
        expect(screen.getByText('Save')).toBeInTheDocument();
    });

    // Parameterized test for saving methods
    it.each([
        ['Button', (el: HTMLElement) => fireEvent.click(el)],
        ['Enter Key', (el: HTMLElement) => fireEvent.keyDown(el, { key: 'Enter', code: 'Enter' })],
    ])('saves configuration using %s', async (_, action) => {
        const onMessage = vi.fn();
        const { input } = await setup([], { onMessage }, isLoadedRef);
        
        fireEvent.change(input, { target: { value: 'My Config' } });
        // Start waiting for the success message to appear which indicates save completion
        action(_ === 'Button' ? screen.getByText('Save') : input);
        
        await waitFor(() => {
            expect(localStorage.getItem('filter_configurations')).toContain('My Config');
            expect(input.value).toBe('');
        });
        
        expect(onMessage).toHaveBeenCalledWith(expect.stringContaining('saved'), 'success');
    });

    it('validates name before saving', async () => {
        const onMessage = vi.fn();
        await setup([], { onMessage }, isLoadedRef);
        fireEvent.click(screen.getByText('Save'));
        expect(localStorage.getItem('filter_configurations')).toBeNull();
        expect(onMessage).toHaveBeenCalledWith('Please enter a name for the configuration', 'error');
    });

    it('limits to MAX_CONFIGS (30)', async () => {
        const configs = Array.from({ length: 30 }, (_, i) => ({ name: `C${i + 1}`, filters: mockFilters }));
        const { input } = await setup(configs, {}, isLoadedRef);
        
        fireEvent.focus(input);
        await screen.findByText('C1');
        
        fireEvent.change(input, { target: { value: 'C31' } });
        fireEvent.click(screen.getByText('Save'));
        
        await waitFor(() => {
            const stored = JSON.parse(localStorage.getItem('filter_configurations') || '[]');
            expect(stored).toHaveLength(30);
            expect(stored[0].name).toBe('C31');
        });
    });
});
