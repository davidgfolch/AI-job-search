import { type Job } from '../../api/ViewerApi';
import AppliedJobsWarning from './AppliedJobsWarning';
import SalaryActions from './SalaryActions';
import SkillsList from './SkillsList';
import CvMatchBar from '../../../common/components/core/CvMatchBar';

interface JobDetailInfoProps {
    job: Job;
    appliedCompanyJobs: Job[];
    loadingApplied: boolean;
    onUpdate?: (data: Partial<Job>) => void;
    showCalculator: boolean;
    onToggleCalculator: () => void;
}

const formatDateTime = (d: string | null) => {
    if (!d) return '-';
    return new Date(d).toLocaleString(undefined, {
        year: 'numeric', month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
};

const isModified = (created: string | undefined | null, modified: string | undefined | null) => {
    if (!created || !modified) return false;
    const d1 = new Date(created);
    const d2 = new Date(modified);
    return Math.abs(d1.getTime() - d2.getTime()) >= 5 * 60 * 1000;
};

export default function JobDetailInfo({ job, appliedCompanyJobs, loadingApplied, onUpdate, showCalculator, onToggleCalculator }: JobDetailInfoProps) {
    const allJobSkills = [job.required_technologies, job.optional_technologies].filter(Boolean).join(', ');

    return (
        <ul className="job-info">
            {job.ai_enrich_error && (
                <li className="info-row" style={{ color: 'red' }}>
                    Enrich Error: <span title="Click to copy" onClick={() => navigator.clipboard.writeText(job.ai_enrich_error!)} style={{ cursor: 'pointer' }}>{job.ai_enrich_error}</span>
                    <button className="config-btn" style={{ marginLeft: '1rem', padding: '2px 8px', fontSize: '0.75rem' }} onClick={() => onUpdate?.({ ai_enrich_error: null, ai_enriched: false })}>Force Re-enrich</button>
                </li>
            )}
            {job.company && (
                <li className="info-row">Company: <span>{job.company}</span><AppliedJobsWarning appliedJobs={appliedCompanyJobs} loadingApplied={loadingApplied} /></li>
            )}
            {job.location && <li className="info-row">Location: <span>{job.location}</span></li>}
            {job.modality && <li className="info-row">Modality: <span>{job.modality}</span></li>}
            {job.salary && (
                <li className="info-row job-salary-row">Salary: <span className="salary-value-text">{job.salary}</span><SalaryActions onToggleCalculator={onToggleCalculator} onUpdate={onUpdate} /></li>
            )}
            {(job.required_technologies || job.optional_technologies) && (
                <li className="info-row">Skills:<ul>
                    {job.required_technologies && <li>Required: <SkillsList skills={job.required_technologies} allJobSkills={allJobSkills} /></li>}
                    {job.optional_technologies && <li>Optional: <SkillsList skills={job.optional_technologies} allJobSkills={allJobSkills} /></li>}
                </ul></li>
            )}
            {job.web_page && (
                <li className="info-row">Source: <span>{job.web_page}</span><ul>
                    {job.created && <li className="info-row"><span>{formatDateTime(job.created)}</span> created</li>}
                    {job.modified && isModified(job.created, job.modified) && <li className="info-row"><span>{formatDateTime(job.modified)}</span> modified</li>}
                </ul></li>
            )}
            {job.client && <li className="info-row">Client: <span>{job.client}</span></li>}
            {job.cv_match_percentage && <li className="info-row cv-match-row">CV Match: <CvMatchBar percentage={job.cv_match_percentage} /></li>}
        </ul>
    );
}
