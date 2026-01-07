import { useState, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import ReactMarkdownCustom from './ReactMarkdownCustom';
import type { Job } from '../api/jobs';
import { jobsApi } from '../api/jobs';
import './JobDetail.css';
import './Filters.css';
import './FilterConfigurations.css';
import SalaryCalculator from './SalaryCalculator';
import { STATE_FIELDS } from '../hooks/contants';

interface JobDetailProps {
    job: Job;
    onUpdate?: (data: Partial<Job>) => void;
    onCreateNew?: () => void;
}

export default function JobDetail({ job, onUpdate, onCreateNew }: JobDetailProps) {
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
    const [showCalculator, setShowCalculator] = useState(false);
    const formatDate = (d: string | null) => !d ? '-' : new Date(d).toLocaleDateString();

    useEffect(() => {  // Scroll to top when job changes
        if (contentRef.current) {
            contentRef.current.scrollTop = 0;
        }
    }, [job]);

    return (
        <div className="job-detail">
            <div className="job-detail-header">
                <h2><a href={job.url || '#'} target="_blank" rel="noopener noreferrer" className="job-link">{job.title}</a></h2>
                {onCreateNew && (
                    <button className="create-job-btn" onClick={onCreateNew} title="Create New Job">
                        ➕ Create New
                    </button>
                )}
            </div>
            <div className="job-detail-content" ref={contentRef}>
                <div className="job-status-floating">
                    {STATE_FIELDS.filter(field => job[field as keyof Job] === true).map(status => (
                        <span key={status} className={`status-tag status-${status}`}>
                            {status.replace(/_/g, ' ')}
                        </span>
                    ))}
                </div>
                <ul className="job-info">
                    {job.company && (
                        <li className="info-row">
                            Company: <span>{job.company}</span>
                            {!loadingApplied && appliedCompanyJobs.length > 0 && (
                                <span className="applied-company-indicator">
                                    {' '}👉 ⚠️{' '}
                                    <a href={`/?ids=${appliedCompanyJobs.map(j => j.id).join(',')}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="already-applied-link"
                                        title="Open in new tab showing these specific jobs">
                                        already applied to {appliedCompanyJobs.length}
                                    </a>
                                    {appliedCompanyJobs.map(aj => (
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
                            )}
                        </li>
                    )}
                    {job.location && <li className="info-row">Location: <span>{job.location}</span></li>}
                    {job.salary && (
                        <li className="info-row job-salary-row">
                            Salary: <span className="salary-value-text">{job.salary}</span>
                            <button 
                                className="config-btn salary-toggle-btn"
                                onClick={() => setShowCalculator(!showCalculator)}>
                                🧮 Freelance
                            </button>
                            <button 
                                className="config-btn salary-toggle-btn"
                                onClick={() => window.open('https://tecalculo.com/calculadora-de-sueldo-neto', '_blank')}>
                                🧮 Gross year
                            </button>
                            {onUpdate && (
                                <button
                                    className="config-btn salary-toggle-btn salary-delete-btn"
                                    onClick={() => onUpdate({ salary: null })}
                                    title="Delete salary information">
                                    🗑️
                                </button>
                            )}
                        </li>
                    )}
                    {(job.required_technologies || job.optional_technologies) && (
                        <li className="info-row">Skills:
                            <ul>
                                {job.required_technologies && <li>Required: <span>{job.required_technologies}</span></li>}
                                {job.optional_technologies && <li>Optional: <span>{job.optional_technologies}</span></li>}
                            </ul>
                        </li>
                    )}
                    {job.web_page && (
                        <li className="info-row">
                            Source: <span>{job.web_page}</span>
                            <ul>
                                {job.created && <li className="info-row"><span>{formatDate(job.created)}</span> created</li>}
                                {job.modified && formatDate(job.modified) !== formatDate(job.created) && <li className="info-row"><span>{formatDate(job.modified)}</span> modified</li>}
                            </ul>
                        </li>
                    )}
                    {job.client && <li className="info-row">Client: <span>{job.client}</span></li>}
                    {job.cv_match_percentage && <li className="info-row">CV Match: <span>{job.cv_match_percentage}%</span></li>}
                </ul>
                
                {showCalculator && <SalaryCalculator onClose={() => setShowCalculator(false)} />}

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
    );
}
