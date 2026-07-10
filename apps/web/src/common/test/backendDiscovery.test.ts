import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { discoverBackendUrl } from '../backendDiscovery';
import { EventEmitter } from 'events';

vi.mock('fs', () => ({ default: { existsSync: vi.fn() } }));
vi.mock('http', () => ({ default: { get: vi.fn() } }));

function createMockSocket(overrides?: { connectError?: boolean; timeoutError?: boolean }) {
  const socket = new EventEmitter() as any;
  socket.setTimeout = vi.fn();
  socket.connect = vi.fn(() => {
    if (overrides?.connectError) setTimeout(() => socket.emit('error', new Error('refused')), 0);
    else if (overrides?.timeoutError) setTimeout(() => socket.emit('timeout'), 0);
    else setTimeout(() => socket.emit('connect'), 0);
  });
  socket.destroy = vi.fn();
  socket.localAddress = '192.168.1.50';
  return socket;
}

let socketFactory: () => any = () => createMockSocket();

vi.mock('net', () => ({
  default: {
    createConnection: vi.fn(),
    Socket: vi.fn().mockImplementation(function () { return socketFactory(); }),
  },
}));

function mockHttpGet(statusCode: number, shouldError = false) {
  const req = new EventEmitter() as any;
  req.destroy = vi.fn();
  const res = new EventEmitter() as any;
  res.statusCode = statusCode;
  res.resume = vi.fn();
  (http.get as any).mockImplementation((_url: string, _opts: any, cb: any) => {
    if (shouldError) setTimeout(() => req.emit('error', new Error('fail')), 0);
    else setTimeout(() => cb(res), 0);
    return req;
  });
}

import fs from 'fs';
import net from 'net';
import http from 'http';

describe('discoverBackendUrl', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    socketFactory = () => createMockSocket();
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns Docker URL when /workspace/.env exists and backend is reachable', async () => {
    (fs.existsSync as any).mockReturnValue(true);
    mockHttpGet(200);
    const result = await discoverBackendUrl();
    expect(result).toBe('http://backend:8000');
  });

  it('falls back from Docker when backend is unreachable', async () => {
    (fs.existsSync as any).mockReturnValue(true);
    mockHttpGet(0, true);
    const result = await discoverBackendUrl();
    expect(result).toBe('http://localhost:8000');
  });

  it('returns localhost when discovery is disabled', async () => {
    (fs.existsSync as any).mockReturnValue(false);
    const result = await discoverBackendUrl({});
    expect(result).toBe('http://localhost:8000');
  });

  it('returns localhost when discovery is explicitly False', async () => {
    (fs.existsSync as any).mockReturnValue(false);
    const result = await discoverBackendUrl({ BACKEND_DISCOVERY: 'False' });
    expect(result).toBe('http://localhost:8000');
  });

  it('returns localhost when backend responds on localhost', async () => {
    (fs.existsSync as any).mockReturnValue(false);
    mockHttpGet(200);
    const result = await discoverBackendUrl({ BACKEND_DISCOVERY: 'True' });
    expect(result).toBe('http://localhost:8000');
  });

  it('scans LAN when localhost probe fails', async () => {
    (fs.existsSync as any).mockReturnValue(false);
    mockHttpGet(0, true);
    (net.createConnection as any).mockReturnValue(createMockSocket());
    socketFactory = () => createMockSocket();
    let httpCall = 0;
    (http.get as any).mockImplementation((_url: string, _opts: any, cb: any) => {
      const req = new EventEmitter() as any;
      req.destroy = vi.fn();
      const res = new EventEmitter() as any;
      res.statusCode = httpCall === 0 ? 0 : 200;
      res.resume = vi.fn();
      httpCall++;
      if (httpCall === 1) setTimeout(() => req.emit('error', new Error('fail')), 0);
      else setTimeout(() => cb(res), 0);
      return req;
    });
    const result = await discoverBackendUrl({ BACKEND_DISCOVERY: 'True' });
    expect(result).toContain(':8000');
  });

  it('falls back to localhost when nothing found in LAN', async () => {
    (fs.existsSync as any).mockReturnValue(false);
    mockHttpGet(0, true);
    (net.createConnection as any).mockReturnValue(createMockSocket());
    socketFactory = () => createMockSocket({ connectError: true });
    const result = await discoverBackendUrl({ BACKEND_DISCOVERY: 'True' });
    expect(result).toBe('http://localhost:8000');
  });

  it('accepts lowercase true for BACKEND_DISCOVERY', async () => {
    (fs.existsSync as any).mockReturnValue(false);
    mockHttpGet(200);
    const result = await discoverBackendUrl({ BACKEND_DISCOVERY: 'true' });
    expect(result).toBe('http://localhost:8000');
  });
});
