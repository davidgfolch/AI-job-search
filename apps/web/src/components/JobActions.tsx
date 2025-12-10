import type { Job, JobListParams } from '../api/jobs';
import { BOOLEAN_FILTER_KEYS } from '../config/filterConfig';
import './JobActions.css';

interface JobActionsProps {
    job: Job;
    filters: JobListParams;
    onSeen: () => void;
    onApplied: () => void;
    onDiscarded: () => void;
    onClosed: () => void;
    onIgnore: () => void;
    onNext: () => void;
    onPrevious: () => void;
    hasNext: boolean;
    hasPrevious: boolean;
}

export default function JobActions({
    job,
    filters,
    onSeen,
    onApplied,
    onDiscarded,
    onClosed,
    onIgnore,
    onNext,
    onPrevious,
    hasNext,
    hasPrevious,
}: JobActionsProps) {
    const handleCopyPermalink = () => {
        const params = new URLSearchParams();
        params.set('jobId', job.id.toString());
        if (filters.search) params.set('search', filters.search);
        if (filters.order) params.set('order', filters.order);
        if (filters.days_old) params.set('days_old', filters.days_old.toString());
        if (filters.salary) params.set('salary', filters.salary);
        if (filters.sql_filter) params.set('sql_filter', filters.sql_filter);
        // Add boolean filters
        BOOLEAN_FILTER_KEYS.forEach(key => {
            if (filters[key] !== undefined) {
                params.set(key, String(filters[key]));
            }
        });
        const permalink = `${window.location.origin}${window.location.pathname}?${params.toString()}`;
        navigator.clipboard.writeText(permalink);
    };

    return (
        <div className="header-actions">
            <button className="header-button state-button seen-button" onClick={onSeen} title="Mark as seen">👁️</button>
            <button className="header-button state-button applied-button" onClick={onApplied} title="Mark as applied">✅</button>
            <button className="header-button state-button discarded-button" onClick={onDiscarded} title="Mark as discarded">❌</button>
            <button className="header-button state-button closed-button" onClick={onClosed} title="Mark as closed">🔒</button>
            <button className="header-button state-button ignore-button" onClick={onIgnore} title="Mark as ignored">🚫</button>
            <div className="button-separator"></div>
            <button className="header-button copy-button" onClick={handleCopyPermalink} title="Copy permalink to clipboard">🔗</button>
            <button className="header-button nav-button" onClick={onPrevious} disabled={!hasPrevious} title="Previous job">⏮</button>
            <button className="header-button nav-button" onClick={onNext} disabled={!hasNext} title="Next job">⏭</button>
        </div>
    );
}
