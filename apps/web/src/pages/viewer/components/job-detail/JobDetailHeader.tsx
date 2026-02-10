import type { Job } from '../../api/ViewerApi';

interface JobDetailHeaderProps {
    job: Job;
    onClose?: () => void;
    onOpenMerged?: (id: number) => void;
}

export default function JobDetailHeader({ job, onClose, onOpenMerged }: JobDetailHeaderProps) {
    return (
        <div className="job-detail-header">
            <h2>
                <a href={job.url || '#'} target="_blank" rel="noopener noreferrer" className="job-link">
                    {job.title}
                </a>
            </h2>
            {job.merged_id && onOpenMerged && (
                <>
                {String(job.merged_id).split(',').map(id => (
                    <button 
                        key={id}
                        className="create-job-btn" 
                        onClick={() => onOpenMerged(Number(id.trim()))} 
                        title={`Open Merged Job (${id.trim()})`}
                    >
                        ⎋ Open Merged
                    </button>
                ))}
                </>
            )}
            {onClose && (
                <button className="create-job-btn" onClick={onClose} title="Close merged view">
                    ✕ Close
                </button>
            )}
        </div>
    );
}
