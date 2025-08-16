// src/components/Dashboard.tsx

import React, { useState, useEffect } from 'react';
import { JobFilters as JobFiltersType } from '@/types/job';
import { useJobs, useJobStats } from '@/hooks/useJobs';
import JobFilters from './JobFilters';
import JobList from './JobList';
import StatsPanel from './StatsPanel';
import { 
  Briefcase, 
  TrendingUp, 
  Clock, 
  Brain,
  Search,
  RefreshCw,
  Settings
} from 'lucide-react';

export default function Dashboard() {
  const [filters, setFilters] = useState<JobFiltersType>({
    limit: 20,
    offset: 0,
    sort_by: 'scraped_date',
    sort_order: 'desc'
  });
  
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(true);

  const { 
    data: jobsResponse, 
    isLoading: jobsLoading, 
    error: jobsError,
    refetch: refetchJobs 
  } = useJobs(filters);

  const { 
    data: stats, 
    isLoading: statsLoading,
    refetch: refetchStats 
  } = useJobStats();

  // Handle filter changes
  const handleFiltersChange = (newFilters: JobFiltersType) => {
    const updatedFilters = {
      ...newFilters,
      limit: filters.limit,
      offset: 0,
      sort_by: filters.sort_by,
      sort_order: filters.sort_order
    };
    setFilters(updatedFilters);
    setCurrentPage(1);
  };

  // Handle page changes
  const handlePageChange = (page: number) => {
    const offset = (page - 1) * (filters.limit || 20);
    setFilters(prev => ({ ...prev, offset }));
    setCurrentPage(page);
    
    // Scroll to top when changing pages
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handle page size changes
  const handlePageSizeChange = (pageSize: number) => {
    setFilters(prev => ({ 
      ...prev, 
      limit: pageSize, 
      offset: 0 
    }));
    setCurrentPage(1);
  };

  // Handle sort changes
  const handleSortChange = (sortBy: string, sortOrder: 'asc' | 'desc') => {
    setFilters(prev => ({
      ...prev,
      sort_by: sortBy as any,
      sort_order: sortOrder,
      offset: 0
    }));
    setCurrentPage(1);
  };

  // Refresh all data
  const handleRefresh = () => {
    refetchJobs();
    refetchStats();
  };

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      refetchStats();
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [refetchStats]);

  const jobs = jobsResponse?.jobs || [];
  const totalCount = jobsResponse?.total_count || 0;
  const hasNext = jobsResponse?.has_next || false;
  const hasPrev = jobsResponse?.has_prev || false;
  const pageSize = filters.limit || 20;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-8 h-8 bg-primary-600 rounded-lg">
                <Briefcase className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">AI Job Search</h1>
                <p className="text-sm text-gray-500">Manage your job opportunities</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Quick Stats */}
              {stats && !statsLoading && (
                <div className="hidden md:flex items-center gap-6 text-sm">
                  <div className="flex items-center gap-2 text-gray-600">
                    <TrendingUp className="h-4 w-4" />
                    <span>{stats.total_jobs.toLocaleString()} total</span>
                  </div>
                  <div className="flex items-center gap-2 text-green-600">
                    <Clock className="h-4 w-4" />
                    <span>{stats.by_state.applied || 0} applied</span>
                  </div>
                  <div className="flex items-center gap-2 text-purple-600">
                    <Brain className="h-4 w-4" />
                    <span>{stats.ai_enriched_count} enriched</span>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors ${
                    showFilters 
                      ? 'bg-primary-50 border-primary-200 text-primary-700' 
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Search className="h-4 w-4" />
                  Filters
                </button>
                
                <button
                  onClick={handleRefresh}
                  disabled={jobsLoading || statsLoading}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${(jobsLoading || statsLoading) ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex gap-6">
          {/* Main Content */}
          <div className="flex-1 space-y-6">
            {/* Filters */}
            {showFilters && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <JobFilters
                  filters={filters}
                  onFiltersChange={handleFiltersChange}
                  isLoading={jobsLoading}
                />
              </div>
            )}

            {/* Sort Controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium text-gray-700">Sort by:</span>
                <select
                  value={`${filters.sort_by}-${filters.sort_order}`}
                  onChange={(e) => {
                    const [sortBy, sortOrder] = e.target.value.split('-');
                    handleSortChange(sortBy, sortOrder as 'asc' | 'desc');
                  }}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="scraped_date-desc">Latest scraped</option>
                  <option value="posted_date-desc">Latest posted</option>
                  <option value="salary_max-desc">Highest salary</option>
                  <option value="salary_max-asc">Lowest salary</option>
                  <option value="title-asc">Title A-Z</option>
                  <option value="title-desc">Title Z-A</option>
                  <option value="company-asc">Company A-Z</option>
                  <option value="company-desc">Company Z-A</option>
                </select>
              </div>

              {/* Results Summary */}
              {totalCount > 0 && (
                <div className="text-sm text-gray-500">
                  {totalCount === 1 ? '1 job found' : `${totalCount.toLocaleString()} jobs found`}
                </div>
              )}
            </div>

            {/* Error State */}
            {jobsError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      Error loading jobs
                    </h3>
                    <div className="mt-2 text-sm text-red-700">
                      <p>Unable to fetch job data. Please check your connection and try again.</p>
                    </div>
                    <div className="mt-4">
                      <button
                        onClick={handleRefresh}
                        className="bg-red-100 px-2 py-1 text-xs font-medium text-red-800 rounded hover:bg-red-200"
                      >
                        Try again
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Job List */}
            {!jobsError && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <JobList
                  jobs={jobs}
                  totalCount={totalCount}
                  currentPage={currentPage}
                  pageSize={pageSize}
                  hasNext={hasNext}
                  hasPrev={hasPrev}
                  isLoading={jobsLoading}
                  onPageChange={handlePageChange}
                  onPageSizeChange={handlePageSizeChange}
                />
              </div>
            )}
          </div>

          {/* Sidebar - Stats Panel */}
          {!showFilters && (
            <div className="w-80 space-y-6">
              <StatsPanel 
                stats={stats} 
                isLoading={statsLoading} 
                onRefresh={refetchStats}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}