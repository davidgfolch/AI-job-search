# AI Job Search Web UI

The modern frontend for the AI Job Search application, built with **React**, **TypeScript**, and **Vite**.

## Features

- **Job Listing**: View and filter job offers scraped from various platforms.
- **Infinite Scroll Pagination**: The list keeps fetching pages on its own until it fills the screen, then again whenever the end of the list is scrolled into view.
- **Next / Previous Job Navigation**: The ⏮ / ⏭ buttons and the `Alt+P` / `Alt+N` shortcuts move the selection, and the list scrolls whenever the new selection is outside the visible frame.
- **Job Management**: Update job status (Applied, Interviewing, Rejected, etc.) and edit job data (title, company, location, salary, skills, modality, comments) via the job detail edit form — advanced fields are shown under the "Edit All" toggle. Modality is multi-select (checkbox group): a job can allow several arrangements at once (REMOTE/HYBRID/ON_SITE).
- **Statistics**: Visual insights into your job search progress.
- **Dashboard autorefresh**: The dashboard polls the backend every 30 s and shows a human-readable "Last updated" timestamp plus the autorefresh interval. The top row shows the configured AI backend, Ollama, Prometheus and Grafana health pills with status, IP/URL and LAN scope.
- **Settings Page**: Manage environment variables and scrapper state directly from the browser.
- **Responsive Design**: Modern UI using CSS and standard React components.
- **Real-time Updates**: The watcher badge receives near-realtime updates via Server-Sent Events (`GET /api/jobs/watcher-events`). When the backend creates, updates, or deletes a job, it broadcasts an SSE event and the frontend debounces a stats refetch (~200 ms), so the `+N` / `-M` watcher badge reflects new matches within seconds instead of waiting up to 5 minutes for the next poll.

## Infinite Scroll Pagination

The job list is paginated by the backend (`page` / `size` query params) and `useAutoLoadMore` (`src/pages/viewer/hooks/useAutoLoadMore.ts`) requests the following pages. It is driven by two viewport-relative signals, so it works regardless of font size, screen height, or which element actually scrolls:

- **Fill**: while the end of the list is already on screen there is nothing to scroll to, so the next page is fetched. Every appended page re-checks, which keeps loading until the list overflows the screen or runs out of jobs.
- **Scroll**: the next page is fetched when the end of the list comes within a `200px` prefetch margin of the bottom of the viewport. This is driven by an `IntersectionObserver` rooted at the viewport (not at the list container) plus a capture-phase `scroll` listener, because Firefox does not report intersection changes caused by a nested container scroll. A `ResizeObserver` on the table re-checks the fill case after a window resize or a font-size change.

Both signals observe a stable `<div className="job-table-sentinel">` rendered after the table. It must not be a table row: appending a page makes the last row a mid-list element, so an observer bound to it would watch the wrong node and pagination would stop after the first page.

Requests are latched, so at most one page is in flight even when several signals fire in the same frame. An empty list is skipped as well: with no rows the end of the list is trivially on screen and its geometry says nothing about whether more is needed. A page that comes back with only already-known jobs would leave the list length unchanged and the fill loop would never end, so `useJobsData.handleLoadMore` also refuses pages past the last one implied by the server `total`.

## Keeping the Selected Job Visible

Moving to the next or previous job — with the ⏮ / ⏭ buttons, the `Alt+P` / `Alt+N` shortcuts, or the auto-selection that follows a state change — selects a row that is usually outside the visible frame. `useScrollSelectedIntoView` (`src/pages/viewer/hooks/useScrollSelectedIntoView.ts`) scrolls `.job-table-container`, the scroll container of the list, by the smallest amount that brings the row back inside it, in both directions and also horizontally.

`Element.scrollIntoView` is deliberately not used: `block: 'nearest'` aligns the row with the nearest edge of the scroll port, and for an upward step that edge is the one the sticky `<thead>` floats over, so the row ends up behind the header and still reads as missing. The hook measures the frame between the bottom of that header and the bottom edge of the list instead. It is a no-op while the row is already readable, it skips lists that report no layout (a hidden tab or a collapsed panel), and it anchors a row taller than the frame right below the header.

Because the scroll happens in a layout effect on the row that React has just committed, it also covers the job a newly loaded page starts at: stepping past the last loaded job appends the next page, selects its first job, and scrolls down to it.

## Reloading the Active Filter Configuration

The job list query is keyed by its filters (`['jobs', filters]` in `src/pages/viewer/hooks/useJobsData.ts`), so applying the configuration that is already in effect produces the same query key. React Query then keeps serving the cached page for `staleTime` (30 s) and nothing refetches, which left the list showing the jobs it already had while the `+N` watcher badge was counting the new ones. Applying a *different* configuration changes the key, so it fetches — which is why switching away and back used to be the only way to see the new jobs.

`Filters.tsx` therefore compares what the configuration would produce against the filters already applied, and reloads the current page when nothing changes. The comparison is done on the merged result rather than on the stored configuration, because a configuration only saves the filters that differ from the defaults and inherits the rest from the current ones.

The reload is `useJobsData.reloadCurrentPage`, which calls `refetch()` on the observed query. It deliberately does **not** use `refreshJobs` / `hardRefresh`, whose `queryClient.resetQueries({ queryKey: ['jobs'] })` resets *every* filter set in the cache: the previously active configuration gets refetched too and can come back as the visible list. `refetch()` touches one query, so no other configuration can be resurrected.

The selected job is kept: reloading is not a reset, so the detail panel stays on the job it had. The watcher badge for the configuration is cleared at the same time by `useFilterWatcher.resetWatcher`, which keeps the badge and the refreshed list consistent. Loading a configuration from a page deeper than the first already changes the query key, so no reload is triggered there.

### Watcher Badge

Each watched filter configuration shows a badge next to its name in the configuration dropdown and pinned configurations:

- `+{N}` (green) — N new jobs matching the filter since the last check cutoff
- `-{N}` (gray) — N jobs that left the filter or were deleted since the last check

The badge reads from `GET /api/jobs/watcher-stats`, which queries the `watcher_match` table (O(1) count instead of rebuilding MySQL views). On any job write through the backend API, an SSE event is broadcast (`GET /api/jobs/watcher-events`) and the frontend triggers a debounced refetch (~200 ms), so the badge stays near-realtime. A 5-minute poll runs as a safety net if the SSE connection drops.

Every configuration carries **its own cutoff**, sent as a `from_<config_id>` param and honoured as such by the backend. The cutoff is the instant up to which the user has already seen the matches ("seen up to now"):

- The global start time (restored from the persisted last check) is the cutoff of every configuration until one of them is reloaded.
- Reloading a configuration (`useFilterWatcher.resetWatcher`) moves **only that configuration's** cutoff to the current instant and clears its badge. The other configurations keep their own cutoffs, so reloading one does not change what the others report.
- The count returned by the backend is shown as it is — it is never masked out. A reloaded configuration therefore starts counting (and notifying) again as soon as a new match arrives, instead of staying muted.

## Settings Page

The Settings page (`/settings`) allows you to manage application configuration without restarting services.

### Environment Variables (`.env` & `.env.secrets`)

Variables are grouped into four logical sections:

| Group | Env Prefix(es) | Description |
|---|---|---|
| **Scrapper** | `SCRAPPER_INFOJOBS_`, `SCRAPPER_LINKEDIN_`, `SCRAPPER_GLASSDOOR_`, `SCRAPPER_TECNOEMPLEO_`, `SCRAPPER_INDEED_` | Credentials, cadency, and search options for each scrapper platform. |
| **AI Enrichment** | `AI_`, `CLEAN_`, `WHERE_`, `SALARY_`, `SKILL_` | Model settings, timeouts, batch sizes, and enrichment flags. |
| **UI Frontend** | `APPLY_`, `GROSS_`, `VITE_` | UI behaviour like the apply modal default text and gross salary calculator URL. |
| **System & Base** | Everything else (e.g. `GLOBAL_TZ`, `GMAIL_*`) | Timezone, Gmail 2FA credentials, and other system-level settings. |

- Fields containing `PWD`, `PASSWORD`, or `EMAIL` are rendered as **password inputs**.
- Each group has a dedicated **Save** button in the group header. A global **Save** button is also available in the section header and footer to save all groups at once.

### Scrapper State

- Displays the current scrapper state as editable JSON in a textarea.
- **Refresh** button (↻) reloads the state from the backend via `GET /settings/scrapper-state`.
- **Save** button persists your edits to the shared MySQL database via `POST /settings/scrapper-state`.

## Tech Stack

- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **Package Manager**: npm
- **Styling**: CSS Modules / Standard CSS
- **State Management**: React Query (TanStack Query)
- **Routing**: React Router
- **Testing**: Vitest + React Testing Library

## Backend Discovery

The web app resolves the backend API URL when the Vite dev server starts, and keeps watching it afterwards.

**Resolution order** (the first candidate that answers on `/health` wins):

| Environment | Candidates, in order |
|-------------|-----------------------|
| Docker | `http://backend:8000` → `http://host.docker.internal:8000` → `http://localhost:8000` → LAN scan |
| Host | `http://localhost:8000` → `http://host.docker.internal:8000` → `http://backend:8000` → LAN scan |

`BACKEND_URL` (when set) pins the target and short-circuits the chain. The LAN scan is only used when `BACKEND_DISCOVERY=True`.

**Waiting at startup**: the dev server does not serve until a backend answers, so a container start (or a host reboot, where every container comes up in parallel) never ends up proxying to a dead target. The wait is bounded by `BACKEND_WAIT_TIMEOUT_SECONDS` (default 120); when it expires the web keeps serving and the watchdog takes over.

**Reconnecting**: a watchdog probes the current target every `BACKEND_CHECK_INTERVAL_SECONDS` (default 10). After `BACKEND_MAX_RETRIES` (default 3) consecutive failures it resolves the backend again (candidate chain + LAN scan) and retargets the live proxy — no restart needed.

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKEND_URL` | – | Pins the backend API URL (skips discovery) |
| `BACKEND_PORT` | `8000` | Backend API port |
| `BACKEND_DISCOVERY` | `False` | `True` allows the LAN scan as a last resort |
| `BACKEND_WAIT_TIMEOUT_SECONDS` | `120` | How long the web waits for the backend at startup |
| `BACKEND_CHECK_INTERVAL_SECONDS` | `10` | Watchdog probe interval |
| `BACKEND_MAX_RETRIES` | `3` | Failed probes before the backend is resolved again |

## Setup & Running

### Prerequisites

Ensure you have `Node.js` (LTS recommended) and `npm` installed.

### Installation

```bash
cd apps/web
npm install
```

### Running Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

## Scripts

- `npm run dev`: Start the development server.
- `npm run build`: Build the application for production.
- `npm run preview`: Preview the production build locally.
- `npm run lint` / `npm run typecheck`: run together by `./scripts/lint.sh web` from the repo root.

Tests run through the centralized runner (`./scripts/test.sh commonlib web`), not `npm test` directly.

### Coverage

`./scripts/test.sh --coverage web` measures **production code only**: `vite.config.ts` includes
every `src` file (so lazily-routed pages still count) and excludes `**/test/**`, CSS,
`node_modules` and `dist`. The Vitest threshold is 90% on **statements and lines**;
functions and branches are reported only.

The enforced frontend floor is the **union** of this unit coverage and the e2e coverage
(see `apps/e2e/coverage.config.ts`), gated by `scripts/coverage/frontend-coverage-gate.mjs`:

```bash
./scripts/test.sh --coverage commonlib web e2e   # both reports, then the union gate
```

## Project Structure

- `src/components`: Reusable UI components.
- `src/pages`: Application pages (routes).
- `src/hooks`: Custom React hooks (including API hooks).
- `src/services`: API service layer.
- `src/types`: TypeScript type definitions.
- `src/utils`: Utility functions.
