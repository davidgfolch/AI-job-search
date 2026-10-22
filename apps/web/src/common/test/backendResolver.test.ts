import { describe, it, expect, vi } from 'vitest';
import { BackendResolver } from '../backendResolver';

function createClock() {
  let time = 0;
  return { now: () => time, sleep: async (ms: number) => { time += ms; } };
}

describe('BackendResolver', () => {
  it('targets the docker service name by default inside docker', () => {
    const resolver = new BackendResolver({ isDocker: true, env: {} });
    expect(resolver.target).toBe('http://backend:8000');
  });

  it('targets localhost by default on the host', () => {
    const resolver = new BackendResolver({ isDocker: false, env: {} });
    expect(resolver.target).toBe('http://localhost:8000');
  });

  it('returns the candidate that answers', async () => {
    const probe = vi.fn(async (url: string) => url === 'http://host.docker.internal:8000/health');
    const resolver = new BackendResolver({ isDocker: true, env: {}, probe });
    expect(await resolver.resolve()).toBe('http://host.docker.internal:8000');
    expect(resolver.target).toBe('http://host.docker.internal:8000');
  });

  it('probes every candidate in order', async () => {
    const probe = vi.fn(async (_url: string) => false);
    const resolver = new BackendResolver({ isDocker: true, env: {}, probe, scanLan: async () => [] });
    await resolver.resolveOnce();
    expect(probe.mock.calls.map((call) => call[0])).toEqual([
      'http://backend:8000/health',
      'http://host.docker.internal:8000/health',
      'http://localhost:8000/health',
    ]);
  });

  it('keeps waiting until the backend answers', async () => {
    const clock = createClock();
    let rounds = 0;
    const probe = vi.fn(async (url: string) => {
      if (url !== 'http://backend:8000/health') return false;
      rounds += 1;
      return rounds >= 3;
    });
    const resolver = new BackendResolver({ isDocker: true, env: {}, probe, sleep: clock.sleep, now: clock.now, settings: { waitTimeoutMs: 60000 } });
    expect(await resolver.resolve()).toBe('http://backend:8000');
    expect(rounds).toBe(3);
  });

  it('never falls back to localhost inside docker when the backend stays down', async () => {
    const clock = createClock();
    const resolver = new BackendResolver({ isDocker: true, env: {}, probe: async () => false, sleep: clock.sleep, now: clock.now, settings: { waitTimeoutMs: 1000 } });
    expect(await resolver.resolve()).toBe('http://backend:8000');
    expect(resolver.target).toBe('http://backend:8000');
  });

  it('stops waiting when the timeout expires', async () => {
    const clock = createClock();
    const probe = vi.fn(async (_url: string) => false);
    const resolver = new BackendResolver({ isDocker: false, env: {}, probe, sleep: clock.sleep, now: clock.now, settings: { waitTimeoutMs: 1000 } });
    expect(await resolver.resolve()).toBe('http://localhost:8000');
    expect(probe.mock.calls.filter((call) => call[0] === 'http://localhost:8000/health')).toHaveLength(2);
  });

  it('scans the LAN as a last resort when discovery is enabled', async () => {
    const probe = vi.fn(async (url: string) => url === 'http://192.168.1.77:8000/health');
    const scanLan = vi.fn(async () => ['192.168.1.77']);
    const resolver = new BackendResolver({ isDocker: false, env: { BACKEND_DISCOVERY: 'True' }, probe, scanLan });
    expect(await resolver.resolveOnce()).toBe('http://192.168.1.77:8000');
    expect(scanLan).toHaveBeenCalled();
  });

  it('does not scan the LAN when discovery is disabled', async () => {
    const scanLan = vi.fn(async () => ['192.168.1.77']);
    const resolver = new BackendResolver({ isDocker: false, env: { BACKEND_DISCOVERY: 'False' }, probe: async () => false, scanLan });
    expect(await resolver.resolveOnce()).toBeNull();
    expect(scanLan).not.toHaveBeenCalled();
  });

  it('checks the current target', async () => {
    const probe = vi.fn(async () => true);
    const resolver = new BackendResolver({ isDocker: true, env: {}, probe });
    expect(await resolver.isReachable()).toBe(true);
    expect(probe).toHaveBeenCalledWith('http://backend:8000/health');
  });

  it('reconnects to a backend that moved', async () => {
    const probe = vi.fn(async (url: string) => url === 'http://host.docker.internal:8000/health');
    const resolver = new BackendResolver({ isDocker: true, env: {}, probe });
    expect(await resolver.reconnect()).toBe('http://host.docker.internal:8000');
    expect(resolver.target).toBe('http://host.docker.internal:8000');
  });

  it('returns null when reconnecting finds nothing', async () => {
    const resolver = new BackendResolver({ isDocker: true, env: {}, probe: async () => false });
    expect(await resolver.reconnect()).toBeNull();
    expect(resolver.target).toBe('http://backend:8000');
  });

  it('exposes the effective settings', () => {
    const resolver = new BackendResolver({ isDocker: true, env: { BACKEND_CHECK_INTERVAL_SECONDS: '4', BACKEND_MAX_RETRIES: '2' } });
    expect(resolver.config.checkIntervalMs).toBe(4000);
    expect(resolver.config.maxRetries).toBe(2);
  });
});
