import type { AppliedCompanyJob } from '../../api/jobs';

interface AppliedJobsWarningProps {
    appliedJobs: AppliedCompanyJob[];
    loadingApplied: boolean;
}

export default function AppliedJobsWarning({ appliedJobs, loadingApplied }: AppliedJobsWarningProps) {
    if (loadingApplied || appliedJobs.length === 0) return null;

    return (
        <span className="applied-company-indicator">
            {' '}👉 ⚠️{' '}
            <a href={`/?ids=${appliedJobs.map(j => j.id).join(',')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="already-applied-link"
                title="Open in new tab showing these specific jobs">
                already applied to {appliedJobs.length}
            </a>
            {appliedJobs.map(aj => (
                <span key={aj.id} className="applied-date">
                    {' '}{aj.created?.startsWith('...') ? aj.created :
                        (aj.created ? '📅 ' + new Date(aj.created).toLocaleDateString('en-GB', {
                            day: '2-digit',
                            month: '2-digit',
                            year: '2-digit'
                        }).replace(/\//g, '-') : '')}
                </span>
            ))}
        </span>
    );
}
