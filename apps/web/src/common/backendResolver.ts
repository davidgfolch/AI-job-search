import { backendSettings, backendUrlCandidates, isDockerEnvironment, lanScanEnabled, probeBackend, scanLanForBackend } from './backendDiscovery.ts';
import type { BackendEnv, BackendSettings } from './backendDiscovery.ts';

const RETRY_INTERVAL_MS = 2000;
const RETRY_LOG_INTERVAL_MS = 5000;

export interface BackendResolverOptions {
  env?: BackendEnv;
  isDocker?: boolean;
  settings?: Partial<BackendSettings>;
  probe?: (url: string) => Promise<boolean>;
  scanLan?: () => Promise<string[]>;
  sleep?: (ms: number) => Promise<void>;
  now?: () => number;
  log?: (message: string) => void;
}

/**
 * Finds the backend API and keeps track of the target the web proxies to.
 * It waits (bounded) for the backend at startup and can re-resolve it later on.
 */
export class BackendResolver {
  private readonly env: BackendEnv;
  private readonly isDocker: boolean;
  private readonly settings: BackendSettings;
  private readonly probe: (url: string) => Promise<boolean>;
  private readonly scanLan: () => Promise<string[]>;
  private readonly sleep: (ms: number) => Promise<void>;
  private readonly now: () => number;
  private readonly log: (message: string) => void;
  private currentUrl: string;

  constructor(options: BackendResolverOptions = {}) {
    this.env = options.env ?? {};
    this.isDocker = options.isDocker ?? isDockerEnvironment();
    this.settings = { ...backendSettings(this.env), ...options.settings };
    this.probe = options.probe ?? probeBackend;
    this.scanLan = options.scanLan ?? (() => scanLanForBackend(this.settings.port, this.log));
    this.sleep = options.sleep ?? ((ms: number) => new Promise((resolve) => setTimeout(resolve, ms)));
    this.now = options.now ?? (() => Date.now());
    this.log = options.log ?? ((message: string) => console.log(message));
    this.currentUrl = backendUrlCandidates(this.isDocker, this.env, this.settings.port)[0];
  }

  /** The URL the web currently proxies to. */
  get target(): string {
    return this.currentUrl;
  }

  /** The effective backend settings (ports, timeouts, retries). */
  get config(): BackendSettings {
    return this.settings;
  }

  /** True when the current target answers on /health. */
  async isReachable(): Promise<boolean> {
    return this.probe(`${this.currentUrl}/health`);
  }

  /** Single pass over the candidate chain (plus the LAN as a last resort). */
  async resolveOnce(): Promise<string | null> {
    for (const candidate of backendUrlCandidates(this.isDocker, this.env, this.settings.port)) {
      if (await this.probe(`${candidate}/health`)) {
        this.log(`[backendDiscovery] Backend reachable at ${candidate}`);
        return candidate;
      }
    }
    if (!lanScanEnabled(this.env)) return null;
    for (const host of await this.scanLan()) {
      const url = `http://${host}:${this.settings.port}`;
      if (await this.probe(`${url}/health`)) {
        this.log(`[backendDiscovery] Backend reachable at ${url} (LAN)`);
        return url;
      }
    }
    return null;
  }

  /**
   * Waits until a backend answers, up to the configured timeout. Never returns a
   * dead target on purpose: when the timeout expires the first candidate is kept
   * (the docker service name or localhost) so the watchdog can recover later.
   */
  async resolve(): Promise<string> {
    const deadline = this.now() + this.settings.waitTimeoutMs;
    let nextLogAt = 0;
    for (;;) {
      const found = await this.resolveOnce();
      if (found) {
        this.currentUrl = found;
        return found;
      }
      const remaining = deadline - this.now();
      if (remaining <= 0) {
        this.log(`[backendDiscovery] No backend answered within ${Math.round(this.settings.waitTimeoutMs / 1000)}s, keeping ${this.currentUrl} and retrying in the background`);
        return this.currentUrl;
      }
      if (this.now() >= nextLogAt) {
        nextLogAt = this.now() + RETRY_LOG_INTERVAL_MS;
        this.log(`[backendDiscovery] Backend not ready, retrying for ${Math.ceil(remaining / 1000)}s more`);
      }
      await this.sleep(Math.min(RETRY_INTERVAL_MS, remaining));
    }
  }

  /**
   * Re-resolves the backend without waiting (used by the watchdog when the
   * current target stopped answering). Returns null when nothing answers.
   */
  async reconnect(): Promise<string | null> {
    const found = await this.resolveOnce();
    if (found) this.currentUrl = found;
    return found;
  }
}
