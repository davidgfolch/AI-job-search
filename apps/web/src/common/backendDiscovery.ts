import net from 'net';
import http from 'http';
import fs from 'fs';

export const BACKEND_PORT = 8000;
export const DEFAULT_WAIT_TIMEOUT_SECONDS = 120;
export const DEFAULT_CHECK_INTERVAL_SECONDS = 10;
export const DEFAULT_MAX_RETRIES = 3;

const SCAN_TIMEOUT_MS = 200;
const PROBE_TIMEOUT_MS = 1000;
const MAX_WORKERS = 100;
const DEFAULT_SUBNETS = ['192.168.1.0/24', '192.168.0.0/24'];

export type BackendEnv = Record<string, string | undefined>;

export interface BackendSettings {
  /** Port the backend API listens on. */
  port: number;
  /** How long the web waits for the backend to answer at startup. */
  waitTimeoutMs: number;
  /** How often the watchdog probes the current backend target. */
  checkIntervalMs: number;
  /** Consecutive failed probes before the target is resolved again. */
  maxRetries: number;
}

function toInt(value: string | undefined, fallback: number, min = 1): number {
  const parsed = Number.parseInt(value ?? '', 10);
  return Number.isFinite(parsed) && parsed >= min ? parsed : fallback;
}

export function backendSettings(env: BackendEnv = {}): BackendSettings {
  return {
    port: toInt(env.BACKEND_PORT, BACKEND_PORT),
    waitTimeoutMs: toInt(env.BACKEND_WAIT_TIMEOUT_SECONDS, DEFAULT_WAIT_TIMEOUT_SECONDS, 0) * 1000,
    checkIntervalMs: toInt(env.BACKEND_CHECK_INTERVAL_SECONDS, DEFAULT_CHECK_INTERVAL_SECONDS) * 1000,
    maxRetries: toInt(env.BACKEND_MAX_RETRIES, DEFAULT_MAX_RETRIES),
  };
}

/** True when the web runs inside the Docker image (the workspace env file is mounted there). */
export function isDockerEnvironment(): boolean {
  return fs.existsSync('/workspace/.env');
}

/**
 * Ordered candidates for the backend API, covering every web/backend topology:
 * web in Docker or on the host, backend in Docker or on the host.
 */
export function backendUrlCandidates(isDocker: boolean, env: BackendEnv = {}, port = BACKEND_PORT): string[] {
  const configured = env.BACKEND_URL?.trim();
  if (configured) return [configured];
  const dockerUrl = `http://backend:${port}`;
  const hostUrl = `http://host.docker.internal:${port}`;
  const localUrl = `http://localhost:${port}`;
  return isDocker ? [dockerUrl, hostUrl, localUrl] : [localUrl, hostUrl, dockerUrl];
}

/** The LAN scan is the last resort, used when no direct candidate answers. */
export function lanScanEnabled(env: BackendEnv = {}): boolean {
  const value = (env.BACKEND_DISCOVERY ?? '').trim().toLowerCase();
  return value === 'true' || value === '1' || value === 'yes';
}

function detectLocalSubnets(): string[] {
  const subnets: string[] = [];
  const s = net.createConnection({ host: '8.8.8.8', port: 80, timeout: 2000 });
  try {
    const localAddr = s.localAddress;
    if (!localAddr) {
      subnets.push(...DEFAULT_SUBNETS);
      return subnets;
    }
    const parts = localAddr.split('.');
    subnets.push(`${parts[0]}.${parts[1]}.${parts[2]}.0/24`);
    const third = parseInt(parts[2]);
    for (const offset of [-1, 1]) {
      const adj = third + offset;
      if (adj >= 0 && adj <= 255) {
        subnets.push(`${parts[0]}.${parts[1]}.${adj}.0/24`);
      }
    }
  } catch {
    subnets.push(...DEFAULT_SUBNETS);
  } finally {
    s.destroy();
  }
  return subnets;
}

function cidrToHosts(cidr: string): string[] {
  const [base, bits] = cidr.split('/');
  const prefixLen = parseInt(bits);
  if (prefixLen < 24) return [];
  const parts = base.split('.').map(Number);
  const hosts: string[] = [];
  const hostCount = Math.pow(2, 32 - prefixLen);
  const baseInt = (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3];
  for (let i = 1; i < hostCount - 1; i++) {
    const ipInt = baseInt + i;
    hosts.push(`${(ipInt >> 24) & 0xff}.${(ipInt >> 16) & 0xff}.${(ipInt >> 8) & 0xff}.${ipInt & 0xff}`);
  }
  return hosts;
}

function scanPort(ip: string, port: number, timeout: number): Promise<boolean> {
  return new Promise((resolve) => {
    const s = new net.Socket();
    s.setTimeout(timeout);
    s.once('connect', () => { s.destroy(); resolve(true); });
    s.once('timeout', () => { s.destroy(); resolve(false); });
    s.once('error', () => { s.destroy(); resolve(false); });
    s.connect(port, ip);
  });
}

/** Probes an absolute URL and resolves true only on a 200 answer. */
export function probeBackend(url: string): Promise<boolean> {
  return new Promise((resolve) => {
    const req = http.get(url, { timeout: PROBE_TIMEOUT_MS }, (res) => {
      res.resume();
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => { req.destroy(); resolve(false); });
  });
}

/** Returns the LAN hosts that answer on the backend port. */
export async function scanLanForBackend(port = BACKEND_PORT, log: (message: string) => void = console.log): Promise<string[]> {
  const subnets = detectLocalSubnets();
  log(`[backendDiscovery] Scanning subnets: ${subnets.join(', ')}`);
  const hosts = subnets.flatMap(cidrToHosts);
  log(`[backendDiscovery] Scanning ${hosts.length} hosts for port ${port}...`);
  const openHosts: string[] = [];
  for (let i = 0; i < hosts.length; i += MAX_WORKERS) {
    const batch = hosts.slice(i, i + MAX_WORKERS);
    const results = await Promise.all(batch.map((ip) => scanPort(ip, port, SCAN_TIMEOUT_MS)));
    batch.forEach((ip, idx) => { if (results[idx]) openHosts.push(ip); });
  }
  log(`[backendDiscovery] Found ${openHosts.length} hosts with port ${port} open`);
  return openHosts;
}
