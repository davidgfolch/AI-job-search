import type { Job, JobListParams } from '../api/jobs';
import { BOOLEAN_FILTER_KEYS } from '../config/filterConfig';
import './JobActions.css';

interface JobActionsProps {
    job?: Job | null;
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
    isBulk?: boolean;
    activeConfigName?: string;
    onDelete?: (count: number) => void;
    selectedCount?: number;
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
     isBulk = false,
     activeConfigName,
     onDelete,
     selectedCount = 0,
 }: JobActionsProps) {
 
     const handleCopyPermalink = () => {
         if (!job) return;
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
 
     const isDeleteMode = activeConfigName === 'Clean - Delete old jobs';
 
     if (isDeleteMode) {
         return (
             <div className="header-actions">
                <button 
                    className="header-button delete-button" 
                    onClick={() => onDelete?.(selectedCount)} 
                    title="Delete jobs"
                    style={{ 
                        backgroundColor: selectedCount < 1 ? undefined : '#dc3545', 
                        color: selectedCount < 1 ? undefined : 'white', 
                        fontWeight: 'bold', 
                        minWidth: '120px' 
                    }}
                    disabled={selectedCount < 1}
                >
                 {isBulk ? `DELETE ${selectedCount}` : 'DELETE'}
                </button>
             </div>
         );
     }

    return (
        <div className="header-actions">
            <button className="header-button state-button seen-button" onClick={onSeen} title="Mark as seen" disabled={isBulk || !job}>👁️</button>
            <button className="header-button state-button applied-button" onClick={onApplied} title="Mark as applied" disabled={isBulk || !job}>✅</button>
            <button className="header-button state-button ignore-button" onClick={onIgnore} title="Mark as ignored">🚫</button>
            <button className="header-button state-button closed-button" onClick={onClosed} title="Mark as closed" disabled={isBulk || !job}>🔒</button>
            <button className="header-button state-button discarded-button" onClick={onDiscarded} title="Mark as discarded" disabled={isBulk || !job}>❌</button>
            <div className="button-separator"></div>
            <button className="header-button copy-button" onClick={handleCopyPermalink} title="Copy permalink to clipboard" disabled={isBulk || !job}>🔗</button>
            <button className="header-button nav-button" onClick={onPrevious} disabled={isBulk || !hasPrevious || !job} title="Previous job">⏮</button>
            <button className="header-button nav-button" onClick={onNext} disabled={isBulk || !hasNext || !job} title="Next job">⏭</button>
        </div>
    );
}
