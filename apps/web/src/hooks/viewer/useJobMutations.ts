import { useState, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { jobsApi, type Job, type JobListParams } from "../../api/jobs";

export type TabType = "list" | "edit";

interface UseJobMutationsProps {
  filters: JobListParams;
  selectedJob: Job | null;
  setSelectedJob: React.Dispatch<React.SetStateAction<Job | null>>;
  activeTab: TabType;
  autoSelectNext: React.MutableRefObject<{
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

  // Modal State
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    message: string;
    onConfirm: () => void;
  }>({ isOpen: false, message: "", onConfirm: () => {} });

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

  const bulkUpdateMutation = useMutation({
    mutationFn: (payload: {
      ids?: number[];
      filters?: JobListParams;
      update: Partial<Job>;
      select_all?: boolean;
    }) => jobsApi.bulkUpdateJobs(payload),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setMessage({ text: `Updated ${data.updated} jobs`, type: "success" });
      setSelectionMode("none");
      setSelectedIds(new Set());
      if (variables.ids && onJobsDeleted) {
        onJobsDeleted(variables.ids);
      }
    },
    onError: (err) => {
      setMessage({
        text: err instanceof Error ? err.message : "Error updating jobs",
        type: "error",
      });
    },
  });

  const handleJobUpdate = useCallback(
    (data: Partial<Job>) => {
      if (selectedJob) {
        // Check if any state field is being updated
        const stateFields = [
          "ignored",
          "seen",
          "applied",
          "discarded",
          "closed",
          "flagged",
          "like",
          "ai_enriched",
        ];
        const hasStateChange = stateFields.some((field) => field in data);
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

    setConfirmModal({
      isOpen: true,
      message: msg,
      onConfirm: () => {
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
        setConfirmModal((prev) => ({ ...prev, isOpen: false }));
      },
    });
  }, [selectionMode, selectedIds, filters, bulkUpdateMutation]);

  return {
    message,
    setMessage,
    confirmModal,
    setConfirmModal,
    handleJobUpdate,
    ignoreSelected,
    updateMutation,
    bulkUpdateMutation,
  };
};
