import { useState } from 'react';
import type { Job } from '../api/jobs';
import './JobDetail.css';

interface JobDetailProps {
    job: Job;
    onUpdate: (data: Partial<Job>) => void;
}

const STATUS_FIELDS = [
    'flagged',
    'like',
    'ignored',
    'seen',
    'applied',
    'discarded',
    'closed',
    'ai_enriched',
];

export default function JobDetail({ job, onUpdate }: JobDetailProps) {
    const [comments, setComments] = useState(job.comments || '');
    const [salary, setSalary] = useState(job.salary || '');
    const [company, setCompany] = useState(job.company || '');
    const [client, setClient] = useState(job.client || '');

    const handleStatusToggle = (field: string) => {
        onUpdate({ [field]: !job[field as keyof Job] });
    };

    const handleSave = () => {
        onUpdate({
            comments,
            salary,
            company,
            client,
        });
    };

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
                <div className="info-row">
                    <strong>ID:</strong> {job.id}
                </div>
                <div className="info-row">
                    <strong>Source:</strong> {job.web_page}
                </div>
                <div className="info-row">
                    <strong>Location:</strong> {job.location || '-'}
                </div>
                <div className="info-row">
                    <strong>Created:</strong> {formatDate(job.created)}
                </div>
                {job.cv_match_percentage !== null && job.cv_match_percentage >= 0 && (
                    <div className="info-row">
                        <strong>CV Match:</strong> {job.cv_match_percentage}%
                    </div>
                )}
            </div>

            <div className="status-form">
                <h3>Status</h3>
                <div className="status-pills">
                    {STATUS_FIELDS.map((field) => (
                        <button
                            key={field}
                            className={`status-pill ${job[field as keyof Job] ? 'active' : ''}`}
                            onClick={() => handleStatusToggle(field)}
                        >
                            {field.replace(/_/g, ' ')}
                        </button>
                    ))}
                </div>
            </div>

            <div className="form-fields">
                <div className="form-field">
                    <label htmlFor="comments">Comments</label>
                    <textarea
                        id="comments"
                        value={comments}
                        onChange={(e) => setComments(e.target.value)}
                        rows={4}
                    />
                </div>

                <div className="form-field">
                    <label htmlFor="salary">Salary</label>
                    <input
                        id="salary"
                        type="text"
                        value={salary}
                        onChange={(e) => setSalary(e.target.value)}
                    />
                </div>

                <div className="form-field">
                    <label htmlFor="company">Company</label>
                    <input
                        id="company"
                        type="text"
                        value={company}
                        onChange={(e) => setCompany(e.target.value)}
                    />
                </div>

                <div className="form-field">
                    <label htmlFor=" client">Client</label>
                    <input
                        id="client"
                        type="text"
                        value={client}
                        onChange={(e) => setClient(e.target.value)}
                    />
                </div>

                <button className="save-btn" onClick={handleSave}>
                    Save Changes
                </button>
            </div>

            {job.required_technologies && (
                <div className="technologies">
                    <h3>Required Technologies</h3>
                    <p>{job.required_technologies}</p>
                </div>
            )}

            {job.optional_technologies && (
                <div className="technologies">
                    <h3>Optional Technologies</h3>
                    <p>{job.optional_technologies}</p>
                </div>
            )}

            {job.markdown && (
                <div className="job-markdown">
                    <h3>Description</h3>
                    <div className="markdown-content">
                        {job.markdown}
                    </div>
                </div>
            )}
        </div>
    );
}
