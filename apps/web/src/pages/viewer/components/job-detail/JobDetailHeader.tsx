import type { Job } from '../../api/ViewerApi';

interface JobDetailHeaderProps {
    job: Job;
    onClose?: () => void;
    onOpenDuplicated?: (id: number) => void;
}

export default function JobDetailHeader({ job, onClose, onOpenDuplicated }: JobDetailHeaderProps) {
    return (
        <div className="job-detail-header">
            <h2 id="job-detail-title">
                <a href={job.url || '#'} target="_blank" rel="noopener noreferrer" className="job-link">
                    {job.title}
                </a>
            </h2>
            {job.duplicated_id && onOpenDuplicated && (
                <>
                {String(job.duplicated_id).split(',').map(id => (
                    <button 
                        key={id}
                        className="create-job-btn" 
                        onClick={() => onOpenDuplicated(Number(id.trim()))} 
                        title={`Open Duplicated Job (${id.trim()})`}
                    >
                        ⎋ Open Duplicated
                    </button>
                ))}
                </>
            )}
            {onClose && (
                <button className="create-job-btn" onClick={onClose} title="Close duplicated view">
                    ✕ Close
                </button>
            )}
        </div>
    );
}
