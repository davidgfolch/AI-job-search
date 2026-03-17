// @vitest-environment jsdom
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { type JobListParams } from '../../../api/ViewerApi';
import { mockFilters, setup, configureMockServiceBehavior } from '../../../test/FilterConfigurationsTestUtils.tsx';

interface TestConfig { name: string; filters: JobListParams; pinned?: boolean; }
const testConfigs: Record<string, TestConfig> = {
    same: { name: 'Same', filters: { ...mockFilters, search: 'Old' } },
    test: { name: 'Test', filters: mockFilters },
    react: { name: 'React', filters: mockFilters },
    python: { name: 'Python', filters: mockFilters },
    senior: { name: 'Senior', filters: { ...mockFilters, search: 'Senior' } },
    del: { name: 'Del', filters: mockFilters },
    active: { name: 'Active', filters: mockFilters },
    pinnedJava: { name: 'PinnedJava', filters: mockFilters, pinned: true },
    z: { name: 'Z', filters: mockFilters },
    a: { name: 'A', filters: mockFilters },
    r: { name: 'R', filters: { search: 'S', days_old: undefined } as JobListParams },
};
const byCompanyConfigs = {
    withRlike: (companyRegex: string) => ({ name: 'By company', filters: { ...mockFilters, sql_filter: `company rlike '${companyRegex}'` } }),
    withoutRlike: { name: 'By company', filters: { ...mockFilters, sql_filter: 'company = "Test"' } },
};

describe('FilterConfigurations Interactions', () => {
    const isLoadedRef = { value: false };

    beforeAll(() => vi.stubGlobal('console', { ...console, error: vi.fn() }));
    beforeEach(() => configureMockServiceBehavior(isLoadedRef));
    afterEach(() => vi.restoreAllMocks());

    it('replaces existing configuration', async () => {
        const { input } = await setup([testConfigs.same], { currentFilters: { ...mockFilters, search: 'New' } }, isLoadedRef);
        fireEvent.focus(input);
        await screen.findByText('Same');
        fireEvent.change(input, { target: { value: 'Same' } });
        fireEvent.click(screen.getByText('Save'));
        await waitFor(() => expect(JSON.parse(localStorage.getItem('filter_configurations') || '[]')[0].filters.search).toBe('New'));
    });

    it.each([
        ['Focus', undefined, 'Test', true],
        ['Filter Match', 'React', 'React', true],
        ['Filter Mismatch', 'React', 'Python', false],
    ])('visibility check: %s', async (_, typeText, checkName, shouldBeVisible) => {
        const configs = [testConfigs.test, testConfigs.react, testConfigs.python];
        const { input } = await setup(configs, {}, isLoadedRef);
        fireEvent.focus(input);
        if (typeText) fireEvent.change(input, { target: { value: typeText } });
        if (shouldBeVisible) {
            await screen.findByText(checkName, {}, { timeout: 2000 });
        } else {
            await waitFor(() => expect(screen.queryByText(checkName)).not.toBeInTheDocument());
        }
    });

    it('loads configuration', async () => {
        const saved = { ...mockFilters, search: 'Senior' };
        const { input, onLoad } = await setup([{ name: 'Senior', filters: saved }], {}, isLoadedRef);
        fireEvent.focus(input);
        fireEvent.click(await screen.findByText('Senior'));
        expect(onLoad).toHaveBeenCalledWith(expect.objectContaining(saved), 'Senior');
    });

    it('closes suggestions on outside click', async () => {
        const { input } = await setup([testConfigs.test], {}, isLoadedRef);
        fireEvent.focus(input);
        await screen.findByText('Test');
        fireEvent.mouseDown(document.body);
        await waitFor(() => expect(screen.queryByRole('list')).not.toBeInTheDocument());
    });

    it('sorts suggestions alphabetically', async () => {
        const { input } = await setup([testConfigs.z, testConfigs.a], {}, isLoadedRef);
        fireEvent.focus(input);
        const items = await screen.findAllByRole('listitem');
        const names = items.map(i => i.textContent?.replace(/[\+\d+\📈📉🔔🔕📌×]/g, '').trim());
        expect(names).toEqual(['A', 'Z']);
    });

    it('resets missing filters', async () => {
        const { input, onLoad } = await setup([testConfigs.r], { currentFilters: { ...mockFilters, days_old: 7 } }, isLoadedRef);
        fireEvent.focus(input);
        fireEvent.click(await screen.findByText('R'));
        expect(onLoad).toHaveBeenCalledWith(expect.objectContaining({ search: 'S', days_old: undefined }), 'R');
    });

    it.each([['Confirms', true], ['Cancels', false]])('handles delete when user %s', async (_, confirm) => {
        const { input } = await setup([testConfigs.del], {}, isLoadedRef);
        fireEvent.focus(input);
        const deleteBtn = (await screen.findByText('Del')).closest('li')?.querySelector('.config-delete-btn');
        fireEvent.click(deleteBtn!);
        await screen.findByText(/Delete configuration "Del"\?/i);
        fireEvent.click(screen.getByText(confirm ? 'Confirm' : 'Cancel', { selector: 'button.modal-button' }));
        await waitFor(() => {
            const stored = JSON.parse(localStorage.getItem('filter_configurations') || '[]');
            if (confirm) expect(stored.some((c: any) => c.name === 'Del')).toBe(false);
            else expect(stored[0].name).toBe('Del');
        });
    });

    it('resets input name if deleted configuration was active', async () => {
        const { input } = await setup([testConfigs.active], {}, isLoadedRef);
        fireEvent.focus(input);
        fireEvent.click(await screen.findByText('Active'));
        expect(input.value).toBe('Active');
        fireEvent.focus(input);
        const deleteBtn = (await screen.findByText('Active')).closest('li')?.querySelector('.config-delete-btn');
        fireEvent.click(deleteBtn!);
        fireEvent.click(screen.getByText('Confirm', { selector: 'button.modal-button' }));
        await waitFor(() => expect(input.value).toBe(''));
    });

    it('keeps pinned configurations visible even when filter does not match', async () => {
        const { input } = await setup([testConfigs.pinnedJava], {}, isLoadedRef);
        fireEvent.focus(input);
        expect(screen.getByText('PinnedJava', { selector: '.pinned-config-name' })).toBeInTheDocument();
        fireEvent.change(input, { target: { value: 'Python' } });
        await waitFor(() => expect(screen.getByText('PinnedJava', { selector: '.pinned-config-name' })).toBeInTheDocument());
        expect(screen.queryByText('PinnedJava', { selector: '.config-name' })).not.toBeInTheDocument();
    });

    it.each([
        { regex: "initi8|primeit|Acid tango|Kairos", expectExpand: true, expectSelection: true },
        { regex: null, expectExpand: false, expectSelection: false },
    ])('By company config handles rlike pattern: $regex', async ({ regex, expectExpand, expectSelection }) => {
        const config = regex ? byCompanyConfigs.withRlike(regex) : byCompanyConfigs.withoutRlike;
        const onToggleExpand = vi.fn();
        const { input } = await setup([config], { onToggleExpand, isExpanded: false }, isLoadedRef);
        const sqlInput = document.createElement('input');
        sqlInput.id = 'filter-sql';
        sqlInput.value = config.filters.sql_filter!;
        document.body.appendChild(sqlInput);
        try {
            fireEvent.focus(input);
            fireEvent.click(await screen.findByText('By company'));
            if (expectExpand) expect(onToggleExpand).toHaveBeenCalled();
            await waitFor(() => expect(document.getElementById('filter-sql')).toHaveFocus());
            if (expectSelection) {
                const selectedText = sqlInput.value.substring(sqlInput.selectionStart || 0, sqlInput.selectionEnd || 0);
                expect(selectedText).toBe(regex);
            } else {
                expect(sqlInput.selectionStart).toBe(sqlInput.selectionEnd);
            }
        } finally { document.body.removeChild(sqlInput); }
    });
});
