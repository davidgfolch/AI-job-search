import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { BackendWatchdog } from '../backendWatchdog';

describe('BackendWatchdog', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('does nothing while the backend answers', async () => {
    const onChange = vi.fn();
    const reconnect = vi.fn(async () => null);
    const watchdog = new BackendWatchdog({ check: async () => true, reconnect, current: () => 'http://backend:8000', onChange });
    watchdog.start();
    await vi.advanceTimersByTimeAsync(3000);
    expect(onChange).not.toHaveBeenCalled();
    expect(reconnect).not.toHaveBeenCalled();
    expect(watchdog.failureCount).toBe(0);
  });

  it('reconnects and reports the new target after N failures', async () => {
    const onChange = vi.fn();
    const reconnect = vi.fn(async () => 'http://backend:8000');
    const watchdog = new BackendWatchdog({ check: async () => false, reconnect, current: () => 'http://localhost:8000', onChange, checkIntervalMs: 1000, maxFailures: 2 });
    watchdog.start();
    await vi.advanceTimersByTimeAsync(1000);
    expect(onChange).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(1000);
    expect(reconnect).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith('http://backend:8000');
  });

  it('keeps the current target when nothing answers', async () => {
    const onChange = vi.fn();
    const reconnect = vi.fn(async () => null);
    const watchdog = new BackendWatchdog({ check: async () => false, reconnect, current: () => 'http://backend:8000', onChange, checkIntervalMs: 1000, maxFailures: 1 });
    watchdog.start();
    await vi.advanceTimersByTimeAsync(1000);
    expect(onChange).not.toHaveBeenCalled();
    expect(watchdog.failureCount).toBe(0);
  });

  it('keeps the current target when the backend did not move', async () => {
    const onChange = vi.fn();
    const reconnect = vi.fn(async () => 'http://backend:8000');
    const watchdog = new BackendWatchdog({ check: async () => false, reconnect, current: () => 'http://backend:8000', onChange, checkIntervalMs: 1000, maxFailures: 1 });
    watchdog.start();
    await vi.advanceTimersByTimeAsync(1000);
    expect(onChange).not.toHaveBeenCalled();
  });

  it('resets the failure counter when the backend answers again', async () => {
    let healthy = false;
    const reconnect = vi.fn(async () => null);
    const watchdog = new BackendWatchdog({ check: async () => healthy, reconnect, current: () => 'http://backend:8000', onChange: vi.fn(), checkIntervalMs: 1000, maxFailures: 3 });
    watchdog.start();
    await vi.advanceTimersByTimeAsync(2000);
    expect(watchdog.failureCount).toBe(2);
    healthy = true;
    await vi.advanceTimersByTimeAsync(1000);
    expect(watchdog.failureCount).toBe(0);
    await vi.advanceTimersByTimeAsync(2000);
    expect(reconnect).not.toHaveBeenCalled();
  });

  it('stops probing after stop()', async () => {
    const check = vi.fn(async () => true);
    const watchdog = new BackendWatchdog({ check, reconnect: async () => null, current: () => 'http://backend:8000', onChange: vi.fn(), checkIntervalMs: 1000 });
    watchdog.start();
    expect(watchdog.running).toBe(true);
    await vi.advanceTimersByTimeAsync(1000);
    watchdog.stop();
    expect(watchdog.running).toBe(false);
    await vi.advanceTimersByTimeAsync(3000);
    expect(check).toHaveBeenCalledTimes(1);
  });

  it('logs a failing check instead of throwing', async () => {
    const log = vi.fn();
    const watchdog = new BackendWatchdog({ check: async () => { throw new Error('boom'); }, reconnect: async () => null, current: () => 'http://backend:8000', onChange: vi.fn(), checkIntervalMs: 1000, log });
    watchdog.start();
    await vi.advanceTimersByTimeAsync(1000);
    expect(log).toHaveBeenCalledWith('[backendWatchdog] Backend check failed: boom');
  });
});
