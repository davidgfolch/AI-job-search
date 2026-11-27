import type { ChangeEvent, Dispatch, SetStateAction } from 'react';

// Define explicit types for formState and setters extracted from useJobEditForm output structure
// This assumes formState and setters structure from useJobEditForm.ts
export interface JobFormFieldsProps {
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
        modality: string[];
        hybridInfo: string;
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
        setModality: Dispatch<SetStateAction<string[]>>;
        setHybridInfo: Dispatch<SetStateAction<string>>;
    };
    handleChange: (setter: Dispatch<SetStateAction<string>>, field: string) => (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
    handleCreate: () => void;
    handleModalityChange: (value: string) => void;
    modalityValues?: string[];
}
