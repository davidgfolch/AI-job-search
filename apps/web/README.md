# AI Job Search Web UI

The modern frontend for the AI Job Search application, built with **React**, **TypeScript**, and **Vite**.

## Features

- **Job Listing**: View and filter job offers scraped from various platforms.
- **Job Management**: Update job status (Applied, Interviewing, Rejected, etc.).
- **Statistics**: Visual insights into your job search progress.
- **Settings Page**: Manage environment variables and scrapper state directly from the browser.
- **Responsive Design**: Modern UI using CSS and standard React components.
- **Real-time Updates**: Interacts with the Python backend to fetch and update data.

## Settings Page

The Settings page (`/settings`) allows you to manage application configuration without restarting services.

### Environment Variables (`.env`)

Variables are grouped into four logical sections:

| Group | Env Prefix(es) | Description |
|---|---|---|
| **Scrapper** | `INFOJOBS_`, `LINKEDIN_`, `GLASSDOOR_`, `TECNOEMPLEO_`, `INDEED_`, `SHAKERS_` | Credentials, cadency, and search options for each scrapper platform. |
| **AI Enrichment** | `AI_`, `CLEAN_`, `WHERE_`, `SALARY_`, `SKILL_` | Model settings, timeouts, batch sizes, and enrichment flags. |
| **UI Frontend** | `APPLY_`, `GROSS_`, `VITE_` | UI behaviour like the apply modal default text and gross salary calculator URL. |
| **System & Base** | Everything else (e.g. `TZ`, `GMAIL_*`) | Timezone, Gmail 2FA credentials, and other system-level settings. |

- Fields containing `PWD`, `PASSWORD`, or `EMAIL` are rendered as **password inputs**.
- Each group has a dedicated **Save** button in the group header. A global **Save** button is also available in the section header and footer to save all groups at once.

### Scrapper State (`scrapper_state.json`)

- Displays the current scrapper state as editable JSON in a textarea.
- **Refresh** button (↻) reloads the file from the backend without saving.
- **Save** button persists your edits back to `scrapper_state.json`.

## Tech Stack

- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **Package Manager**: npm
- **Styling**: CSS Modules / Standard CSS
- **State Management**: React Query (TanStack Query)
- **Routing**: React Router
- **Testing**: Vitest + React Testing Library

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
