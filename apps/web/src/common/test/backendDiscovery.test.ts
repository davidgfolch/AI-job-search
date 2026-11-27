import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest';
import { backendSettings, backendUrlCandidates, isDockerEnvironment, lanScanEnabled, probeBackend, scanLanForBackend } from '../backendDiscovery';
import { EventEmitter } from 'events';
import type { ClientRequest, IncomingMessage } from 'http';

vi.mock('fs', () => ({ default: { existsSync: vi.fn() } }));
vi.mock('http', () => ({ default: { get: vi.fn() } }));

function createMockSocket(overrides?: { connectError?: boolean; timeoutError?: boolean }) {
  const socket = Object.assign(new EventEmitter(), {
    setTimeout: vi.fn(),
    connect: vi.fn(),
    destroy: vi.fn(),
    localAddress: '192.168.1.50',
  });
  socket.connect.mockImplementation(() => {
    if (overrides?.connectError) setTimeout(() => socket.emit('error', new Error('refused')), 0);
    else if (overrides?.timeoutError) setTimeout(() => socket.emit('timeout'), 0);
    else setTimeout(() => socket.emit('connect'), 0);
  });
  return socket;
}

type MockSocket = ReturnType<typeof createMockSocket>;
let socketFactory: () => MockSocket = () => createMockSocket();

vi.mock('net', () => ({
  default: {
    createConnection: vi.fn(),
    Socket: vi.fn().mockImplementation(function () { return socketFactory(); }),
  },
}));

function mockHttpGet(statusCode: number, shouldError = false) {
  const req = Object.assign(new EventEmitter(), { destroy: vi.fn() });
  const res = Object.assign(new EventEmitter(), { statusCode, resume: vi.fn() });
  (vi.mocked(http.get) as Mock).mockImplementation((_url: string, _opts: unknown, cb: (res: IncomingMessage) => void) => {
    if (shouldError) setTimeout(() => req.emit('error', new Error('fail')), 0);
    else setTimeout(() => cb(res as unknown as IncomingMessage), 0);
    return req as unknown as ClientRequest;
  });
}

import fs from 'fs';
import net from 'net';
import http from 'http';

describe('backendSettings', () => {
  it('returns the defaults when nothing is configured', () => {
    expect(backendSettings({})).toEqual({ port: 8000, waitTimeoutMs: 120000, checkIntervalMs: 10000, maxRetries: 3 });
  });

  it('reads the environment overrides', () => {
    const settings = backendSettings({ BACKEND_PORT: '9000', BACKEND_WAIT_TIMEOUT_SECONDS: '5', BACKEND_CHECK_INTERVAL_SECONDS: '2', BACKEND_MAX_RETRIES: '7' });
    expect(settings).toEqual({ port: 9000, waitTimeoutMs: 5000, checkIntervalMs: 2000, maxRetries: 7 });
  });

  it('ignores invalid values', () => {
    const settings = backendSettings({ BACKEND_PORT: 'abc', BACKEND_MAX_RETRIES: '-1', BACKEND_CHECK_INTERVAL_SECONDS: 'x' });
    expect(settings).toEqual({ port: 8000, waitTimeoutMs: 120000, checkIntervalMs: 10000, maxRetries: 3 });
  });

  it('allows disabling the startup wait', () => {
    expect(backendSettings({ BACKEND_WAIT_TIMEOUT_SECONDS: '0' }).waitTimeoutMs).toBe(0);
  });
});

describe('backendUrlCandidates', () => {
  it('prefers the docker service name inside docker', () => {
    expect(backendUrlCandidates(true)).toEqual(['http://backend:8000', 'http://host.docker.internal:8000', 'http://localhost:8000']);
  });

  it('prefers localhost on the host', () => {
    expect(backendUrlCandidates(false)).toEqual(['http://localhost:8000', 'http://host.docker.internal:8000', 'http://backend:8000']);
  });

  it('honours an explicit BACKEND_URL', () => {
    expect(backendUrlCandidates(true, { BACKEND_URL: 'http://my-backend:9999' })).toEqual(['http://my-backend:9999']);
  });

  it('honours the configured port', () => {
    expect(backendUrlCandidates(true, {}, 9000)[0]).toBe('http://backend:9000');
  });
});

describe('lanScanEnabled', () => {
  it.each(['True', 'true', '1', 'yes'])('is enabled for %s', (value) => {
    expect(lanScanEnabled({ BACKEND_DISCOVERY: value })).toBe(true);
  });

  it.each([undefined, 'False', 'false', '0', 'no'])('is disabled for %s', (value) => {
    expect(lanScanEnabled({ BACKEND_DISCOVERY: value })).toBe(false);
  });
});

describe('isDockerEnvironment', () => {
  it('detects the docker workspace mount', () => {
    vi.mocked(fs.existsSync).mockReturnValue(true);
    expect(isDockerEnvironment()).toBe(true);
  });

  it('reports false outside docker', () => {
    vi.mocked(fs.existsSync).mockReturnValue(false);
    expect(isDockerEnvironment()).toBe(false);
  });
});

describe('probeBackend', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('resolves true on a 200 answer', async () => {
    mockHttpGet(200);
    expect(await probeBackend('http://backend:8000/health')).toBe(true);
  });

  it('resolves false on a non 200 answer', async () => {
    mockHttpGet(500);
    expect(await probeBackend('http://backend:8000/health')).toBe(false);
  });

  it('resolves false when the connection fails', async () => {
    mockHttpGet(0, true);
    expect(await probeBackend('http://backend:8000/health')).toBe(false);
  });

  it('resolves false when the request times out', async () => {
    const req = Object.assign(new EventEmitter(), { destroy: vi.fn() });
    (vi.mocked(http.get) as Mock).mockImplementation(() => {
      setTimeout(() => req.emit('timeout'), 0);
      return req as unknown as ClientRequest;
    });
    expect(await probeBackend('http://backend:8000/health')).toBe(false);
    expect(req.destroy).toHaveBeenCalled();
  });
});

describe('scanLanForBackend', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    socketFactory = () => createMockSocket();
    (vi.mocked(net.createConnection) as Mock).mockReturnValue(createMockSocket());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns the hosts that answer on the backend port', async () => {
    const log = vi.fn();
    const hosts = await scanLanForBackend(8000, log);
    expect(hosts.length).toBeGreaterThan(0);
    expect(hosts.every((host) => /^\d+\.\d+\.\d+\.\d+$/.test(host))).toBe(true);
  });

  it('returns no host when every connection is refused', async () => {
    socketFactory = () => createMockSocket({ connectError: true });
    const hosts = await scanLanForBackend(8000, vi.fn());
    expect(hosts).toEqual([]);
  });

  it('returns no host when the connections time out', async () => {
    socketFactory = () => createMockSocket({ timeoutError: true });
    const hosts = await scanLanForBackend(8000, vi.fn());
    expect(hosts).toEqual([]);
  });
});
