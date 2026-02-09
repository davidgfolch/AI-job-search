import { useRef, type Dispatch, type SetStateAction } from 'react';
import { useAutoResizeTextArea } from '../../common/hooks/useAutoResizeTextArea';

// Define explicit types for formState and setters extracted from useJobEditForm output structure
// This assumes formState and setters structure from useJobEditForm.ts
interface JobFormFieldsProps {
    mode: 'edit' | 'create';
    jobId?: number;
    showAllFields: boolean;
    formState: {
        title: string;
        location: string;
        url: string;
        webPage: string;
        markdown: string;
        comments: string;
        salary: string;
        company: string;
        client: string;
        requiredTechnologies: string;
        optionalTechnologies: string;
        [key: string]: any;
    };
    setters: {
        setTitle: Dispatch<SetStateAction<string>>;
        setLocation: Dispatch<SetStateAction<string>>;
        setUrl: Dispatch<SetStateAction<string>>;
        setWebPage: Dispatch<SetStateAction<string>>;
        setMarkdown: Dispatch<SetStateAction<string>>;
        setComments: Dispatch<SetStateAction<string>>;
        setSalary: Dispatch<SetStateAction<string>>;
        setCompany: Dispatch<SetStateAction<string>>;
        setClient: Dispatch<SetStateAction<string>>;
        setRequiredTechnologies: Dispatch<SetStateAction<string>>;
        setOptionalTechnologies: Dispatch<SetStateAction<string>>;
        [key: string]: any;
    };
    handleChange: (setter: Dispatch<SetStateAction<string>>, field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
    handleCreate: () => void;
}

export default function JobFormFields({
    mode, jobId, showAllFields,
    formState, setters, handleChange, handleCreate
}: JobFormFieldsProps) {
    const {
        title, location, url, webPage, markdown, comments, salary, company, client,
        requiredTechnologies, optionalTechnologies
    } = formState;
    const {
        setTitle, setLocation, setUrl, setWebPage, setMarkdown, setComments, setSalary,
        setCompany, setClient, setRequiredTechnologies, setOptionalTechnologies
    } = setters;
    // Ref for textarea auto-resize
    const commentsRef = useRef<HTMLTextAreaElement>(null);
    const markdownRef = useRef<HTMLTextAreaElement>(null);
    const requiredTechnologiesRef = useRef<HTMLTextAreaElement>(null);
    const optionalTechnologiesRef = useRef<HTMLTextAreaElement>(null);
    // Auto-resize hooks
    useAutoResizeTextArea(commentsRef, comments, [showAllFields, jobId]);
    useAutoResizeTextArea(markdownRef, markdown, [showAllFields, jobId]);
    useAutoResizeTextArea(requiredTechnologiesRef, requiredTechnologies, [showAllFields, jobId]);
    useAutoResizeTextArea(optionalTechnologiesRef, optionalTechnologies, [showAllFields, jobId]);
    const formIdPrefix = jobId ? `job-${jobId}` : 'job-new';
    return (
        <div className="form-fields">
            {(mode === 'create' || showAllFields) && (
                <div className="form-field">
                    <label htmlFor={`${formIdPrefix}-title`}>Title *</label>
                    <input type="text" 
                        id={`${formIdPrefix}-title`} name="title"
                        value={title} onChange={handleChange(setTitle, 'title')} 
                        placeholder="Job Title"
                        autoComplete="organization-title"
                    />
                </div>
            )}
            
            <div className="form-row">
                {(mode === 'create' || showAllFields) && (
                    <div className="form-field">
                        <label htmlFor={`${formIdPrefix}-company`}>Company *</label>
                        <input type="text" 
                            id={`${formIdPrefix}-company`} name="company"
                            value={company} onChange={handleChange(setCompany, 'company')} 
                            placeholder="Company Name"
                            autoComplete="organization"
                        />
                    </div>
                )}
                <div className="form-field">
                    <label htmlFor={`${formIdPrefix}-client`}>Client</label>
                    <input type="text" 
                        id={`${formIdPrefix}-client`} name="client"
                        value={client} onChange={handleChange(setClient, 'client')} 
                        placeholder="Client (if applicable)"
                        autoComplete="off"
                    />
                </div>
                {(mode === 'create' || showAllFields) && (
                    <div className="form-field">
                        <label htmlFor={`${formIdPrefix}-location`}>Location</label>
                        <input type="text" 
                            id={`${formIdPrefix}-location`} name="location"
                            value={location} onChange={handleChange(setLocation, 'location')} 
                            placeholder="Location"
                            autoComplete="address-level2"
                        />
                    </div>
                )}
            </div>

            <div className="form-field">
                <label htmlFor={`${formIdPrefix}-salary`}>Salary</label>
                <input type="text" 
                    id={`${formIdPrefix}-salary`} name="salary"
                    value={salary} onChange={handleChange(setSalary, 'salary')} 
                    placeholder="Salary range"
                    autoComplete="off"
                />
            </div>

            {(mode === 'create' || showAllFields) && (
                <div className="form-row">
                    <div className="form-field">
                        <label htmlFor={`${formIdPrefix}-url`}>URL</label>
                        <input type="text" 
                            id={`${formIdPrefix}-url`} name="url"
                            value={url} onChange={handleChange(setUrl, 'url')} 
                            placeholder="Job Link"
                            autoComplete="url"
                        />
                    </div>
                    <div className="form-field form-field-small">
                        <label htmlFor={`${formIdPrefix}-webPage`}>Source</label>
                        <input type="text" 
                            id={`${formIdPrefix}-webPage`} name="webPage"
                            value={webPage} onChange={handleChange(setWebPage, 'web_page')} 
                            placeholder="Source (e.g. LinkedIn, Manual)"
                            autoComplete="off"
                        />
                    </div>
                </div>
            )}
            {(showAllFields) && (
                <>
                <div className="form-field">
                    <label htmlFor={`${formIdPrefix}-requiredTechnologies`}>Required Skills</label>
                    <textarea ref={requiredTechnologiesRef} 
                        id={`${formIdPrefix}-requiredTechnologies`} name="requiredTechnologies"
                        value={requiredTechnologies} onChange={handleChange(setRequiredTechnologies, 'required_technologies')} 
                        style={{ maxHeight: '10rem' }} 
                        placeholder="Required Technologies (comma separated)"
                        autoComplete="off"
                    />
                </div>
                <div className="form-field">
                    <label htmlFor={`${formIdPrefix}-optionalTechnologies`}>Optional Skills</label>
                    <textarea ref={optionalTechnologiesRef} 
                        id={`${formIdPrefix}-optionalTechnologies`} name="optionalTechnologies"
                        value={optionalTechnologies} onChange={handleChange(setOptionalTechnologies, 'optional_technologies')} 
                        style={{ maxHeight: '10rem' }} 
                        placeholder="Optional Technologies (comma separated)"
                        autoComplete="off"
                    />
                </div>
                </>
            )}
            <div className="form-field">
                <label htmlFor={`${formIdPrefix}-comments`}>Comments</label>
                <textarea ref={commentsRef} 
                    id={`${formIdPrefix}-comments`} name="comments"
                    value={comments} onChange={handleChange(setComments, 'comments')} 
                    style={{ maxHeight: '10rem' }} 
                    placeholder="Add your comments here..." 
                    autoComplete="off"
                />
            </div>
            {(mode === 'create' || showAllFields) && (
                <div className="form-field">
                    <label htmlFor={`${formIdPrefix}-markdown`}>Description</label>
                    <textarea ref={markdownRef}
                        id={`${formIdPrefix}-markdown`} name="markdown"
                        value={markdown} onChange={handleChange(setMarkdown, 'markdown')} 
                        style={{ maxHeight: '10rem' }}
                        placeholder="Job Description (Markdown supported)"
                        autoComplete="off"
                    />
                </div>
            )}
            {mode === 'create' && (
                <div className="form-actions">
                    <button className="create-btn" onClick={handleCreate} disabled={!title || !company}>Create Job</button>
                </div>
            )}
        </div>
    );
}
