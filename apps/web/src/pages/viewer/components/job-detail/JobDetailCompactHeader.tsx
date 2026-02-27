import { type Job } from '../../api/ViewerApi';
import SkillsList from './SkillsList';
import CvMatchBar from '../../../common/components/core/CvMatchBar';

interface JobDetailCompactHeaderProps {
    job: Job;
}

export default function JobDetailCompactHeader({ job }: JobDetailCompactHeaderProps) {
    const allJobSkills = [job.required_technologies, job.optional_technologies]
        .filter(Boolean)
        .join(', ');

    const truncatedSalary = job.salary && job.salary.length > 50 
        ? job.salary.substring(0, 47) + '...' 
        : job.salary;

    return (
        <div className="job-detail-compact-header">
            <span className="compact-item">
                <span className="compact-company">{job.company}</span>
            </span>
            <span className="compact-item compact-modality">
                {job.modality}
            </span>
            {truncatedSalary && (
                <span className="compact-item compact-salary" title={job.salary || undefined}>
                    {truncatedSalary}
                </span>
            )}
            <span className="compact-item compact-skills">
                {allJobSkills && <SkillsList skills={allJobSkills} allJobSkills={allJobSkills} />}
            </span>
            {job.cv_match_percentage !== null && job.cv_match_percentage !== undefined && (
                <span className="compact-item compact-cv-match">
                    <CvMatchBar percentage={job.cv_match_percentage} />
                </span>
            )}
        </div>
    );
}
