import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import type { Job, AppliedCompanyJob } from '../api/jobs';
import { jobsApi } from '../api/jobs';
import './JobDetail.css';

interface JobDetailProps {
    job: Job;
}

export default function JobDetail({ job }: JobDetailProps) {
    const [appliedCompanyJobs, setAppliedCompanyJobs] = useState<AppliedCompanyJob[]>([]);
    const [loadingApplied, setLoadingApplied] = useState(false);

    useEffect(() => {
        const fetchAppliedJobs = async () => {
            if (!job.company) {
                setAppliedCompanyJobs([]);
                return;
            }

            console.log('Fetching applied jobs for company:', job.company, 'Client:', job.client);
            setLoadingApplied(true);
            try {
                const jobs = await jobsApi.getAppliedJobsByCompany(job.company, job.client || undefined);
                console.log('Applied company jobs response:', jobs);
                setAppliedCompanyJobs(jobs);
            } catch (error) {
                console.error('Error fetching applied company jobs:', error);
                setAppliedCompanyJobs([]);
            } finally {
                setLoadingApplied(false);
            }
        };
        fetchAppliedJobs();
    }, [job.company, job.client]);

    const formatDate = (date: string | null) => {
        if (!date) return '-';
        return new Date(date).toLocaleDateString();
    };

    return (
        <div className="job-detail">
            <div className="job-detail-header">
                <h2><a href={job.url || '#'} target="_blank" rel="noopener noreferrer" className="job-link">{job.title}</a></h2>
            </div>

            <div className="job-detail-content">
                <ul className="job-info">
                    {job.company && (
                        <li className="info-row">
                            Company: <span>{job.company}</span>
                            {!loadingApplied && appliedCompanyJobs.length > 0 && (
                                <span className="applied-company-indicator">
                                    {' '}👉 ⚠️ already applied ({appliedCompanyJobs.length})
                                    {appliedCompanyJobs.map(aj => (
                                        <span key={aj.id} className="applied-date">
                                            {' '}📅 {aj.created ? new Date(aj.created).toLocaleDateString('en-GB', {
                                                day: '2-digit',
                                                month: '2-digit',
                                                year: '2-digit'
                                            }).replace(/\//g, '-') : '-'}
                                        </span>
                                    ))}
                                </span>
                            )}
                        </li>
                    )}
                    {job.location && <li className="info-row">Location: <span>{job.location}</span></li>}
                    {job.salary && <li className="info-row">Salary: <span>{job.salary}</span></li>}

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
                {job.comments && (
                    <div className="job-comments">
                        <h3>Comments</h3>
                        <div className="markdown-content"><ReactMarkdown>{job.comments}</ReactMarkdown></div>
                    </div>
                )}
                {job.markdown && (
                    <div className="job-markdown">
                        <div className="markdown-content"><ReactMarkdown>{job.markdown}</ReactMarkdown></div>
                    </div>
                )}
            </div>
        </div>
    );
}
