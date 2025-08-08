// src/components/JobList.tsx

import React, { useState } from 'react';
import { Job, JobState } from '@/types/job';
import { useBulkUpdateJobs, useBulkDeleteJobs, useEnrichJobs } from '@/hooks/useJobs';
import JobCard from './JobCard';
import { 
  ChevronLeft, 
  ChevronRight, 
  Trash2, 
  Brain, 
  CheckCircle2,
  Circle,
  MoreHorizontal,
  Eye,
  FileX,
  Zap
} from 'lucide-react';

interface JobListProps {
  jobs: Job[];
  totalCount: number;
  currentPage: number;
  pageSize: number;
  hasNext: boolean;
  hasPrev: boolean;
  isLoading: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

const BULK_ACTIONS = [
  { value: 'seen', label: 'Mark as Seen', icon: Eye, color: 'text-gray-600' },
  { value: 'applied', label: 'Mark as Applied', icon: CheckCircle2, color: 'text-green-600' },
  { value: 'rejected', label: 'Mark as Rejected', icon: FileX, color: 'text-red-600' },
  { value: 'ignored', label: 'Mark as Ignored', icon: Circle, color: 'text-gray-400' },
  { value: 'discarded', label: 'Mark as Discarded', icon: Trash2, color: 'text-red-600' },
];

export default function JobList({
  jobs,
  totalCount,
  currentPage,
  pageSize,
  hasNext,
  hasPrev,
  isLoading,
  onPageChange,
  onPageSizeChange,
}: JobListProps) {
  const [selectedJobs, setSelectedJobs] = useState<Set<number>>(new Set());
  const [showBulkActions, setShowBulkActions] = useState(false);

  const bulkUpdateMutation = useBulkUpdateJobs();
  const bulkDeleteMutation = useBulkDeleteJobs();
  const enrichJobsMutation = useEnrichJobs();

  // Handle individual job selection
  const handleJobSelect = (job: Job) => {
    const newSelected = new Set(selectedJobs);
    if (newSelected.has(job.id)) {
      newSelected.delete(job.id);
    } else {
      newSelected.add(job.id);
    }
    setSelectedJobs(newSelected);
  };

  // Handle select all toggle
  const handleSelectAll = () => {
    if (selectedJobs.size === jobs.length) {
      setSelectedJobs(new Set());
    } else {
      setSelectedJobs(new Set(jobs.map(job => job.id)));
    }
  };

  // Handle bulk state update
  const handleBulkStateUpdate = async (newState: JobState) => {
    if (selectedJobs.size === 0) return;
    
    try {
      await bulkUpdateMutation.mutateAsync({
        ids: Array.from(selectedJobs),
        updates: { state: newState }
      });
      setSelectedJobs(new Set());
      setShowBulkActions(false);
    } catch (error) {
      // Error handled by hook
    }
  };

  // Handle bulk delete
  const handleBulkDelete = async () => {
    if (selectedJobs.size === 0) return;
    
    if (!confirm(`Are you sure you want to delete ${selectedJobs.size} job(s)? This action cannot be undone.`)) {
      return;
    }
    
    try {
      await bulkDeleteMutation.mutateAsync(Array.from(selectedJobs));
      setSelectedJobs(new Set());
      setShowBulkActions(false);
    } catch (error) {
      // Error handled by hook
    }
  };

  // Handle bulk AI enrichment
  const handleBulkEnrich = async () => {
    if (selectedJobs.size === 0) return;
    
    try {
      await enrichJobsMutation.mutateAsync(Array.from(selectedJobs));
      setSelectedJobs(new Set());
      setShowBulkActions(false);
    } catch (error) {
      // Error handled by hook
    }
  };

  // Calculate pagination info
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalCount);
  const totalPages = Math.ceil(totalCount / pageSize);

  const isAllSelected = jobs.length > 0 && selectedJobs.size === jobs.length;
  const isSomeSelected = selectedJobs.size > 0 && selectedJobs.size < jobs.length;

  if (jobs.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 mb-4">
          <FileX className="h-16 w-16 mx-auto" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
        <p className="text-gray-500">
          Try adjusting your filters or check back later for new opportunities.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with bulk actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={isAllSelected}
              ref={(input) => {
                if (input) input.indeterminate = isSomeSelected;
              }}
              onChange={handleSelectAll}
              className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
            />
            <span className="ml-3 text-sm text-gray-700">
              {selectedJobs.size > 0 
                ? `${selectedJobs.size} of ${jobs.length} selected`
                : `Select all ${jobs.length} jobs`
              }
            </span>
          </div>

          {selectedJobs.size > 0 && (
            <div className="flex items-center gap-2">
              {/* Quick Actions */}
              <div className="flex border border-gray-300 rounded-lg overflow-hidden">
                {BULK_ACTIONS.map((action) => {
                  const Icon = action.icon;
                  return (
                    <button
                      key={action.value}
                      onClick={() => handleBulkStateUpdate(action.value as JobState)}
                      disabled={bulkUpdateMutation.isPending}
                      className={`px-3 py-2 text-sm hover:bg-gray-50 transition-colors border-r border-gray-300 last:border-r-0 ${action.color} disabled:opacity-50`}
                      title={action.label}
                    >
                      <Icon className="h-4 w-4" />
                    </button>
                  );
                })}
              </div>

              {/* Special Actions */}
              <button
                onClick={handleBulkEnrich}
                disabled={enrichJobsMutation.isPending}
                className="flex items-center gap-1 px-3 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
                title="AI Enrich Selected"
              >
                <Brain className="h-4 w-4" />
                Enrich
              </button>

              <button
                onClick={handleBulkDelete}
                disabled={bulkDeleteMutation.isPending}
                className="flex items-center gap-1 px-3 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                title="Delete Selected"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </button>

              <button
                onClick={() => setSelectedJobs(new Set())}
                className="text-gray-500 hover:text-gray-700 text-sm"
              >
                Clear selection
              </button>
            </div>
          )}
        </div>

        {/* Results info */}
        <div className="text-sm text-gray-500">
          Showing {startItem}-{endItem} of {totalCount.toLocaleString()} jobs
        </div>
      </div>

      {/* Loading overlay */}
      {isLoading && (
        <div className="relative">
          <div className="absolute inset-0 bg-white bg-opacity-75 z-10 flex items-center justify-center">
            <div className="flex items-center gap-2 text-gray-600">
              <Zap className="h-5 w-5 animate-spin" />
              <span>Loading jobs...</span>
            </div>
          </div>
        </div>
      )}

      {/* Job cards grid */}
      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-1">
        {jobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            isSelected={selectedJobs.has(job.id)}
            onSelect={handleJobSelect}
            showCheckbox={true}
          />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 pt-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">Show</span>
              <select
                value={pageSize}
                onChange={(e) => onPageSizeChange(parseInt(e.target.value))}
                className="px-2 py-1 border border-gray-300 rounded text-sm focus:ring-primary-500 focus:border-primary-500"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
              <span className="text-sm text-gray-700">per page</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={!hasPrev || isLoading}
              className="flex items-center gap-1 px-3 py-2 text-sm text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </button>

            {/* Page numbers */}
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(7, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 7) {
                  pageNum = i + 1;
                } else if (currentPage <= 4) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 3) {
                  pageNum = totalPages - 6 + i;
                } else {
                  pageNum = currentPage - 3 + i;
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => onPageChange(pageNum)}
                    disabled={isLoading}
                    className={`px-3 py-2 text-sm rounded-lg disabled:cursor-not-allowed ${
                      currentPage === pageNum
                        ? 'bg-primary-600 text-white'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>

            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={!hasNext || isLoading}
              className="flex items-center gap-1 px-3 py-2 text-sm text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}