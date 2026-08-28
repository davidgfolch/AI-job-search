import type { Job } from '../../api/ViewerApi';
import { titleWithShortcut } from '../../shortcutsConfig';
import { useShortcuts } from '../../shortcutsContext';
import ShortcutBadge from '../ShortcutBadge';

interface JobDetailHeaderProps {
    job: Job;
    onCloseDuplicated?: () => void;
    onOpenDuplicated?: (id: number) => void;
}

export default function JobDetailHeader({ job, onCloseDuplicated, onOpenDuplicated }: JobDetailHeaderProps) {
    const { shortcuts, modifierPressed } = useShortcuts();
    return (
        <div className="job-detail-header">
            <h2 id="job-detail-title">
                <a href={job.url || '#'} target="_blank" rel="noopener noreferrer" className="job-link" title={titleWithShortcut('Open job URL', shortcuts.openUrl)}>
                    {job.title}
                    <ShortcutBadge display={shortcuts.openUrl.display} visible={modifierPressed} />
                </a>
            </h2>
            {job.duplicated_id && onOpenDuplicated && (
                <>
                {String(job.duplicated_id).split(',').map(id => (
                    <button 
                        key={id}
                        className="create-job-btn open-duplicated-btn" 
                        onClick={() => onOpenDuplicated(Number(id.trim()))} 
                        title={`Open Duplicated Job (${id.trim()})`}
                    >
                        Open Duplicated
                    </button>
                ))}
                </>
            )}
            {onCloseDuplicated && (
                <button className="create-job-btn" style={{fontSize: '1rem'}} onClick={onCloseDuplicated} title="Close duplicated view">
                    ✕ Close old duplicated
                </button>
            )}
            <ShortcutBadge display={shortcuts.detailFocus.display} visible={modifierPressed} />
        </div>
    );
}
