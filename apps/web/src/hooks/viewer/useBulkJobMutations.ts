import { useMutation, useQueryClient } from "@tanstack/react-query";
import { jobsApi, type Job, type JobListParams } from "../../api/jobs";

interface UseBulkJobMutationsProps {
  onJobsDeleted?: (ids: number[] | 'all') => void;
  setMessage: (msg: { text: string; type: "success" | "error" } | null) => void;
  setSelectionMode: (mode: "none" | "manual" | "all") => void;
  setSelectedIds: (ids: Set<number>) => void;
}

export function useBulkJobMutations({
  onJobsDeleted,
  setMessage,
  setSelectionMode,
  setSelectedIds,
}: UseBulkJobMutationsProps) {
  const queryClient = useQueryClient();

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

  const bulkDeleteMutation = useMutation({
    mutationFn: (payload: {
      ids?: number[];
      filters?: JobListParams;
      select_all?: boolean;
    }) => jobsApi.deleteJobs(payload),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setMessage({ text: `Deleted ${data.deleted} jobs`, type: "success" });
      setSelectionMode("none");
      setSelectedIds(new Set());
      if (variables.select_all && onJobsDeleted) {
        onJobsDeleted('all');
      } else if (variables.ids && onJobsDeleted) {
        onJobsDeleted(variables.ids);
      }
    },
    onError: (err) => {
      setMessage({
        text: err instanceof Error ? err.message : "Error deleting jobs",
        type: "error",
      });
    },
  });

  return {
    bulkUpdateMutation,
    bulkDeleteMutation,
  };
}
