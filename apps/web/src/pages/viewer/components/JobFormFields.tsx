import { useRef, type Dispatch, type SetStateAction } from 'react';
import { useAutoResizeTextArea } from '../../common/hooks/useAutoResizeTextArea';
import { FormField } from '../../common/components/core/FormField';

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
                <FormField id={`${formIdPrefix}-title`} label="Title *">
                    <input type="text" 
                        id={`${formIdPrefix}-title`} name="title"
                        value={title} onChange={handleChange(setTitle, 'title')} 
                        placeholder="Job Title"
                        autoComplete="organization-title"
                    />
                </FormField>
            )}
            
            <div className="form-row">
                {(mode === 'create' || showAllFields) && (
                    <FormField id={`${formIdPrefix}-company`} label="Company *">
                        <input type="text" 
                            id={`${formIdPrefix}-company`} name="company"
                            value={company} onChange={handleChange(setCompany, 'company')} 
                            placeholder="Company Name"
                            autoComplete="organization"
                        />
                    </FormField>
                )}
                <FormField id={`${formIdPrefix}-client`} label="Client">
                    <input type="text" 
                        id={`${formIdPrefix}-client`} name="client"
                        value={client} onChange={handleChange(setClient, 'client')} 
                        placeholder="Client (if applicable)"
                        autoComplete="off"
                    />
                </FormField>
                {(mode === 'create' || showAllFields) && (
                    <FormField id={`${formIdPrefix}-location`} label="Location">
                        <input type="text" 
                            id={`${formIdPrefix}-location`} name="location"
                            value={location} onChange={handleChange(setLocation, 'location')} 
                            placeholder="Location"
                            autoComplete="address-level2"
                        />
                    </FormField>
                )}
            </div>

            <FormField id={`${formIdPrefix}-salary`} label="Salary">
                <input type="text" 
                    id={`${formIdPrefix}-salary`} name="salary"
                    value={salary} onChange={handleChange(setSalary, 'salary')} 
                    placeholder="Salary range"
                    autoComplete="off"
                />
            </FormField>

            {(mode === 'create' || showAllFields) && (
                <div className="form-row">
                    <FormField id={`${formIdPrefix}-url`} label="URL">
                        <input type="text" 
                            id={`${formIdPrefix}-url`} name="url"
                            value={url} onChange={handleChange(setUrl, 'url')} 
                            placeholder="Job Link"
                            autoComplete="url"
                        />
                    </FormField>
                    <FormField id={`${formIdPrefix}-webPage`} label="Source" className="form-field form-field-small">
                        <input type="text" 
                            id={`${formIdPrefix}-webPage`} name="webPage"
                            value={webPage} onChange={handleChange(setWebPage, 'web_page')} 
                            placeholder="Source (e.g. LinkedIn, Manual)"
                            autoComplete="off"
                        />
                    </FormField>
                </div>
            )}
            {(showAllFields) && (
                <>
                <FormField id={`${formIdPrefix}-requiredTechnologies`} label="Required Skills">
                    <textarea ref={requiredTechnologiesRef} 
                        id={`${formIdPrefix}-requiredTechnologies`} name="requiredTechnologies"
                        value={requiredTechnologies} onChange={handleChange(setRequiredTechnologies, 'required_technologies')} 
                        style={{ maxHeight: '10rem' }} 
                        placeholder="Required Technologies (comma separated)"
                        autoComplete="off"
                    />
                </FormField>
                <FormField id={`${formIdPrefix}-optionalTechnologies`} label="Optional Skills">
                    <textarea ref={optionalTechnologiesRef} 
                        id={`${formIdPrefix}-optionalTechnologies`} name="optionalTechnologies"
                        value={optionalTechnologies} onChange={handleChange(setOptionalTechnologies, 'optional_technologies')} 
                        style={{ maxHeight: '10rem' }} 
                        placeholder="Optional Technologies (comma separated)"
                        autoComplete="off"
                    />
                </FormField>
                </>
            )}
            <FormField id={`${formIdPrefix}-comments`} label="Comments">
                <textarea ref={commentsRef} 
                    id={`${formIdPrefix}-comments`} name="comments"
                    value={comments} onChange={handleChange(setComments, 'comments')} 
                    style={{ maxHeight: '10rem' }} 
                    placeholder="Add your comments here..." 
                    autoComplete="off"
                />
            </FormField>
            {(mode === 'create' || showAllFields) && (
                <FormField id={`${formIdPrefix}-markdown`} label="Description">
                    <textarea ref={markdownRef}
                        id={`${formIdPrefix}-markdown`} name="markdown"
                        value={markdown} onChange={handleChange(setMarkdown, 'markdown')} 
                        style={{ maxHeight: '10rem' }}
                        placeholder="Job Description (Markdown supported)"
                        autoComplete="off"
                    />
                </FormField>
            )}
            {mode === 'create' && (
                <div className="form-actions">
                    <button className="create-btn" onClick={handleCreate} disabled={!title || !company}>Create Job</button>
                </div>
            )}
        </div>
    );
}
