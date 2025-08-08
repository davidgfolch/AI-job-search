// src/components/JobCard.tsx

import React, { useState } from 'react';
import { Job, JobState } from '@/types/job';
import { useUpdateJob } from '@/hooks/useJobs';
import { 
  MapPin, 
  Building2, 
  Calendar, 
  DollarSign, 
  ExternalLink, 
  Brain, 
  MessageSquare,
  Edit,
  Check,
  X
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';

interface JobCardProps {
  job: Job;
  isSelected?: boolean;
  onSelect?: (job: Job) => void;
  showCheckbox?: boolean;
}

const JOB_STATE_COLORS: Record<JobState, string> = {
  'new': 'bg-blue-100 text-blue-800',
  'seen': 'bg-gray-100 text-gray-800',
  'applied': 'bg-green-100 text-green-800',
  'interview_scheduled': 'bg-yellow-100 text-yellow-800',
  'interviewed': 'bg-purple-100 text-purple-800',
  'rejected': 'bg-red-100 text-red-800',
  'offer_received': 'bg-emerald-100 text-emerald-800',
  'accepted': 'bg-emerald-200 text-emerald-900',
  'declined': 'bg-orange-100 text-orange-800',
  'ignored': 'bg-gray-100 text-gray-600',
  'discarded': 'bg-red-50 text-red-600',
  'closed': 'bg-gray-100 text-gray-600',
};

const JOB_STATE_LABELS: Record<JobState, string> = {
  'new': 'New',
  'seen': 'Seen',
  'applied': 'Applied',
  'interview_scheduled': 'Interview Scheduled',
  'interviewed': 'Interviewed',
  'rejected': 'Rejected',
  'offer_received': 'Offer Received',
  'accepted': 'Accepted',
  'declined': 'Declined',
  'ignored': 'Ignored',
  'discarded': 'Discarded',
  'closed': 'Closed',
};

export default function JobCard({ job, isSelected, onSelect, showCheckbox }: JobCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedComments, setEditedComments] = useState(job.comments || '');
  const [selectedState, setSelectedState] = useState<JobState>(job.state);
  
  const updateJobMutation = useUpdateJob();

  const handleStateChange = async (newState: JobState) => {
    setSelectedState(newState);
    try {
      await updateJobMutation.mutateAsync({
        id: job.id,
        updates: { state: newState }
      });
    } catch (error) {
      // Revert state on error
      setSelectedState(job.state);
    }
  };

  const handleSaveComments = async () => {
    try {
      await updateJobMutation.mutateAsync({
        id: job.id,
        updates: { comments: editedComments }
      });
      setIsEditing(false);
    } catch (error) {
      // Error is handled by the hook
    }
  };

  const handleCancelEdit = () => {
    setEditedComments(job.comments || '');
    setIsEditing(false);
  };

  const formatSalary = () => {
    if (job.salary) return job.salary;
    if (job.salary_min && job.salary_max) {
      return `€${job.salary_min.toLocaleString()} - €${job.salary_max.toLocaleString()}`;
    }
    if (job.salary_min) return `From €${job.salary_min.toLocaleString()}`;
    if (job.salary_max) return `Up to €${job.salary_max.toLocaleString()}`;
    return null;
  };

  return (
    <div 
      className={`bg-white border rounded-lg p-6 hover:shadow-lg transition-all duration-200 ${
        isSelected ? 'ring-2 ring-primary-500 border-primary-300' : 'border-gray-200 hover:border-gray-300'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-3 flex-1">
          {showCheckbox && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onSelect?.(job)}
              className="mt-1 w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
            />
          )}
          
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <h3 className="text-lg font-semibold text-gray-900 leading-tight hover:text-primary-600 cursor-pointer">
                {job.title}
              </h3>
              
              <div className="flex items-center gap-2 flex-shrink-0">
                {job.ai_enriched && (
                  <div className="flex items-center text-purple-600" title="AI Enriched">
                    <Brain className="h-4 w-4" />
                  </div>
                )}
                
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 hover:text-primary-600 transition-colors"
                  title="View original job posting"
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
            </div>
            
            <div className="flex items-center gap-2 mt-1 text-gray-600">
              <Building2 className="h-4 w-4" />
              <span className="font-medium">{job.company}</span>
              {job.location && (
                <>
                  <span>•</span>
                  <MapPin className="h-4 w-4" />
                  <span>{job.location}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-2">
          <select
            value={selectedState}
            onChange={(e) => handleStateChange(e.target.value as JobState)}
            disabled={updateJobMutation.isPending}
            className={`text-xs px-3 py-1 rounded-full border-0 font-medium cursor-pointer ${JOB_STATE_COLORS[selectedState]}`}
          >
            {Object.entries(JOB_STATE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Job Info */}
      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-4">
        <div className="flex items-center gap-1">
          <Calendar className="h-4 w-4" />
          <span>Posted {formatDistanceToNow(new Date(job.posted_date), { addSuffix: true })}</span>
        </div>
        
        {formatSalary() && (
          <div className="flex items-center gap-1 text-green-600">
            <DollarSign className="h-4 w-4" />
            <span className="font-medium">{formatSalary()}</span>
          </div>
        )}
        
        <div className={`px-2 py-1 rounded text-xs font-medium ${
          job.source === 'linkedin' ? 'bg-blue-100 text-blue-700' :
          job.source === 'glassdoor' ? 'bg-green-100 text-green-700' :
          job.source === 'infojobs' ? 'bg-purple-100 text-purple-700' :
          'bg-gray-100 text-gray-700'
        }`}>
          {job.source.charAt(0).toUpperCase() + job.source.slice(1)}
        </div>

        {job.job_type && (
          <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
            {job.job_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </span>
        )}

        {job.experience_level && (
          <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs">
            {job.experience_level.charAt(0).toUpperCase() + job.experience_level.slice(1)}
          </span>
        )}
      </div>

      {/* Technologies */}
      {(job.required_technologies?.length > 0 || job.ai_skills?.length > 0) && (
        <div className="mb-4">
          <div className="flex flex-wrap gap-1">
            {job.required_technologies?.slice(0, 6).map((tech) => (
              <span
                key={tech}
                className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-md font-medium"
              >
                {tech}
              </span>
            ))}
            {job.ai_skills?.slice(0, 3).map((skill) => (
              <span
                key={skill}
                className="px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded-md font-medium border border-purple-200"
                title="AI detected skill"
              >
                {skill}
              </span>
            ))}
            {(job.required_technologies?.length > 6 || job.ai_skills?.length > 3) && (
              <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-md">
                +{(job.required_technologies?.length || 0) + (job.ai_skills?.length || 0) - 6 - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Description Preview */}
      {job.ai_summary ? (
        <div className="mb-4">
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="h-4 w-4 text-purple-600" />
              <span className="text-sm font-medium text-purple-800">AI Summary</span>
            </div>
            <p className="text-sm text-purple-700 leading-relaxed">
              {job.ai_summary.length > 150 
                ? `${job.ai_summary.substring(0, 150)}...` 
                : job.ai_summary
              }
            </p>
          </div>
        </div>
      ) : job.description && (
        <div className="mb-4">
          <p className="text-sm text-gray-600 leading-relaxed">
            {job.description.length > 200 
              ? `${job.description.substring(0, 200)}...` 
              : job.description
            }
          </p>
        </div>
      )}

      {/* Comments Section */}
      <div className="border-t pt-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">Comments</span>
          </div>
          
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="text-gray-400 hover:text-primary-600 transition-colors"
              title="Edit comments"
            >
              <Edit className="h-4 w-4" />
            </button>
          )}
        </div>

        {isEditing ? (
          <div className="space-y-2">
            <textarea
              value={editedComments}
              onChange={(e) => setEditedComments(e.target.value)}
              placeholder="Add your notes, interview feedback, or any comments about this position..."
              className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
              rows={3}
            />
            <div className="flex items-center gap-2">
              <button
                onClick={handleSaveComments}
                disabled={updateJobMutation.isPending}
                className="flex items-center gap-1 px-3 py-1 bg-primary-600 text-white text-sm rounded hover:bg-primary-700 disabled:opacity-50"
              >
                <Check className="h-3 w-3" />
                Save
              </button>
              <button
                onClick={handleCancelEdit}
                disabled={updateJobMutation.isPending}
                className="flex items-center gap-1 px-3 py-1 border border-gray-300 text-gray-700 text-sm rounded hover:bg-gray-50"
              >
                <X className="h-3 w-3" />
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-600">
            {job.comments ? (
              <p className="leading-relaxed">{job.comments}</p>
            ) : (
              <p className="italic text-gray-400">No comments yet. Click edit to add notes.</p>
            )}
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="flex items-center justify-between pt-3 mt-3 border-t text-xs text-gray-400">
        <span>Scraped {format(new Date(job.scraped_date), 'MMM d, yyyy')}</span>
        <span>ID: {job.id}</span>
      </div>
    </div>
  );
}