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
    const [modality, setModality] = useState<string[]>([]);
    const [hybridInfo, setHybridInfo] = useState('');
    
    // Local state for status fields to handle optimistic updates
    const [statusState, setStatusState] = useState<Record<string, boolean>>({});
    const [showAllFields, setShowAllFields] = useState(mode === 'create');
    
    // Ref to track debounce timers for auto-save
    const debounceTimersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

    const buildStatusState = (source: Job): Record<string, boolean> => {
        const result: Record<string, boolean> = {};
        BOOLEAN_FILTER_KEYS.forEach(key => {
            result[key] = source[key as keyof Job] as boolean;
        });
        return result;
    };

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
        setModality([]);
        setHybridInfo('');
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
        setModality(job.modality || []);
        setHybridInfo(job.hybrid_info || '');
    };

    // Sync local state with job prop when it changes
    const [synced, setSynced] = useState<{ job: Job | null; mode: 'edit' | 'create' } | null>(null);
    if (synced?.job !== job || synced?.mode !== mode) {
        const previous = synced;
        setSynced({ job, mode });
        if (mode === 'create') {
            setShowAllFields(true);
            resetForm();
            setStatusState({});
        } else if (job) {
            if (previous?.job?.id !== job.id || previous?.mode !== 'edit') setShowAllFields(false);
            populateForm(job);
            setStatusState(buildStatusState(job));
        }
    }

    const handleStatusToggle = (field: string) => {
        if (mode === 'edit' && job) {
            const newValue = !statusState[field];
            setStatusState(prev => ({ ...prev, [field]: newValue }));
            onUpdate({ [field]: newValue });
        } else if (mode === 'create') {
             setStatusState(prev => ({ ...prev, [field]: !prev[field] }));
        }
    };

    const handleModalityChange = (value: string) => {
        const next = modality.includes(value) ? modality.filter(item => item !== value) : [...modality, value];
        setModality(next);
        if (mode === 'edit' && job) {
            onUpdate({ modality: next.length > 0 ? next : null });
        }
    };

    const handleAutoSave = (field: string, value: string) => {
        if (mode === 'create') return;
        if (debounceTimersRef.current[field]) {
            clearTimeout(debounceTimersRef.current[field]);
        }
        debounceTimersRef.current[field] = setTimeout(() => {
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
        const timers = debounceTimersRef.current;
        return () => { Object.values(timers).forEach(timer => clearTimeout(timer)); };
    }, []);

    const handleCreate = () => {
        if (onCreate) {
            // Build explicit boolean fields object with all keys set to false by default
            const booleanFields: Record<string, boolean> = {};
            BOOLEAN_FILTER_KEYS.forEach(key => {
                booleanFields[key] = statusState[key] ?? false;
            });

            onCreate({
                title, company, location, salary, url, web_page: webPage,
                markdown, comments, client,
                required_technologies: requiredTechnologies,
                optional_technologies: optionalTechnologies,
                modality: modality.length > 0 ? modality : null,
                hybrid_info: hybridInfo || null,
                ...booleanFields
            });
        }
    };

    return {
        formState: {
            title, location, url, webPage, markdown, comments, salary, company, client,
            requiredTechnologies, optionalTechnologies, modality, hybridInfo, statusState, showAllFields
        },
        setters: {
            setTitle, setLocation, setUrl, setWebPage, setMarkdown, setComments, setSalary, 
            setCompany, setClient, setRequiredTechnologies, setOptionalTechnologies,
            setModality, setHybridInfo, setShowAllFields
        },
        actions: {
            handleStatusToggle,
            handleChange,
            handleModalityChange,
            handleCreate
        }
    };
}
