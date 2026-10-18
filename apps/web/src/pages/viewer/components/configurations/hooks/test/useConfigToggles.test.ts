import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useConfigToggles } from '../useConfigToggles';
import type { FilterConfig } from '../useFilterConfigurations';
import type { FilterConfigService } from '../../../hooks/FilterConfigService';

const makeService = () => ({
    updateStatistics: vi.fn().mockResolvedValue(undefined),
    updatePinned: vi.fn().mockResolvedValue(undefined),
    save: vi.fn().mockResolvedValue(undefined),
});

const withId: FilterConfig = { id: 1, name: 'A', filters: {} as FilterConfig['filters'], watched: false, statistics: false, pinned: false };

describe('useConfigToggles', () => {
    let service: ReturnType<typeof makeService>;
    let setSavedConfigs: ReturnType<typeof vi.fn>;
    let notify: ReturnType<typeof vi.fn>;
    const setup = (configs: FilterConfig[]) => renderHook(() => useConfigToggles({
        savedConfigs: configs, setSavedConfigs: setSavedConfigs as never, service: service as unknown as FilterConfigService, notify
    }));

    beforeEach(() => {
        service = makeService();
        setSavedConfigs = vi.fn();
        notify = vi.fn();
    });

    it('flips statistics and calls updateStatistics when the config has an id', async () => {
        const { result } = setup([{ ...withId, statistics: false }]);
        await act(async () => { await result.current.toggleStatistics('A'); });
        expect(service.updateStatistics).toHaveBeenCalledWith(1, true);
        expect(setSavedConfigs).toHaveBeenCalledWith([expect.objectContaining({ statistics: true })]);
    });

    it('flips pin and calls updatePinned', async () => {
        const { result } = setup([{ ...withId, pinned: true }]);
        await act(async () => { await result.current.togglePin('A'); });
        expect(service.updatePinned).toHaveBeenCalledWith(1, false);
        expect(setSavedConfigs).toHaveBeenCalledWith([expect.objectContaining({ pinned: false })]);
    });

    it('falls back to service.save when the config has no id', async () => {
        const { result } = setup([{ name: 'Local', filters: {} as FilterConfig['filters'], statistics: false }]);
        await act(async () => { await result.current.toggleStatistics('Local'); });
        expect(service.updateStatistics).not.toHaveBeenCalled();
        expect(service.save).toHaveBeenCalledWith([expect.objectContaining({ statistics: true })]);
    });

    it('is a no-op when the config name is unknown', async () => {
        const { result } = setup([{ ...withId }]);
        await act(async () => { await result.current.toggleStatistics('missing'); });
        expect(service.updateStatistics).not.toHaveBeenCalled();
        expect(setSavedConfigs).not.toHaveBeenCalled();
    });

    it('notifies and reverts the optimistic update when the service call fails', async () => {
        service.updateStatistics.mockRejectedValueOnce(new Error('boom'));
        const { result } = setup([{ ...withId, statistics: false }]);
        await act(async () => { await result.current.toggleStatistics('A'); });
        expect(notify).toHaveBeenCalledWith('Failed to update statistics setting', 'error');
        expect(setSavedConfigs).toHaveBeenLastCalledWith([expect.objectContaining({ statistics: false })]);
    });

    it('persists a watch toggle via service.save and updates state on success', async () => {
        const { result } = setup([{ ...withId, watched: false }]);
        act(() => { result.current.toggleWatch('A'); });
        await waitFor(() => expect(service.save).toHaveBeenCalledWith([expect.objectContaining({ watched: true })]));
        expect(setSavedConfigs).toHaveBeenCalledWith([expect.objectContaining({ watched: true })]);
    });

    it('notifies when the watch save fails', async () => {
        service.save.mockRejectedValueOnce(new Error('boom'));
        const { result } = setup([{ ...withId, watched: false }]);
        act(() => { result.current.toggleWatch('A'); });
        await waitFor(() => expect(notify).toHaveBeenCalledWith('Failed to update watch setting', 'error'));
    });

    it('is a no-op for an unknown watch name', async () => {
        const { result } = setup([{ ...withId }]);
        act(() => { result.current.toggleWatch('missing'); });
        await waitFor(() => expect(service.save).not.toHaveBeenCalled());
        expect(setSavedConfigs).not.toHaveBeenCalled();
    });
});
