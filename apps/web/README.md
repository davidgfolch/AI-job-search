# AI Job Search Web UI

The modern frontend for the AI Job Search application, built with **React**, **TypeScript**, and **Vite**.

## Features

- **Job Listing**: View and filter job offers scraped from various platforms. The list shows Location and Modality (R/H/O initials) next to Company; columns flex with the available list width and the extra ones hide automatically in a narrow panel or on a small screen.
- **Infinite Scroll Pagination**: The list keeps fetching pages on its own until it fills the screen, then again whenever the end of the list is scrolled into view.
- **Next / Previous Job Navigation**: The ⏮ / ⏭ buttons and the `Alt+P` / `Alt+N` shortcuts move the selection, and the list scrolls whenever the new selection is outside the visible frame.
- **Resizable Panels**: Drag the divider (or focus it and use the arrow keys) between the job list and the detail panel to adjust their widths. The ratio is remembered across reloads; the ↔ button or a double-click on the divider restores 50/50. The ‹ / › buttons toggle the list/detail panels off and back on. On mobile the panels stay stacked and the divider is hidden.
- **Job Management**: Update job status (Applied, Interviewing, Rejected, etc.) and edit job data (title, company, location, salary, skills, modality, comments) via the job detail edit form — advanced fields are shown under the "Edit All" toggle. Modality is multi-select (checkbox group): a job can allow several arrangements at once (REMOTE/HYBRID/ON_SITE). For hybrid jobs the detail also shows the extracted arrangement (`hybrid_info`, e.g. "3 days remote / 2 days office") right below the modality.
- **Filter Configurations**: Save the current filters under a name, then load, pin, watch, stats or delete them from the configuration dropdown.
- **Statistics**: Visual insights into your job search progress. A global Site filter (default `Linkedin`, or `(All)`) applies to the source and keyword charts; keywords are charted per keyword (aggregated across scraper sites in `(All)`), with reported totals, processed/new/duplicate bars and a table of already-in-DB job ids.
- **Dashboard autorefresh**: The dashboard polls the backend every 30 s and shows a human-readable "Last updated" timestamp plus the autorefresh interval. The top row shows the configured AI backend, Ollama, Prometheus and Grafana health pills with status, IP/URL and LAN scope.
- **Settings Page**: Manage environment variables and scrapper state directly from the browser.
- **Responsive Design**: Modern UI using CSS and standard React components.
- **Real-time Updates**: The watcher badge receives near-realtime updates via Server-Sent Events (`GET /api/jobs/watcher-events`). When the backend creates, updates, or deletes a job, it broadcasts an SSE event and the frontend debounces a stats refetch (~200 ms), so the `+N` / `-M` watcher badge reflects new matches within seconds instead of waiting up to 5 minutes for the next poll.

## Filter Configurations

Filter configurations are named filter sets stored by the backend, listed in the dropdown at the top of the filters panel and optionally pinned as shortcuts.
A configuration stores the filters that differ from the defaults; loading it merges them over the current filters and resets the list to page 1.

### Auto Select All

The "Auto select all" pill below the Modality box stores `auto_select_all` in the configuration's `filters` JSON, so it is saved, loaded, exported and migrated with the configuration.
When enabled, a bulk action targets every matching job instead of only the loaded page. Manually deselecting rows is respected until the next configuration or filter change.
Only `true` enables it: a configuration that omits the flag, or stores it as `null`, loads with the pill unselected.

### Filter Expanded

The "Filter expanded" pill next to "Auto select all" stores `filter_expanded` in the configuration's `filters` JSON, so it is saved, loaded, exported and migrated with the configuration.
Loading a configuration expands the filters panel when the flag is `true` and collapses it otherwise (`null`/absent means collapsed);
this covers dropdown entries, pinned configurations and the `Alt+#` shortcuts.
Clicking the pill toggles the flag and the panel immediately. The header `Filters ▼/▶` toggle only opens or closes the panel
and does not change the saved flag: use the pill to choose what a configuration does when it loads.

The "By company" default configuration ships with `filter_expanded: true`, so it opens the panel, focuses the SQL input and selects the `rlike` literal.

### Watcher Badge

Each watched filter configuration shows a badge next to its name in the configuration dropdown and pinned configurations:

- `+{N}` (green) — N new jobs matching the filter since the last check cutoff
- `-{N}` (gray) — N jobs that left the filter or were deleted since the last check

The badge reads from `GET /api/jobs/watcher-stats`. On any job write through the backend API, an SSE event is broadcast
(`GET /api/jobs/watcher-events`) and the frontend triggers a debounced refetch (~200 ms), so the badge stays near-realtime.
A 5-minute poll runs as a safety net if the SSE connection drops.

Every configuration carries **its own cutoff**, sent as a `from_<config_id>` param and honoured as such by the backend.
The cutoff is the instant up to which the user has already seen the matches ("seen up to now"):

- The global start time (restored from the persisted last check) is the cutoff of every configuration until one of them is reloaded.
- Reloading a configuration moves **only that configuration's** cutoff to the current instant and clears its badge.
  The other configurations keep their own cutoffs, so reloading one does not change what the others report.
- The count returned by the backend is shown as it is — it is never masked out. A reloaded configuration therefore starts
  counting (and notifying) again as soon as a new match arrives, instead of staying muted.

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

Ensure you have `Node.js` 22.12+ (Node 24 recommended) and `npm` installed.

### Installation

From the repository root:

```bash
./scripts/install.sh    # Linux/Mac
.\scripts\install.bat   # Windows
```

### Running Development Server

From the repository root:

```bash
./apps/web/run.sh    # Linux/Mac
.\apps\web\run.bat   # Windows
```

The application will be available at `http://localhost:5173`.

## Scripts

- `npm run dev`: Start the development server (wrapped by `./apps/web/run.sh` / `.\apps\web\run.bat`).
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
