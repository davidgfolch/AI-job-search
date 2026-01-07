import { useState, useEffect, useRef } from 'react';
import type { Job } from '../api/jobs';
import { BOOLEAN_FILTERS } from '../config/filterConfig';
import './JobEditForm.css';

interface JobEditFormProps {
    job: Job | null;
    onUpdate: (data: Partial<Job>) => void;
    onCreate?: (data: Partial<Job>) => void;
    mode?: 'edit' | 'create';
}

export default function JobEditForm({ job, onUpdate, onCreate, mode = 'edit' }: JobEditFormProps) {
    const [title, setTitle] = useState('');
    const [location, setLocation] = useState('');
    const [url, setUrl] = useState('');
    const [webPage, setWebPage] = useState('Manual');
    const [markdown, setMarkdown] = useState('');
    const [comments, setComments] = useState('');
    const [salary, setSalary] = useState('');
    const [company, setCompany] = useState('');
    const [client, setClient] = useState('');
    // Local state for status fields to handle optimistic updates
    const [statusState, setStatusState] = useState<Record<string, boolean>>({});
    // Ref to track debounce timers for auto-save
    const debounceTimers = useRef<Record<string, number>>({});
    // Ref for textarea auto-resize
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    // Sync local state with job prop when it changes
    useEffect(() => {
        if (mode === 'edit' && job) {
            setTitle(job.title || '');
            setLocation(job.location || '');
            setUrl(job.url || '');
            setWebPage(job.web_page || '');
            setMarkdown(job.markdown || '');
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
        } else if (mode === 'create') {
            // Reset fields for create mode
            setTitle('');
            setLocation('');
            setUrl('');
            setWebPage('Manual');
            setMarkdown('');
            setComments('');
            setSalary('');
            setCompany('');
            setClient('');
            setStatusState({});
        }
    }, [job, mode]);
    const handleStatusToggle = (field: string) => {
        if (mode === 'edit' && job) {
            const newValue = !statusState[field];
            // Optimistically update local state
            setStatusState(prev => ({ ...prev, [field]: newValue }));
            // Send update to backend
            onUpdate({ [field]: newValue });
        } else if (mode === 'create') {
             setStatusState(prev => ({ ...prev, [field]: !prev[field] }));
        }
    };
    // Auto-save handler with debouncing
    const handleAutoSave = (field: string, value: string) => {
        if (mode === 'create') return; // Don't auto-save in create mode
        if (debounceTimers.current[field]) { // Clear existing timer for this field
            clearTimeout(debounceTimers.current[field]);
        }
        debounceTimers.current[field] = setTimeout(() => { // Set new timer
            onUpdate({ [field]: value });
        }, 1000); // 1 second debounce
    };
    const handleChange = (setter: React.Dispatch<React.SetStateAction<string>>, field: string) => (
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
    ) => {
        const value = e.target.value;
        setter(value);
        handleAutoSave(field, value);
    };
    useEffect(() => { // Auto-resize textarea based on content
        if (textareaRef.current) {
            // Reset height to auto to get the correct scrollHeight
            textareaRef.current.style.height = 'auto';
            // Set height to scrollHeight to fit content
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [comments, markdown]); // Resize on comments or markdown change
    useEffect(() => { // Clean up timers on unmount
        return () => {
            Object.values(debounceTimers.current).forEach(timer => clearTimeout(timer));
        };
    }, []);
    const handleCreate = () => {
        if (onCreate) {
            onCreate({title, company, location, salary, url, web_page: webPage,
                markdown, comments, client, ...statusState});
        }
    };
    if (mode === 'edit' && !job) {
        return (
            <div className="job-edit-form">
                <div className="no-selection">Select a job to edit</div>
            </div>
        );
    }
    return (
        <div className="job-edit-form">
            {mode === 'create' && <h2 className="form-title">Create New Job</h2>}
            <div className="status-form">
                <div className="status-pills">
                    {BOOLEAN_FILTERS.map((filter) => (
                        <button key={filter.key} className={`status-pill ${statusState[filter.key] ? 'active' : ''}`}
                            onClick={() => handleStatusToggle(filter.key)}>
                            {filter.label}
                        </button>
                    ))}
                </div>
            </div>
            <div className="form-fields">
                {mode === 'create' && (
                    <>
                        <div className="form-field">
                            <label htmlFor="title">Title *</label>
                            <input id="title" type="text" value={title}
                                onChange={handleChange(setTitle, 'title')} placeholder="Job Title"/>
                        </div>
                        <div className="form-field">
                            <label htmlFor="company">Company *</label>
                            <input id="company" type="text" value={company}
                                onChange={handleChange(setCompany, 'company')} placeholder="Company Name"/>
                        </div>
                    </>
                )}
                <div className="form-field">
                    <label htmlFor="location">Location</label>
                    <input id="location" type="text" value={location}
                        onChange={handleChange(setLocation, 'location')} placeholder="Location"/>
                </div>
                <div className="form-field">
                    <label htmlFor="salary">Salary</label>
                    <input id="salary" type="text" value={salary}
                        onChange={handleChange(setSalary, 'salary')} placeholder="Salary range"/>
                </div>
                {mode === 'create' && (
                    <>
                        <div className="form-field">
                            <label htmlFor="url">URL</label>
                            <input id="url" type="text" value={url}
                                onChange={handleChange(setUrl, 'url')} placeholder="Job Link"/>
                        </div>
                        <div className="form-field">
                            <label htmlFor="webPage">Source</label>
                            <input id="webPage" type="text" value={webPage}
                                onChange={handleChange(setWebPage, 'web_page')} placeholder="Source (e.g. LinkedIn, Manual)"/>
                        </div>
                    </>
                )}
                <div className="form-field">
                    <label htmlFor="client">Client</label>
                    <input id="client" type="text" value={client}
                        onChange={handleChange(setClient, 'client')} placeholder="Client (if applicable)"/>
                </div>
                <div className="form-field">
                    <label htmlFor="markdown">Description</label>
                    <textarea id="markdown" value={markdown} style={{ minHeight: '100px' }}
                        onChange={handleChange(setMarkdown, 'markdown')}
                        placeholder="Job Description (Markdown supported)"/>
                </div>
                <div className="form-field">
                    <label htmlFor="comments">Comments</label>
                    <textarea ref={textareaRef} id="comments" value={comments}
                        onChange={handleChange(setComments, 'comments')}
                        placeholder="Add your comments here..." />
                </div>
                {mode === 'create' && (
                    <div className="form-actions">
                        <button className="create-btn" onClick={handleCreate} disabled={!title || !company}>Create Job</button>
                    </div>
                )}
            </div>
        </div>
    );
}
