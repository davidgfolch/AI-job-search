import { useState, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { jobsApi, type Job, type JobListParams } from "../../api/jobs";
import { STATE_FIELDS } from "../contants";
import { useConfirmationModal } from "../useConfirmationModal";
import { useBulkJobMutations } from "./useBulkJobMutations";

export type TabType = "list" | "edit";

export const getDeleteOldJobsMsg = (count: number) => `Going to delete ${count} older jobs (see sql filter)`;


interface UseJobMutationsProps {
  filters: JobListParams;
  selectedJob: Job | null;
  setSelectedJob: React.Dispatch<React.SetStateAction<Job | null>>;
  activeTab: TabType;
  autoSelectNext: React.RefObject<{
    shouldSelect: boolean;
    previousJobId: number | null;
  }>;
  selectedIds: Set<number>;
  setSelectedIds: React.Dispatch<React.SetStateAction<Set<number>>>;
  selectionMode: "none" | "manual" | "all";
  setSelectionMode: React.Dispatch<
    React.SetStateAction<"none" | "manual" | "all">
  >;
  onJobUpdated?: (job: Job) => void;
  onJobsDeleted?: (ids: number[]) => void;
}

export const useJobMutations = ({
  filters,
  selectedJob,
  setSelectedJob,
  activeTab,
  autoSelectNext,
  selectedIds,
  setSelectedIds,
  selectionMode,
  setSelectionMode,
  onJobUpdated,
  onJobsDeleted,
}: UseJobMutationsProps) => {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState<{
    text: string;
    type: "success" | "error";
  } | null>(null);

  const confirmModal = useConfirmationModal();

  const { bulkUpdateMutation, bulkDeleteMutation } = useBulkJobMutations({
      onJobsDeleted,
      setMessage,
      setSelectionMode,
      setSelectedIds
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Job> }) =>
      jobsApi.updateJob(id, data),
    onSuccess: (updatedJob) => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      if (selectedJob && updatedJob.id === selectedJob.id) {
        setSelectedJob(updatedJob);
      }
      onJobUpdated?.(updatedJob);
    },
  });

  const handleJobUpdate = useCallback(
    (data: Partial<Job>) => {
      if (selectedJob) {
        // Check if any state field is being updated
        const hasStateChange = STATE_FIELDS.some((field) => field in data);
        if (hasStateChange && activeTab === "list") {
          autoSelectNext.current = {
            shouldSelect: true,
            previousJobId: selectedJob.id,
          };
        }
        updateMutation.mutate({ id: selectedJob.id, data });
      }
    },
    [selectedJob, updateMutation, activeTab, autoSelectNext]
  );

  const ignoreSelected = useCallback(() => {
    const count = selectionMode === "all" ? "all" : selectedIds.size;
    const msg =
      selectionMode === "all"
        ? "Are you sure you want to ignore ALL jobs matching the current filters?"
        : `Are you sure you want to ignore ${count} selected jobs?`;

    confirmModal.confirm(msg, () => {
        if (selectionMode === "all") {
          bulkUpdateMutation.mutate({
            select_all: true,
            filters,
            update: { ignored: true },
          });
        } else if (selectedIds.size > 0) {
          bulkUpdateMutation.mutate({
            ids: Array.from(selectedIds),
            update: { ignored: true },
          });
        }
    });
  }, [selectionMode, selectedIds, filters, bulkUpdateMutation, confirmModal]);

  const deleteSelected = useCallback((count: number) => {
    const msg = getDeleteOldJobsMsg(count);
    confirmModal.confirm(msg, () => {
        if (selectionMode === "all") {
          bulkDeleteMutation.mutate({
            select_all: true,
            filters,
          });
        } else if (selectedIds.size > 0) {
          bulkDeleteMutation.mutate({
            ids: Array.from(selectedIds),
          });
        }
    });
  }, [selectionMode, selectedIds, filters, bulkDeleteMutation, confirmModal]);

  return {
    message,
    setMessage,
    confirmModal: {
        isOpen: confirmModal.isOpen,
        message: confirmModal.message,
        onConfirm: confirmModal.handleConfirm,
        close: confirmModal.close,
    },
    setConfirmModal: (val: any) => { 
        // Backward compatibility shim if needed, or better, expose close.
        if (typeof val === 'function') {
            const newState = val({ isOpen: confirmModal.isOpen });
            if (!newState.isOpen) confirmModal.close();
        } else if (!val.isOpen) {
            confirmModal.close();
        }
    },
    handleJobUpdate,
    ignoreSelected,
    deleteSelected,
    updateMutation,
    bulkUpdateMutation,
    bulkDeleteMutation,
  };
};
