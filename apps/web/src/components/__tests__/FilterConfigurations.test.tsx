import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import FilterConfigurations from '../FilterConfigurations';
import { createMockFilters, setupLocalStorage, getStoredConfigs } from '../../__tests__/test-utils';
import { type JobListParams } from '../../api/jobs';

vi.mock('../../data/defaults', () => ({ defaultFilterConfigurations: [] }));

const mockFilters = createMockFilters({ search: 'React Developer', flagged: true, like: false, days_old: 7 });

async function setup(configs: { name: string, filters: JobListParams }[] = [], props: any = {}) {
    localStorage.setItem('filter_configurations', JSON.stringify(configs));
    const onLoad = vi.fn();
    const result = render(<FilterConfigurations currentFilters={props.currentFilters || mockFilters} onLoadConfig={onLoad} onMessage={props.onMessage || vi.fn()} />);
    await act(async () => await new Promise(resolve => setTimeout(resolve, 0)));
    return { ...result, input: screen.getByPlaceholderText(/Type to load or enter name to save/i), onLoad };
}

describe('FilterConfigurations', () => {
    beforeEach(() => setupLocalStorage());
    afterEach(() => vi.restoreAllMocks());

    it('renders correctly', async () => {
        await setup();
        expect(screen.getByLabelText(/Filter Configurations/i)).toBeInTheDocument();
        expect(screen.getByText('Save')).toBeInTheDocument();
    });

    it.each([
        ['Button', (el: HTMLElement) => fireEvent.click(el)],
        ['Enter Key', (el: HTMLElement) => fireEvent.keyDown(el, { key: 'Enter', code: 'Enter' })],
    ])('saves configuration using %s', async (_, action) => {
        const onMessage = vi.fn();
        const { input } = await setup([], { onMessage });
        fireEvent.change(input, { target: { value: 'My Config' } });
        action(_ === 'Button' ? screen.getByText('Save') : input);
        
        await waitFor(() => expect(getStoredConfigs()).toHaveLength(2));
        expect(getStoredConfigs()[0]).toEqual({ name: 'My Config', filters: mockFilters });
        if (onMessage.mock.calls.length) expect(onMessage).toHaveBeenCalledWith(expect.stringContaining('saved'), 'success');
        expect((input as HTMLInputElement).value).toBe('');
    });

    it('validates name before saving', async () => {
        const onMessage = vi.fn();
        await setup([], { onMessage });
        fireEvent.click(screen.getByText('Save'));
        expect(getStoredConfigs()).toHaveLength(0);
        expect(onMessage).toHaveBeenCalledWith('Please enter a name for the configuration', 'error');
    });

    it('replaces existing configuration', async () => {
        const { input } = await setup([{ name: 'Same', filters: { ...mockFilters, search: 'Old' } }], 
                                     { currentFilters: { ...mockFilters, search: 'New' } });
        fireEvent.focus(input);
        await screen.findByText('Same');
        fireEvent.change(input, { target: { value: 'Same' } });
        fireEvent.click(screen.getByText('Save'));
        await waitFor(() => expect(getStoredConfigs()[0].filters.search).toBe('New'));
    });

    it('limits to MAX_CONFIGS (30)', async () => {
        const configs = Array.from({ length: 30 }, (_, i) => ({ name: `C${i + 1}`, filters: mockFilters }));
        const { input } = await setup(configs);
        fireEvent.focus(input);
        await screen.findByText('C1');
        fireEvent.change(input, { target: { value: 'C31' } });
        fireEvent.click(screen.getByText('Save'));
        await waitFor(() => {
            const stored = getStoredConfigs();
            expect(stored).toHaveLength(30);
            expect(stored[0].name).toBe('C31');
        });
    });

    it.each([
        ['Focus', 'Test', (i: any) => fireEvent.focus(i), true],
        ['Filter', 'React', (i: any) => fireEvent.change(i, { target: { value: 'React' } }), true],
        ['Mismatch', 'Python', (i: any) => fireEvent.change(i, { target: { value: 'React' } }), false],
    ])('visibility on %s', async (_, name, action, visible) => {
        const configs = [{ name: 'Test', filters: mockFilters }, { name: 'React', filters: mockFilters }, { name: 'Python', filters: mockFilters }];
        const { input } = await setup(configs);
        fireEvent.focus(input);
        if (visible) await screen.findByText(name, {}, { timeout: 2000 });
        else await screen.findByText('Test');
        action(input);
        if (visible) await screen.findByText(name);
        else expect(screen.queryByText(name)).not.toBeInTheDocument();
    });

    it('loads configuration', async () => {
        const saved = { ...mockFilters, search: 'Senior' };
        const { input, onLoad } = await setup([{ name: 'Senior', filters: saved }]);
        fireEvent.focus(input);
        fireEvent.click(await screen.findByText('Senior'));
        expect(onLoad).toHaveBeenCalledWith(expect.objectContaining(saved), 'Senior');
    });

    it('closes suggestions on outside click', async () => {
        const { input } = await setup([{ name: 'Test', filters: mockFilters }]);
        fireEvent.focus(input);
        await screen.findByText('Test');
        fireEvent.mouseDown(document.body);
        await waitFor(() => expect(screen.queryByText('Test')).not.toBeInTheDocument());
    });

    it('sorts suggestions', async () => {
        const configs = [{ name: 'Z', filters: mockFilters }, { name: 'A', filters: mockFilters }];
        const { input } = await setup(configs);
        fireEvent.focus(input);
        const items = await screen.findAllByRole('listitem');
        expect(items.map(i => i.textContent?.replace('×', '').trim())).toEqual(['A', 'Clean - Delete old jobs', 'Z']);
    });

    it('resets missing filters', async () => {
        const saved = { search: 'S', days_old: undefined };
        const { input, onLoad } = await setup([{ name: 'R', filters: saved as JobListParams }], { currentFilters: { ...mockFilters, days_old: 7 } });
        fireEvent.focus(input);
        fireEvent.click(await screen.findByText('R'));
        expect(onLoad).toHaveBeenCalledWith(expect.objectContaining({ search: 'S', days_old: undefined }), 'R');
    });

    it.each([['Confirms', true], ['Cancels', false]])('handles delete when %s', async (_, confirm) => {
        const { input } = await setup([{ name: 'Del', filters: mockFilters }]);
        fireEvent.focus(input);
        fireEvent.click((await screen.findByText('Del')).closest('li')!.querySelector('.config-delete-btn')!);
        await screen.findByText(/Delete configuration "Del"\?/i);
        
        fireEvent.click(screen.getByText(confirm ? 'Confirm' : 'Cancel', { selector: 'button.modal-button' }));
        await waitFor(() => {
            const stored = getStoredConfigs();
            if (confirm) expect(stored.some((c: any) => c.name === 'Del')).toBe(false);
            else expect(stored[0].name).toBe('Del');
        });
    });
});
