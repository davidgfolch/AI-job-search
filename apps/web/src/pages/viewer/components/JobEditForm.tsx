import { useRef } from 'react';
import type { Job } from '../api/ViewerApi';
import { BOOLEAN_FILTERS } from '../constants';
import { useAutoResizeTextArea } from '../../common/hooks/useAutoResizeTextArea';
import { useJobEditForm } from './hooks/useJobEditForm';
import './JobEditForm.css';

interface JobEditFormProps {
    job: Job | null;
    onUpdate: (data: Partial<Job>) => void;
    onCreate?: (data: Partial<Job>) => void;
    mode?: 'edit' | 'create';
}

export default function JobEditForm({ job, onUpdate, onCreate, mode = 'edit' }: JobEditFormProps) {
    const { 
        formState, 
        setters, 
        actions 
    } = useJobEditForm({ job, onUpdate, onCreate, mode });

    const {
        title, location, url, webPage, markdown, comments, salary, company, client,
        requiredTechnologies, optionalTechnologies, statusState, showAllFields
    } = formState;

    const {
        setTitle, setLocation, setUrl, setWebPage, setMarkdown, setComments, setSalary,
        setCompany, setClient, setRequiredTechnologies, setOptionalTechnologies, setShowAllFields
    } = setters;

    const { handleStatusToggle, handleChange, handleCreate } = actions;

    // Ref for textarea auto-resize
    const commentsRef = useRef<HTMLTextAreaElement>(null);
    const markdownRef = useRef<HTMLTextAreaElement>(null);
    const requiredTechnologiesRef = useRef<HTMLTextAreaElement>(null);
    const optionalTechnologiesRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize hooks
    useAutoResizeTextArea(commentsRef, comments, [showAllFields, job?.id]);
    useAutoResizeTextArea(markdownRef, markdown, [showAllFields, job?.id]);
    useAutoResizeTextArea(requiredTechnologiesRef, requiredTechnologies, [showAllFields, job?.id]);
    useAutoResizeTextArea(optionalTechnologiesRef, optionalTechnologies, [showAllFields, job?.id]);

    if (mode === 'edit' && !job) return <div className="job-edit-form"><div className="no-selection">Select a job to edit</div></div>;

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
                            onClick={() => handleStatusToggle(filter.key as string)}>
                            {filter.label}
                        </button>
                    ))}
                </div>
            </div>
            <div className="form-fields">
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
                {(showAllFields) && (
                    <>
                    <div className="form-field">
                        <label htmlFor="requiredTechnologies">Required Skills</label>
                        <textarea ref={requiredTechnologiesRef} id="requiredTechnologies" value={requiredTechnologies} style={{ maxHeight: '10rem' }} onChange={handleChange(setRequiredTechnologies, 'required_technologies')} placeholder="Required Technologies (comma separated)"/>
                    </div>
                    <div className="form-field">
                        <label htmlFor="optionalTechnologies">Optional Skills</label>
                        <textarea ref={optionalTechnologiesRef} id="optionalTechnologies" value={optionalTechnologies} style={{ maxHeight: '10rem' }} onChange={handleChange(setOptionalTechnologies, 'optional_technologies')} placeholder="Optional Technologies (comma separated)"/>
                    </div>
                    </>
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
