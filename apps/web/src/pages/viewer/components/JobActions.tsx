import type { Job, JobListParams } from '../api/jobs';
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
        const permalink = `${window.location.origin}${window.location.pathname}?jobId=${job.id}`;
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
