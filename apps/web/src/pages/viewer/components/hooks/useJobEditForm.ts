import { useState, useEffect, useRef } from 'react';
import type { Job } from '../../api/ViewerApi';
import { BOOLEAN_FILTER_KEYS } from '../../constants';

interface UseJobEditFormProps {
    job: Job | null;
    onUpdate: (data: Partial<Job>) => void;
    onCreate?: (data: Partial<Job>) => void;
    mode: 'edit' | 'create';
}

export function useJobEditForm({ job, onUpdate, onCreate, mode }: UseJobEditFormProps) {
    const [title, setTitle] = useState('');
    const [location, setLocation] = useState('');
    const [url, setUrl] = useState('');
    const [webPage, setWebPage] = useState('Manual');
    const [markdown, setMarkdown] = useState('');
    const [comments, setComments] = useState('');
    const [salary, setSalary] = useState('');
    const [company, setCompany] = useState('');
    const [client, setClient] = useState('');
    const [requiredTechnologies, setRequiredTechnologies] = useState('');
    const [optionalTechnologies, setOptionalTechnologies] = useState('');
    
    // Local state for status fields to handle optimistic updates
    const [statusState, setStatusState] = useState<Record<string, boolean>>({});
    const [showAllFields, setShowAllFields] = useState(mode === 'create');
    
    // Ref to track debounce timers for auto-save
    const debounceTimers = useRef<Record<string, number>>({});
    
    // Track previous job ID to detect job switches vs updates
    const previousJobId = useRef<number | null>(null);

    // Sync local state with job prop when it changes
    useEffect(() => {
        if (mode === 'create') {
            setShowAllFields(true);
            resetForm();
            setStatusState({});
            previousJobId.current = null;
        } else if (mode === 'edit' && job) {
            if (previousJobId.current !== job.id) {
                setShowAllFields(false);
                previousJobId.current = job.id;
            }
            populateForm(job);
            
            // Update status state from job
            const newStatusState: Record<string, boolean> = {};
            BOOLEAN_FILTER_KEYS.forEach(key => {
                newStatusState[key] = job[key as keyof Job] as boolean;
            });
            setStatusState(newStatusState);
        }
    }, [job, mode]);

    const resetForm = () => {
        setTitle('');
        setLocation('');
        setUrl('');
        setWebPage('Manual');
        setMarkdown('');
        setComments('');
        setSalary('');
        setCompany('');
        setClient('');
        setRequiredTechnologies('');
        setOptionalTechnologies('');
    };

    const populateForm = (job: Job) => {
        setTitle(job.title || '');
        setLocation(job.location || '');
        setUrl(job.url || '');
        setWebPage(job.web_page || '');
        setMarkdown(job.markdown || '');
        setComments(job.comments || '');
        setSalary(job.salary || '');
        setCompany(job.company || '');
        setClient(job.client || '');
        setRequiredTechnologies(job.required_technologies || '');
        setOptionalTechnologies(job.optional_technologies || '');
    };

    const handleStatusToggle = (field: string) => {
        if (mode === 'edit' && job) {
            const newValue = !statusState[field];
            setStatusState(prev => ({ ...prev, [field]: newValue }));
            onUpdate({ [field]: newValue });
        } else if (mode === 'create') {
             setStatusState(prev => ({ ...prev, [field]: !prev[field] }));
        }
    };

    const handleAutoSave = (field: string, value: string) => {
        if (mode === 'create') return;
        if (debounceTimers.current[field]) {
            clearTimeout(debounceTimers.current[field]);
        }
        debounceTimers.current[field] = setTimeout(() => {
            onUpdate({ [field]: value });
        }, 1000);
    };

    const handleChange = (setter: React.Dispatch<React.SetStateAction<string>>, field: string) => (
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
    ) => {
        const value = e.target.value;
        setter(value);
        handleAutoSave(field, value);
    };

    useEffect(() => {
        return () => { Object.values(debounceTimers.current).forEach(timer => clearTimeout(timer)); };
    }, []);

    const handleCreate = () => {
        if (onCreate) {
            onCreate({
                title, company, location, salary, url, web_page: webPage,
                markdown, comments, client, 
                required_technologies: requiredTechnologies, 
                optional_technologies: optionalTechnologies,
                ...statusState
            });
        }
    };

    return {
        formState: {
            title, location, url, webPage, markdown, comments, salary, company, client,
            requiredTechnologies, optionalTechnologies, statusState, showAllFields
        },
        setters: {
            setTitle, setLocation, setUrl, setWebPage, setMarkdown, setComments, setSalary, 
            setCompany, setClient, setRequiredTechnologies, setOptionalTechnologies, setShowAllFields
        },
        actions: {
            handleStatusToggle,
            handleChange,
            handleCreate
        }
    };
}
