import type { Job } from '../api/ViewerApi';

export type SelectionMode = 'none' | 'manual' | 'all';

interface ToggleJobSelectionArgs {
    id: number;
    selectionMode: SelectionMode;
    selectedIds: Set<number>;
    allJobs: Job[];
    setSelectionMode: (mode: SelectionMode) => void;
    setSelectedIds: (ids: Set<number>) => void;
    setSelectedJob: (job: Job | null) => void;
}

/** Toggle one row in the selection, switching out of the select-all mode when it is active. */
export const toggleJobSelection = ({
    id, selectionMode, selectedIds, allJobs, setSelectionMode, setSelectedIds, setSelectedJob,
}: ToggleJobSelectionArgs) => {
    if (selectionMode === 'all') {
        // Deselecting one row while all are selected: switch to manual with every loaded job except this one
        const newSelected = new Set<number>();
        for (const job of allJobs) {
            if (job.id !== id) newSelected.add(job.id);
        }
        setSelectionMode('manual');
        setSelectedIds(newSelected);
        const job = allJobs.find(j => j.id === id);
        if (job) setSelectedJob(job);
        return;
    }
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
        newSelected.delete(id);
        if (newSelected.size === 0) {
            setSelectionMode('none');
        }
    } else {
        newSelected.add(id);
        setSelectionMode('manual');
        const job = allJobs.find(j => j.id === id);
        if (job) setSelectedJob(job);
    }
    setSelectedIds(newSelected);
};
