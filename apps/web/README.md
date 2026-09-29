# AI Job Search Web UI

The modern frontend for the AI Job Search application, built with **React**, **TypeScript**, and **Vite**.

## Features

- **Job Listing**: View and filter job offers scraped from various platforms.
- **Infinite Scroll Pagination**: The list keeps fetching pages on its own until it fills the screen, then again whenever the end of the list is scrolled into view.
- **Next / Previous Job Navigation**: The ⏮ / ⏭ buttons and the `Alt+P` / `Alt+N` shortcuts move the selection, and the list scrolls whenever the new selection is outside the visible frame.
- **Job Management**: Update job status (Applied, Interviewing, Rejected, etc.).
- **Statistics**: Visual insights into your job search progress.
- **Settings Page**: Manage environment variables and scrapper state directly from the browser.
- **Responsive Design**: Modern UI using CSS and standard React components.
- **Real-time Updates**: Interacts with the Python backend to fetch and update data.

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

The web app auto-discovers the backend API URL at Vite startup:

| Environment | Behavior |
|-------------|----------|
| Docker | Uses `http://backend:8000` (Docker DNS) |
| Local (default) | Uses `http://localhost:8000` |
| Local (`BACKEND_DISCOVERY=True`) | Tries localhost → scans LAN for port 8000 → verifies `/health` |

Set `BACKEND_DISCOVERY=True` in your `.env` to enable automatic LAN discovery when the backend runs on a different machine.

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
- `npm run lint`: Run ESLint to check for code quality issues.
- `npm test`: Run unit tests using Vitest.
- `npm run preview`: Preview the production build locally.

## Project Structure

- `src/components`: Reusable UI components.
- `src/pages`: Application pages (routes).
- `src/hooks`: Custom React hooks (including API hooks).
- `src/services`: API service layer.
- `src/types`: TypeScript type definitions.
- `src/utils`: Utility functions.
