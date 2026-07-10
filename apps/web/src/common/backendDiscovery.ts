import net from 'net';
import http from 'http';
import fs from 'fs';

const BACKEND_PORT = 8000;
const SCAN_TIMEOUT_MS = 200;
const PROBE_TIMEOUT_MS = 1000;
const MAX_WORKERS = 100;

function detectLocalSubnets(): string[] {
  const subnets: string[] = [];
  const s = net.createConnection({ host: '8.8.8.8', port: 80, timeout: 2000 });
  try {
    const localAddr = s.localAddress;
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
    subnets.push('192.168.1.0/24', '192.168.0.0/24');
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

function probeBackend(url: string): Promise<boolean> {
  return new Promise((resolve) => {
    const req = http.get(url, { timeout: PROBE_TIMEOUT_MS }, (res) => {
      res.resume();
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => { req.destroy(); resolve(false); });
  });
}

export async function discoverBackendUrl(env?: Record<string, string>): Promise<string> {
  const isDocker = fs.existsSync('/workspace/.env');
  if (isDocker) {
    if (await probeBackend(`http://backend:${BACKEND_PORT}/health`)) {
      console.log('[backendDiscovery] Docker detected, backend reachable at http://backend:8000');
      return `http://backend:${BACKEND_PORT}`;
    }
    console.log('[backendDiscovery] Docker detected but backend unreachable, scanning... (set BACKEND_DISCOVERY=False to skip)');
  }

  const backendDiscovery = env?.BACKEND_DISCOVERY ?? process.env.BACKEND_DISCOVERY;
  const discoveryEnabled = backendDiscovery === 'True' || backendDiscovery === 'true';
  if (!discoveryEnabled) {
    console.log('[backendDiscovery] Discovery disabled, using http://localhost:8000');
    return 'http://localhost:8000';
  }

  if (await probeBackend(`http://localhost:${BACKEND_PORT}/health`)) {
    console.log(`[backendDiscovery] Backend found at localhost:${BACKEND_PORT}`);
    return `http://localhost:${BACKEND_PORT}`;
  }

  console.log('[backendDiscovery] Localhost failed, scanning LAN...');
  const subnets = detectLocalSubnets();
  console.log(`[backendDiscovery] Scanning subnets: ${subnets.join(', ')}`);

  const hosts = subnets.flatMap(cidrToHosts);
  console.log(`[backendDiscovery] Scanning ${hosts.length} hosts for port ${BACKEND_PORT}...`);

  const openHosts: string[] = [];
  for (let i = 0; i < hosts.length; i += MAX_WORKERS) {
    const batch = hosts.slice(i, i + MAX_WORKERS);
    const results = await Promise.all(batch.map((ip) => scanPort(ip, BACKEND_PORT, SCAN_TIMEOUT_MS)));
    batch.forEach((ip, idx) => { if (results[idx]) openHosts.push(ip); });
  }

  console.log(`[backendDiscovery] Found ${openHosts.length} hosts with port ${BACKEND_PORT} open`);

  for (const ip of openHosts) {
    const url = `http://${ip}:${BACKEND_PORT}`;
    if (await probeBackend(`${url}/health`)) {
      console.log(`[backendDiscovery] Backend found at ${url}`);
      return url;
    }
  }

  console.log('[backendDiscovery] No backend found, falling back to localhost');
  return `http://localhost:${BACKEND_PORT}`;
}
