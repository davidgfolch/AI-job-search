import { useState, useCallback } from 'react';
import { type Job, jobsApi } from '../api/ViewerApi';

interface UseAppliedModalProps {
    selectedJob: Job | null;
    allJobs: Job[];
    onJobUpdate: (update: Partial<Job>) => void;
    onBulkUpdate: (ids: number[], update: Partial<Job>) => void;
    selectedIds: Set<number>;
    selectionMode: 'none' | 'manual' | 'all';
}

export function useAppliedModal({
    selectedJob,
    allJobs,
    onJobUpdate,
    onBulkUpdate,
    selectedIds,
    selectionMode,
}: UseAppliedModalProps) {
    const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
    const [pendingJobIds, setPendingJobIds] = useState<number[]>([]);

    const appendComment = (existingComment: string | null, newComment: string): string => {
        if (!existingComment || existingComment.trim() === '') {
            return newComment.trim();
        }
        return existingComment.trim() + ' ' + newComment.trim();
    };

    const openModal = useCallback(() => {
        const jobIds: number[] = [];
        
        if (selectionMode === 'all') {
            // "all" selection should not reach here due to button being disabled
            return;
        } else if (selectedIds.size > 1) {
            // Multiple selection should not reach here due to button being disabled
            return;
        } else if (selectedIds.size === 1) {
            // Single selection in bulk mode
            jobIds.push(...selectedIds);
        } else {
            // Single job mode - will be handled by onJobUpdate
            jobIds.push(-1); // Use -1 as indicator for single job mode
        }

        setPendingJobIds(jobIds);
        setIsModalOpen(true);
    }, [selectedIds, selectionMode]);

    const handleConfirm = useCallback(async (includeComment: boolean, comment: string) => {
        const isSingleJob = pendingJobIds.length === 1 && pendingJobIds[0] === -1;
        
        if (includeComment && comment.trim()) {
            const trimmedComment = comment.trim();
            
            if (isSingleJob && selectedJob) {
                // Single job update - append comment to existing
                const newComment = appendComment(selectedJob.comments, trimmedComment);
                onJobUpdate({ applied: true, comments: newComment });
            } else if (pendingJobIds.length === 1) {
                // Bulk update for single selected job - get existing job data first
                const jobId = pendingJobIds[0];
                const existingJob = allJobs.find(j => j.id === jobId) || 
                                 await jobsApi.getJob(jobId).catch(() => null);
                
                if (existingJob) {
                    const newComment = appendComment(existingJob.comments, trimmedComment);
                    const update: Partial<Job> = { applied: true, comments: newComment };
                    onBulkUpdate(pendingJobIds, update);
                } else {
                    // Fallback - just set the comment
                    const update: Partial<Job> = { applied: true, comments: trimmedComment };
                    onBulkUpdate(pendingJobIds, update);
                }
            }
        } else {
            // No comment - just mark as applied
            if (isSingleJob) {
                onJobUpdate({ applied: true });
            } else {
                const update: Partial<Job> = { applied: true };
                onBulkUpdate(pendingJobIds, update);
            }
        }

        setIsModalOpen(false);
        setPendingJobIds([]);
    }, [pendingJobIds, selectedJob, allJobs, onJobUpdate, onBulkUpdate]);

    const handleCancel = useCallback(() => {
        setIsModalOpen(false);
        setPendingJobIds([]);
    }, []);

    return {
        isModalOpen,
        openModal,
        handleConfirm,
        handleCancel,
    };
}