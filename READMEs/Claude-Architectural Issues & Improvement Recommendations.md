# Architectural Issues & Improvement Recommendations

## Summary

This document outlines architectural issues identified in the codebase and the improvements that were implemented.

## Issues Found

### Backend (`apps/backend`) - Layer Duplication & Tight Coupling

**Issues Found:**
- **Services are thin wrappers** - `JobsService` merely delegates to `JobsRepository` without adding business logic
- **Tight coupling** - Direct instantiation of services within other services (`FilterConfigurationsService()` in `get_watcher_stats`)
- **DRY violations** - Filter extraction logic duplicated across `jobs_service.py`, `statistics_service.py`, and `api/jobs.py`
- **Missing abstractions** - No interfaces/protocols defining service/repo contracts
- **Hardcoded filter keys** - `JOB_BOOLEAN_KEYS` defined in constants but re-listed inline in multiple places

### Frontend (`apps/web`) - Hook Complexity & State Management

**Issues Found:**
- **`useFilterWatcher.ts` has 198 lines** with complex state management (refs, intervals, notifications, debouncing)
- **Multiple ref patterns** (`notifiedCountsRef`, `lastRequestIdRef`, `justResetRef`) for state that could be in React state
- **Complex debouncing logic** mixed with polling logic

### Common Library (`apps/commonlib`) - Missing Abstractions

**Issue:** MySQL utilities handle both connection management and query execution in one class.

### Scrapper (`apps/scrapper`) - Code Organization

**Issue:** Scrapers for different sites likely have duplicate DOM parsing patterns.

## Implemented Improvements

### 1. Filter Parsing Utility Module

**Created:** `apps/backend/utils/filter_parser.py`

## Recommendations (Not Yet Implemented)

### 1. Backend - Introduce Dependency Injection

Currently, services instantiate repositories directly:
```python
def __init__(self, repo: JobsRepository = None):
    self.repo = repo or JobsRepository()  # Tight coupling
```

**Recommendation:** Create interfaces and inject dependencies:
```python
class IJobsRepository(Protocol):
    def list_jobs(...) -> Dict[str, Any]: ...

class JobsService:
    def __init__(self, repo: IJobsRepository):
        self.repo = repo
```

### 2. Backend - Remove Redundant Service Layer

The service layer currently adds no value. For CRUD operations, consider:
- Direct repository access from API layer, OR
- Convert services to true orchestrators with business logic

### 3. Frontend - Split `useFilterWatcher` Hook

**Recommendation:** Extract into composable hooks:
- `usePolling()` - Polling logic
- `useNotificationAggregator()` - Notification logic
- `useWatcherState()` - State management

### 4. Common Library - Separate Connection Pool

**Recommendation:** Split `MysqlUtil` into:
- Connection pool management
- Query execution utilities

### 5. Scrapper - Base Scraper Class

**Recommendation:** Create a base scraper class with common functionality:
- Login handling
- Navigation logic
- Error handling
- Anti-bot measures
