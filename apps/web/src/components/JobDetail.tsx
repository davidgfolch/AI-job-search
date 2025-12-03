import ReactMarkdown from 'react-markdown';
import type { Job } from '../api/jobs';
import './JobDetail.css';

interface JobDetailProps {
    job: Job;
}

export default function JobDetail({ job }: JobDetailProps) {
    const formatDate = (date: string | null) => {
        if (!date) return '-';
        return new Date(date).toLocaleDateString();
    };

    return (
        <div className="job-detail">
            <div className="job-detail-header">
                <h2>{job.title}</h2>
                <a href={job.url || '#'} target="_blank" rel="noopener noreferrer" className="job-link">
                    View Job →
                </a>
            </div>

            <div className="job-info">
                <div className="info-row"><strong>ID:</strong> {job.id}</div>
                <div className="info-row"><strong>Source:</strong> {job.web_page}</div>
                <div className="info-row"><strong>Location:</strong> {job.location || '-'}</div>
                <div className="info-row"><strong>Created:</strong> {formatDate(job.created)}</div>
                <div className="info-row"><strong>Modified:</strong> {formatDate(job.modified)}</div>
                {job.cv_match_percentage !== null && job.cv_match_percentage >= 0 && (
                    <div className="info-row"><strong>CV Match:</strong> {job.cv_match_percentage}%</div>
                )}
                {job.company && <div className="info-row"><strong>Company:</strong> {job.company}</div>}
                {job.client && <div className="info-row"><strong>Client:</strong> {job.client}</div>}
                {job.salary && <div className="info-row"><strong>Salary:</strong> {job.salary}</div>}
            </div>

            {job.required_technologies && (
                <div className="technologies"><h3>Required Technologies</h3><p>{job.required_technologies}</p></div>
            )}

            {job.optional_technologies && (
                <div className="technologies"><h3>Optional Technologies</h3><p>{job.optional_technologies}</p></div>
            )}

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
    );
}
