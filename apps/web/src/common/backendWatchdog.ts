const DEFAULT_CHECK_INTERVAL_MS = 10000;
const DEFAULT_MAX_FAILURES = 3;

export interface BackendWatchdogOptions {
  /** Probes the current target; true when it answers. */
  check: () => Promise<boolean>;
  /** Looks for a reachable backend again; null when nothing answers. */
  reconnect: () => Promise<string | null>;
  /** The target currently in use. */
  current: () => string;
  /** Called with the new target when the backend moved. */
  onChange: (url: string) => void;
  checkIntervalMs?: number;
  maxFailures?: number;
  log?: (message: string) => void;
}

/**
 * Watches the backend target: after N consecutive failed probes it resolves the
 * backend again and reports the new URL so the proxy can be retargeted.
 */
export class BackendWatchdog {
  private readonly options: Required<BackendWatchdogOptions>;
  private failures = 0;
  private timer: ReturnType<typeof setInterval> | undefined;
  private ticking = false;

  constructor(options: BackendWatchdogOptions) {
    this.options = {
      ...options,
      checkIntervalMs: options.checkIntervalMs ?? DEFAULT_CHECK_INTERVAL_MS,
      maxFailures: options.maxFailures ?? DEFAULT_MAX_FAILURES,
      log: options.log ?? ((message: string) => console.log(message)),
    };
  }

  /** Consecutive failed probes so far. */
  get failureCount(): number {
    return this.failures;
  }

  get running(): boolean {
    return this.timer !== undefined;
  }

  start(): void {
    if (this.timer !== undefined) return;
    const timer = setInterval(() => { void this.tick(); }, this.options.checkIntervalMs);
    this.timer = timer;
    const unref = (timer as unknown as { unref?: () => void }).unref;
    if (typeof unref === 'function') unref.call(timer);
  }

  stop(): void {
    if (this.timer === undefined) return;
    clearInterval(this.timer);
    this.timer = undefined;
  }

  private async tick(): Promise<void> {
    if (this.ticking) return;
    this.ticking = true;
    try {
      if (await this.options.check()) {
        if (this.failures > 0) this.options.log(`[backendWatchdog] Backend reachable again after ${this.failures} failed check(s)`);
        this.failures = 0;
        return;
      }
      this.failures += 1;
      this.options.log(`[backendWatchdog] Backend unreachable (${this.failures}/${this.options.maxFailures})`);
      if (this.failures < this.options.maxFailures) return;
      this.failures = 0;
      const url = await this.options.reconnect();
      if (!url) {
        this.options.log(`[backendWatchdog] No backend found while reconnecting, keeping ${this.options.current()}`);
        return;
      }
      if (url === this.options.current()) {
        this.options.log(`[backendWatchdog] Backend still unreachable at ${url}`);
        return;
      }
      this.options.log(`[backendWatchdog] Backend moved, switching proxy target to ${url}`);
      this.options.onChange(url);
    } catch (error) {
      this.options.log(`[backendWatchdog] Backend check failed: ${(error as Error).message}`);
    } finally {
      this.ticking = false;
    }
  }
}
