import { useState, useEffect, useRef } from 'react';
import type { Job } from '../api/jobs';
import { BOOLEAN_FILTERS } from '../config/filterConfig';
import { useAutoResizeTextArea } from '../hooks/useAutoResizeTextArea';
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
    const [showAllFields, setShowAllFields] = useState(mode === 'create');
    // Ref to track debounce timers for auto-save
    const debounceTimers = useRef<Record<string, number>>({});
    // Ref for textarea auto-resize
    const commentsRef = useRef<HTMLTextAreaElement>(null);
    const markdownRef = useRef<HTMLTextAreaElement>(null);
    // Track previous job ID to detect job switches vs updates
    const previousJobId = useRef<number | null>(null);
    // Sync local state with job prop when it changes
    useEffect(() => {
        if (mode === 'create') {
            setShowAllFields(true);
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
            previousJobId.current = null;
        } else if (mode === 'edit' && job) {
            if (previousJobId.current !== job.id) { // Only reset showAllFields if we switched to a different job
                setShowAllFields(false);
                previousJobId.current = job.id;
            }
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
    useEffect(() => { // Clean up timers on unmount
        return () => { Object.values(debounceTimers.current).forEach(timer => clearTimeout(timer)); };
    }, []);
    const handleCreate = () => {
        if (onCreate) {
            onCreate({title, company, location, salary, url, web_page: webPage,
                markdown, comments, client, ...statusState});
        }
    };
    
    // Auto-resize hooks
    useAutoResizeTextArea(commentsRef, comments, [showAllFields, job?.id]);
    useAutoResizeTextArea(markdownRef, markdown, [showAllFields, job?.id]);

    if (mode === 'edit' && !job) return <div className="job-edit-form"><div className="no-selection">Select a job to edit</div></div>;

    const hideLabels = mode === 'create' || showAllFields;
    return (
        <div className="job-edit-form">
            {mode === 'create' && <h2 className="form-title">Create New Job</h2>}
            {mode === 'edit' && (
                <div className="toggle-edit-btn">
                    <button onClick={() => setShowAllFields(!showAllFields)} className="create-btn">
                        {showAllFields ? 'Edit Less' : 'Edit All'}
                    </button>
                </div>
            )}
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
            <div className={`form-fields ${hideLabels ? 'hide-labels' : ''}`}>
                {(mode === 'create' || showAllFields) && (
                    <div className="form-field">
                        <label htmlFor="title">Title *</label>
                        <input id="title" type="text" value={title} onChange={handleChange(setTitle, 'title')} placeholder="Job Title"/>
                    </div>
                )}
                
                <div className="form-row">
                    {(mode === 'create' || showAllFields) && (
                        <div className="form-field">
                            <label htmlFor="company">Company *</label>
                            <input id="company" type="text" value={company} onChange={handleChange(setCompany, 'company')} placeholder="Company Name"/>
                        </div>
                    )}
                    <div className="form-field">
                        <label htmlFor="client">Client</label>
                        <input id="client" type="text" value={client} onChange={handleChange(setClient, 'client')} placeholder="Client (if applicable)"/>
                    </div>
                    {(mode === 'create' || showAllFields) && (
                        <div className="form-field">
                            <label htmlFor="location">Location</label>
                            <input id="location" type="text" value={location} onChange={handleChange(setLocation, 'location')} placeholder="Location"/>
                        </div>
                    )}
                </div>

                <div className="form-field">
                    <label htmlFor="salary">Salary</label>
                    <input id="salary" type="text" value={salary} onChange={handleChange(setSalary, 'salary')} placeholder="Salary range"/>
                </div>

                {(mode === 'create' || showAllFields) && (
                    <div className="form-row">
                        <div className="form-field">
                            <label htmlFor="url">URL</label>
                            <input id="url" type="text" value={url} onChange={handleChange(setUrl, 'url')} placeholder="Job Link"/>
                        </div>
                        <div className="form-field form-field-small">
                            <label htmlFor="webPage">Source</label>
                            <input id="webPage" type="text" value={webPage} onChange={handleChange(setWebPage, 'web_page')} placeholder="Source (e.g. LinkedIn, Manual)"/>
                        </div>
                    </div>
                )}
                <div className="form-field">
                    <label htmlFor="comments">Comments</label>
                    <textarea ref={commentsRef} id="comments" value={comments} style={{ maxHeight: '10rem' }} onChange={handleChange(setComments, 'comments')} placeholder="Add your comments here..." />
                </div>
                {(mode === 'create' || showAllFields) && (
                    <div className="form-field">
                        <label htmlFor="markdown">Description</label>
                        <textarea ref={markdownRef} id="markdown" value={markdown} style={{ maxHeight: '10rem' }} onChange={handleChange(setMarkdown, 'markdown')} placeholder="Job Description (Markdown supported)"/>
                    </div>
                )}
                {mode === 'create' && (
                    <div className="form-actions">
                        <button className="create-btn" onClick={handleCreate} disabled={!title || !company}>Create Job</button>
                    </div>
                )}
            </div>
        </div>
    );
}