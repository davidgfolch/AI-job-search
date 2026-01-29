import type { Job } from '../../api/jobs';

interface JobDetailHeaderProps {
    job: Job;
    onCreateNew?: () => void;
    onDelete?: () => void;
}

export default function JobDetailHeader({ job, onCreateNew, onDelete }: JobDetailHeaderProps) {
    return (
        <div className="job-detail-header">
            <h2>
                <a href={job.url || '#'} target="_blank" rel="noopener noreferrer" className="job-link">
                    {job.title}
                </a>
            </h2>
            {onCreateNew && (
                <button className="create-job-btn" onClick={onCreateNew} title="Create New Job">
                    ➕ Create
                </button>
            )}
            {onDelete && (
                <button className="create-job-btn" onClick={onDelete} title="Delete this job">
                    🗑️ Delete
                </button>
            )}
        </div>
    );
}
