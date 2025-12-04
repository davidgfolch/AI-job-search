import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import type { Job, JobListParams } from '../api/jobs';
import './JobDetail.css';

interface JobDetailProps {
    job: Job;
    filters: JobListParams;
    onSeen: () => void;
    onApplied: () => void;
    onDiscarded: () => void;
    onClosed: () => void;
    onIgnore: () => void;
    onNext: () => void;
    onPrevious: () => void;
    hasNext: boolean;
    hasPrevious: boolean;
}

export default function JobDetail({ job, filters, onSeen, onApplied, onDiscarded, onClosed, onIgnore, onNext, onPrevious, hasNext, hasPrevious }: JobDetailProps) {
    const [copied, setCopied] = useState(false);

    const formatDate = (date: string | null) => {
        if (!date) return '-';
        return new Date(date).toLocaleDateString();
    };

    const generatePermalink = () => {
        const params = new URLSearchParams();
        params.set('jobId', job.id.toString());

        // Add current filters to permalink
        if (filters.search) params.set('search', filters.search);
        if (filters.order) params.set('order', filters.order);
        if (filters.days_old) params.set('days_old', filters.days_old.toString());
        if (filters.salary) params.set('salary', filters.salary);
        if (filters.sql_filter) params.set('sql_filter', filters.sql_filter);

        // Add boolean filters
        const booleanFilters: (keyof JobListParams)[] = [
            'flagged', 'like', 'ignored', 'seen', 'applied', 'discarded', 'closed',
            'interview_rh', 'interview', 'interview_tech', 'interview_technical_test',
            'interview_technical_test_done', 'ai_enriched', 'easy_apply'
        ];
        booleanFilters.forEach(key => {
            if (filters[key] !== undefined) {
                params.set(key, String(filters[key]));
            }
        });

        return `${window.location.origin}${window.location.pathname}?${params.toString()}`;
    };

    const handleCopyPermalink = () => {
        const permalink = generatePermalink();
        navigator.clipboard.writeText(permalink).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        });
    };

    return (
        <div className="job-detail">
            <div className="job-detail-header">
                <h2><a href={job.url || '#'} target="_blank" rel="noopener noreferrer" className="job-link">{job.title}</a></h2>
                <div className="header-actions">
                    <button className="header-button state-button seen-button" onClick={onSeen} title="Mark as seen">👁️</button>
                    <button className="header-button state-button applied-button" onClick={onApplied} title="Mark as applied">✅</button>
                    <button className="header-button state-button discarded-button" onClick={onDiscarded} title="Mark as discarded">❌</button>
                    <button className="header-button state-button closed-button" onClick={onClosed} title="Mark as closed">🔒</button>
                    <button className="header-button state-button ignore-button" onClick={onIgnore} title="Mark as ignored">🚫</button>
                    <div className="button-separator"></div>
                    <button className="header-button copy-button" onClick={handleCopyPermalink} title="Copy permalink to clipboard">
                        {copied ? '✓' : '🔗'}
                    </button>
                    <button className="header-button nav-button" onClick={onPrevious} disabled={!hasPrevious} title="Previous job">⏮</button>
                    <button className="header-button nav-button" onClick={onNext} disabled={!hasNext} title="Next job">⏭</button>
                </div>
            </div>

            <div className="job-detail-content">
                <ul className="job-info">
                    {job.company && <li className="info-row">Company: <span>{job.company}</span></li>}
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
