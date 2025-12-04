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
                <div className="job-info">
                    {job.company && <div className="info-row"><strong>Company:</strong> {job.company}</div>}
                    {job.location && <div className="info-row"><strong>Location:</strong> {job.location}</div>}
                    {job.salary && <div className="info-row"><strong>Salary:</strong> {job.salary}</div>}
                    {job.required_technologies && (<div className="info-row"><strong>Required skills:</strong> {job.required_technologies}</div>)}
                    {job.optional_technologies && (<div className="info-row"><strong>Optional skills:</strong> {job.optional_technologies}</div>)}

                    {job.created && <div className="info-row"><strong>Created:</strong> {formatDate(job.created)}</div>}
                    {job.modified && <div className="info-row"><strong>Modified:</strong> {formatDate(job.modified)}</div>}

                    {job.id && <div className="info-row"><strong>ID:</strong> {job.id}</div>}
                    {job.web_page && <div className="info-row"><strong>Source:</strong> {job.web_page}</div>}
                    {job.client && <div className="info-row"><strong>Client:</strong> {job.client}</div>}
                    {job.cv_match_percentage && <div className="info-row"><strong>CV Match:</strong> {job.cv_match_percentage}%</div>}
                </div>
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
