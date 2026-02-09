import type { Job } from '../api/ViewerApi';
import { useJobEditForm } from './hooks/useJobEditForm';
import StatusButtons from './StatusButtons';
import JobFormFields from './JobFormFields';
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
        statusState, showAllFields
    } = formState;

    const {
        setShowAllFields
    } = setters;

    const { handleStatusToggle, handleChange, handleCreate } = actions;

    if (mode === 'edit' && !job) return <div className="job-edit-form"><div className="no-selection">Select a job to edit</div></div>;

    return (
        <div className="job-edit-form">
            {mode === 'create' && <h2 className="form-title">Create New Job</h2>}
            {mode === 'edit' && (
                <div className="toggle-edit-btn">
                    <button onClick={() => setShowAllFields(!showAllFields)} className="create-btn" type="button">
                        {showAllFields ? 'Edit Less' : 'Edit All'}
                    </button>
                </div>
            )}
            
            <StatusButtons 
                statusState={statusState} 
                handleStatusToggle={handleStatusToggle} 
            />

            <JobFormFields 
                mode={mode} 
                jobId={job?.id}
                showAllFields={showAllFields}
                formState={formState}
                setters={setters}
                handleChange={handleChange}
                handleCreate={handleCreate}
            />
        </div>
    );
}
