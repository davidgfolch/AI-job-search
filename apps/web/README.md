# AI Job Search Web UI

The modern frontend for the AI Job Search application, built with **React**, **TypeScript**, and **Vite**.

## Features

- **Job Listing**: View and filter job offers scropped from various platforms.
- **Job Management**: Update job status (Applied, Interviewing, Rejected, etc.).
- **Statistics**: Visual insights into your job search progress (Integration pending).
- **Responsive Design**: Modern UI using CSS and standard React components.
- **Real-time Updates**: Interacts with the Python backend to fetch and update data.

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
