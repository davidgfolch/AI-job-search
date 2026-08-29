import type { Job, JobListParams } from '../api/jobs';
import { titleWithShortcut } from '../shortcutsConfig';
import { useShortcuts } from '../shortcutsContext';
import ShortcutBadge from './ShortcutBadge';
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
}: JobActionsProps) {
    const { shortcuts, modifierPressed } = useShortcuts();
 
    const handleCopyPermalink = () => {
        if (!job) return;
        const permalink = `${window.location.origin}${window.location.pathname}?jobId=${job.id}`;
        navigator.clipboard.writeText(permalink);
    };

    return (
        <div className="header-actions">
            <button className="header-button state-button seen-button" onClick={onSeen} title="Mark as seen" disabled={isBulk || !job}>👁️</button>
            <button className="header-button state-button applied-button" onClick={onApplied} title={titleWithShortcut('Mark as applied', shortcuts.apply)} disabled={isBulk || !job}>✅<ShortcutBadge display={shortcuts.apply.display} visible={modifierPressed} /></button>
            <button className="header-button state-button ignore-button" onClick={onIgnore} title={titleWithShortcut('Mark as ignored', shortcuts.ignore)}>🚫<ShortcutBadge display={shortcuts.ignore.display} visible={modifierPressed} /></button>
            <button className="header-button state-button closed-button" onClick={onClosed} title="Mark as closed" disabled={isBulk || !job}>🔒</button>
            <button className="header-button state-button discarded-button" onClick={onDiscarded} title="Mark as discarded" disabled={isBulk || !job}>❌</button>
            <div className="button-separator"></div>
            <button className="header-button copy-button" onClick={handleCopyPermalink} title="Copy permalink to clipboard" disabled={isBulk || !job}>🔗</button>
            <button className="header-button nav-button" onClick={onPrevious} disabled={isBulk || !hasPrevious || !job} title={titleWithShortcut('Previous job', shortcuts.previous)}>⏮<ShortcutBadge display={shortcuts.previous.display} visible={modifierPressed} /></button>
            <button className="header-button nav-button" onClick={onNext} disabled={isBulk || !hasNext || !job} title={titleWithShortcut('Next job', shortcuts.next)}>⏭<ShortcutBadge display={shortcuts.next.display} visible={modifierPressed} /></button>
        </div>
    );
}
