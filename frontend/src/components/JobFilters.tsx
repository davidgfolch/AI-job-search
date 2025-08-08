// src/components/JobFilters.tsx

import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { JobFilters as JobFiltersType, JobState } from '@/types/job';
import { useFilterOptions } from '@/hooks/useJobs';
import { Search, Filter, X, Calendar, DollarSign } from 'lucide-react';

interface JobFiltersProps {
  filters: JobFiltersType;
  onFiltersChange: (filters: JobFiltersType) => void;
  isLoading?: boolean;
}

const JOB_STATES: { value: JobState; label: string; color: string }[] = [
  { value: 'new', label: 'New', color: 'bg-blue-100 text-blue-800' },
  { value: 'seen', label: 'Seen', color: 'bg-gray-100 text-gray-800' },
  { value: 'applied', label: 'Applied', color: 'bg-green-100 text-green-800' },
  { value: 'interview_scheduled', label: 'Interview Scheduled', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'interviewed', label: 'Interviewed', color: 'bg-purple-100 text-purple-800' },
  { value: 'rejected', label: 'Rejected', color: 'bg-red-100 text-red-800' },
  { value: 'offer_received', label: 'Offer Received', color: 'bg-emerald-100 text-emerald-800' },
  { value: 'accepted', label: 'Accepted', color: 'bg-emerald-100 text-emerald-800' },
  { value: 'declined', label: 'Declined', color: 'bg-orange-100 text-orange-800' },
  { value: 'ignored', label: 'Ignored', color: 'bg-gray-100 text-gray-600' },
  { value: 'discarded', label: 'Discarded', color: 'bg-red-100 text-red-600' },
  { value: 'closed', label: 'Closed', color: 'bg-gray-100 text-gray-600' },
];

export default function JobFilters({ filters, onFiltersChange, isLoading }: JobFiltersProps) {
  const { control, handleSubmit, watch, reset, setValue } = useForm<JobFiltersType>({
    defaultValues: filters,
  });

  const { data: filterOptions } = useFilterOptions();
  
  const watchedFilters = watch();
  
  // Apply filters when form changes
  const onSubmit = (data: JobFiltersType) => {
    onFiltersChange(data);
  };

  // Clear all filters
  const clearFilters = () => {
    const emptyFilters: JobFiltersType = {};
    reset(emptyFilters);
    onFiltersChange(emptyFilters);
  };

  // Count active filters
  const activeFiltersCount = Object.values(watchedFilters).filter(value => {
    if (Array.isArray(value)) return value.length > 0;
    return value !== undefined && value !== null && value !== '';
  }).length;

  return (
    <div className="bg-white border-b border-gray-200 p-6">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Search and Quick Actions Row */}
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          <div className="flex-1 max-w-md">
            <Controller
              name="search"
              control={control}
              render={({ field }) => (
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    {...field}
                    type="text"
                    placeholder="Search jobs, companies, technologies..."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              )}
            />
          </div>
          
          <div className="flex gap-2 items-center">
            <span className="text-sm text-gray-500">
              {activeFiltersCount > 0 && `${activeFiltersCount} filters active`}
            </span>
            {activeFiltersCount > 0 && (
              <button
                type="button"
                onClick={clearFilters}
                className="flex items-center gap-1 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="h-4 w-4" />
                Clear
              </button>
            )}
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Filter className="h-4 w-4" />
              {isLoading ? 'Applying...' : 'Apply Filters'}
            </button>
          </div>
        </div>

        {/* Filter Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          
          {/* Company Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Company
            </label>
            <Controller
              name="company"
              control={control}
              render={({ field }) => (
                <input
                  {...field}
                  type="text"
                  placeholder="Company name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                />
              )}
            />
          </div>

          {/* Location Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location
            </label>
            <Controller
              name="location"
              control={control}
              render={({ field }) => (
                <select
                  {...field}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                >
                  <option value="">All locations</option>
                  {filterOptions?.locations.map((location) => (
                    <option key={location} value={location}>
                      {location}
                    </option>
                  ))}
                </select>
              )}
            />
          </div>

          {/* Source Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Source
            </label>
            <Controller
              name="source"
              control={control}
              render={({ field: { value, onChange } }) => (
                <select
                  multiple
                  value={value || []}
                  onChange={(e) => {
                    const selectedValues = Array.from(e.target.selectedOptions, option => option.value);
                    onChange(selectedValues);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                >
                  {filterOptions?.sources.map((source) => (
                    <option key={source} value={source}>
                      {source.charAt(0).toUpperCase() + source.slice(1)}
                    </option>
                  ))}
                </select>
              )}
            />
          </div>

          {/* Job State Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <Controller
              name="state"
              control={control}
              render={({ field: { value, onChange } }) => (
                <select
                  multiple
                  value={value || []}
                  onChange={(e) => {
                    const selectedValues = Array.from(e.target.selectedOptions, option => option.value) as JobState[];
                    onChange(selectedValues);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                >
                  {JOB_STATES.map((state) => (
                    <option key={state.value} value={state.value}>
                      {state.label}
                    </option>
                  ))}
                </select>
              )}
            />
          </div>

          {/* Salary Range */}
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min Salary (€)
              </label>
              <Controller
                name="salary_min"
                control={control}
                render={({ field }) => (
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      {...field}
                      type="number"
                      placeholder="30,000"
                      onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                    />
                  </div>
                )}
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Salary (€)
              </label>
              <Controller
                name="salary_max"
                control={control}
                render={({ field }) => (
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      {...field}
                      type="number"
                      placeholder="80,000"
                      onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                    />
                  </div>
                )}
              />
            </div>
          </div>

          {/* Job Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Job Type
            </label>
            <Controller
              name="job_type"
              control={control}
              render={({ field: { value, onChange } }) => (
                <select
                  multiple
                  value={value || []}
                  onChange={(e) => {
                    const selectedValues = Array.from(e.target.selectedOptions, option => option.value);
                    onChange(selectedValues);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                >
                  {filterOptions?.job_types.map((type) => (
                    <option key={type} value={type}>
                      {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              )}
            />
          </div>

          {/* Experience Level Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Experience Level
            </label>
            <Controller
              name="experience_level"
              control={control}
              render={({ field: { value, onChange } }) => (
                <select
                  multiple
                  value={value || []}
                  onChange={(e) => {
                    const selectedValues = Array.from(e.target.selectedOptions, option => option.value);
                    onChange(selectedValues);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                >
                  {filterOptions?.experience_levels.map((level) => (
                    <option key={level} value={level}>
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </option>
                  ))}
                </select>
              )}
            />
          </div>

          {/* Posted Date Range */}
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Posted After
              </label>
              <Controller
                name="posted_after"
                control={control}
                render={({ field }) => (
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      {...field}
                      type="date"
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                    />
                  </div>
                )}
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Posted Before
              </label>
              <Controller
                name="posted_before"
                control={control}
                render={({ field }) => (
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      {...field}
                      type="date"
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                    />
                  </div>
                )}
              />
            </div>
          </div>

          {/* AI Enriched Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              AI Status
            </label>
            <Controller
              name="ai_enriched"
              control={control}
              render={({ field: { value, onChange } }) => (
                <select
                  value={value === undefined ? '' : value.toString()}
                  onChange={(e) => {
                    const val = e.target.value;
                    onChange(val === '' ? undefined : val === 'true');
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                >
                  <option value="">All jobs</option>
                  <option value="true">AI Enriched</option>
                  <option value="false">Not AI Enriched</option>
                </select>
              )}
            />
          </div>

        </div>

        {/* Technologies Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Required Technologies
          </label>
          <Controller
            name="required_technologies"
            control={control}
            render={({ field: { value, onChange } }) => (
              <div className="flex flex-wrap gap-2">
                {filterOptions?.technologies.slice(0, 20).map((tech) => {
                  const isSelected = value?.includes(tech) || false;
                  return (
                    <button
                      key={tech}
                      type="button"
                      onClick={() => {
                        const currentTech = value || [];
                        if (isSelected) {
                          onChange(currentTech.filter(t => t !== tech));
                        } else {
                          onChange([...currentTech, tech]);
                        }
                      }}
                      className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                        isSelected
                          ? 'bg-primary-100 border-primary-300 text-primary-800'
                          : 'bg-gray-100 border-gray-300 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {tech}
                    </button>
                  );
                })}
                {filterOptions && filterOptions.technologies.length > 20 && (
                  <span className="text-sm text-gray-500 py-1">
                    +{filterOptions.technologies.length - 20} more available...
                  </span>
                )}
              </div>
            )}
          />
        </div>

      </form>
    </div>
  );
}