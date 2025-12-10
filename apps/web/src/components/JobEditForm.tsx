import { useState, useEffect, useRef } from 'react';
import type { Job } from '../api/jobs';
import { BOOLEAN_FILTERS } from '../config/filterConfig';
import './JobEditForm.css';

interface JobEditFormProps {
    job: Job | null;
    onUpdate: (data: Partial<Job>) => void;
}



export default function JobEditForm({ job, onUpdate }: JobEditFormProps) {
    const [comments, setComments] = useState(job?.comments || '');
    const [salary, setSalary] = useState(job?.salary || '');
    const [company, setCompany] = useState(job?.company || '');
    const [client, setClient] = useState(job?.client || '');

    // Local state for status fields to handle optimistic updates
    const [statusState, setStatusState] = useState<Record<string, boolean>>({});

    // Ref to track debounce timers for auto-save
    const debounceTimers = useRef<Record<string, number>>({});

    // Sync local state with job prop when it changes
    useEffect(() => {
        if (job) {
            setComments(job.comments || '');
            setSalary(job.salary || '');
            setCompany(job.company || '');
            setClient(job.client || '');

            // Update status state from job
            const newStatusState: Record<string, boolean> = {};
            BOOLEAN_FILTERS.forEach(filter => {
                newStatusState[filter.key] = job[filter.key as keyof Job] as boolean;
            });
            setStatusState(newStatusState);
        }
    }, [job]);

    const handleStatusToggle = (field: string) => {
        if (job) {
            const newValue = !statusState[field];
            // Optimistically update local state
            setStatusState(prev => ({ ...prev, [field]: newValue }));
            // Send update to backend
            onUpdate({ [field]: newValue });
        }
    };

    // Auto-save handler with debouncing
    const handleAutoSave = (field: string, value: string) => {
        // Clear existing timer for this field
        if (debounceTimers.current[field]) {
            clearTimeout(debounceTimers.current[field]);
        }

        // Set new timer
        debounceTimers.current[field] = setTimeout(() => {
            onUpdate({ [field]: value });
        }, 1000); // 1 second debounce
    };

    const handleCommentsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const value = e.target.value;
        setComments(value);
        handleAutoSave('comments', value);
    };

    const handleSalaryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setSalary(value);
        handleAutoSave('salary', value);
    };

    const handleCompanyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setCompany(value);
        handleAutoSave('company', value);
    };

    const handleClientChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setClient(value);
        handleAutoSave('client', value);
    };

    // Clean up timers on unmount
    useEffect(() => {
        return () => {
            Object.values(debounceTimers.current).forEach(timer => clearTimeout(timer));
        };
    }, []);

    if (!job) {
        return (
            <div className="job-edit-form">
                <div className="no-selection">Select a job to edit</div>
            </div>
        );
    }

    return (
        <div className="job-edit-form">
            <div className="status-form">
                <div className="status-pills">
                    {BOOLEAN_FILTERS.map((filter) => (
                        <button
                            key={filter.key}
                            className={`status-pill ${statusState[filter.key] ? 'active' : ''}`}
                            onClick={() => handleStatusToggle(filter.key)}
                        >
                            {filter.label}
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
                        onChange={handleCommentsChange}
                        rows={4}
                        placeholder="Auto-saves as you type..."
                    />
                </div>

                <div className="form-field">
                    <label htmlFor="salary">Salary</label>
                    <input
                        id="salary"
                        type="text"
                        value={salary}
                        onChange={handleSalaryChange}
                        placeholder="Auto-saves as you type..."
                    />
                </div>

                <div className="form-field">
                    <label htmlFor="company">Company</label>
                    <input
                        id="company"
                        type="text"
                        value={company}
                        onChange={handleCompanyChange}
                        placeholder="Auto-saves as you type..."
                    />
                </div>

                <div className="form-field">
                    <label htmlFor="client">Client</label>
                    <input
                        id="client"
                        type="text"
                        value={client}
                        onChange={handleClientChange}
                        placeholder="Auto-saves as you type..."
                    />
                </div>
            </div>
        </div>
    );
}
