import { useState, useRef, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import ReactMarkdownCustom from '../../common/components/core/ReactMarkdownCustom';
import { jobsApi, type Job } from "../api/ViewerApi";
import './JobDetail.css';
import './Filters.css';
import './FilterConfigurations.css';
import SalaryCalculator from './salaryCalculator/SalaryCalculator';
import { parseSalaryCalculationFromComments, parseAllSalaryCalculationsFromComments } from './salaryCalculator/salaryFormatters';
import CvMatchBar from '../../common/components/core/CvMatchBar';
import { STATE_FIELDS } from '../constants';
import JobDetailHeader from './job-detail/JobDetailHeader';
import AppliedJobsWarning from './job-detail/AppliedJobsWarning';
import SalaryActions from './job-detail/SalaryActions';
import SkillsList from './job-detail/SkillsList';

interface JobDetailProps {
    job: Job;
    onUpdate?: (data: Partial<Job>) => void;
    onOpenDuplicated?: (id: number) => void;
    onClose?: () => void;
    hideDuplicatedButton?: boolean;
}

export default function JobDetail({ job, onUpdate, onOpenDuplicated, onClose, hideDuplicatedButton }: JobDetailProps) {
    const { data: appliedCompanyJobs = [], isLoading: loadingApplied } = useQuery({
        queryKey: ['appliedCompanyJobs', job.company, job.client],
        queryFn: async () => {
            if (!job.company) return [];
            const jobs = await jobsApi.getAppliedJobsByCompany(job.company, job.client || undefined);
            if (jobs.length > 60) {
                jobs.splice(60); // Limit to first X entries
                jobs[60 - 1].created = '...';
            }
            return jobs;
        },
        enabled: !!job.company,
        staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    });

    const contentRef = useRef<HTMLDivElement>(null);
    const savedCalcParams = useMemo(() => parseSalaryCalculationFromComments(job.comments), [job.comments]);
    const allSavedCalcParams = useMemo(() => parseAllSalaryCalculationsFromComments(job.comments), [job.comments]);
    const [showCalculator, setShowCalculator] = useState(false);

    // Auto-show calculator when switching to a job with saved calc params
    useEffect(() => {
        setShowCalculator(!!savedCalcParams);
    }, [job.id, savedCalcParams]);
    
    const formatDateTime = (d: string | null) => {
        if (!d) return '-';
        return new Date(d).toLocaleString(undefined, {
            year: 'numeric',
            month: 'numeric',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const isModified = (created: string | undefined | null, modified: string | undefined | null) => {
        if (!created || !modified) return false;
        const d1 = new Date(created);
        const d2 = new Date(modified);
        // Ignore difference under 5 minutes
        return Math.abs(d1.getTime() - d2.getTime()) >= 5 * 60 * 1000;
    };

    useEffect(() => {  // Scroll to top when job changes
        if (contentRef.current) {
            contentRef.current.scrollTop = 0;
        }
    }, [job]);

    const allJobSkills = [job.required_technologies, job.optional_technologies]
        .filter(Boolean)
        .join(', ');

    return (
        <div className="job-detail">
            <JobDetailHeader 
                job={job} 
                onCloseDuplicated={onClose} 
                onOpenDuplicated={hideDuplicatedButton ? undefined : onOpenDuplicated}
            />
            <div className="job-detail-scroll-wrapper">
                <div className="job-status-floating">
                    {STATE_FIELDS.filter(field => job[field as keyof Job] === true).map(status => (
                        <span key={status} className={`status-tag status-${status}`}>
                            {status.replace(/_/g, ' ')}
                        </span>
                    ))}
                </div>
                <div className="job-detail-content" ref={contentRef}>
                    <ul className="job-info">
                    {job.ai_enrich_error && (
                        <li className="info-row" style={{ color: 'red' }}>
                            Enrich Error: <span 
                                title="Click to copy" 
                                onClick={() => navigator.clipboard.writeText(job.ai_enrich_error!)}
                                style={{ cursor: 'pointer' }}>
                                {job.ai_enrich_error}
                            </span>
                            <button 
                                className="config-btn" 
                                style={{ marginLeft: '1rem', padding: '2px 8px', fontSize: '0.75rem' }}
                                onClick={() => onUpdate?.({ ai_enrich_error: null, ai_enriched: false })}>
                                Force Re-enrich
                            </button>
                        </li>
                    )}
                    {job.company && (
                        <li className="info-row">
                            Company: <span>{job.company}</span>
                            <AppliedJobsWarning 
                                appliedJobs={appliedCompanyJobs} 
                                loadingApplied={loadingApplied}/>
                        </li>
                    )}
                    {job.location && <li className="info-row">Location: <span>{job.location}</span></li>}
                    {job.modality && <li className="info-row">Modality: <span>{job.modality}</span></li>}
                    {job.salary && (
                        <li className="info-row job-salary-row">
                            Salary: <span className="salary-value-text">{job.salary}</span>
                            <SalaryActions 
                                onToggleCalculator={() => setShowCalculator(!showCalculator)} 
                                onUpdate={onUpdate}/>
                        </li>
                    )}
                    {(job.required_technologies || job.optional_technologies) && (
                        <li className="info-row">Skills:
                            <ul>
                                {job.required_technologies && (
                                    <li>
                                        Required:{' '}
                                        <SkillsList 
                                            skills={job.required_technologies} 
                                            allJobSkills={allJobSkills}
                                        />
                                    </li>
                                )}
                                {job.optional_technologies && (
                                    <li>
                                        Optional:{' '}
                                        <SkillsList 
                                            skills={job.optional_technologies} 
                                            allJobSkills={allJobSkills}
                                        />
                                    </li>
                                )}
                            </ul>
                        </li>
                    )}
                    {job.web_page && (
                        <li className="info-row">
                            Source: <span>{job.web_page}</span>
                            <ul>
                            {job.created && <li className="info-row"><span>{formatDateTime(job.created)}</span> created</li>}
                                {job.modified && isModified(job.created, job.modified) && <li className="info-row"><span>{formatDateTime(job.modified)}</span> modified</li>}
                            </ul>
                        </li>
                    )}
                    {job.client && <li className="info-row">Client: <span>{job.client}</span></li>}
                    {job.cv_match_percentage && (
                        <li className="info-row cv-match-row">
                            CV Match: <CvMatchBar percentage={job.cv_match_percentage} />
                        </li>
                    )}
                </ul>
                {showCalculator && <SalaryCalculator key={job.id} onClose={() => setShowCalculator(false)} job={job} onUpdate={onUpdate} initialParams={savedCalcParams} allSavedParams={allSavedCalcParams} />}
                {job.comments && (
                    <div className="job-comments">
                        <h3>Comments</h3>
                        <div className="markdown-content">
                            <ReactMarkdownCustom>{job.comments}</ReactMarkdownCustom>
                        </div>
                    </div>
                )}
                {job.markdown && (
                    <div className="job-markdown">
                        <div className="markdown-content">
                            <ReactMarkdownCustom>{job.markdown}</ReactMarkdownCustom>
                        </div>
                    </div>
                )}
            </div>
            </div>
        </div>
    );
}
