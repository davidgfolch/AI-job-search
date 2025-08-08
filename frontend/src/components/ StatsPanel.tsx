// src/components/StatsPanel.tsx

import React from 'react';
import { JobStats } from '@/types/job';
import { 
  TrendingUp, 
  Brain, 
  DollarSign, 
  Calendar,
  Building2,
  Code,
  RefreshCw,
  CheckCircle2,
  Clock,
  XCircle,
  Eye,
  FileX
} from 'lucide-react';
import { format } from 'date-fns';

interface StatsPanelProps {
  stats?: JobStats;
  isLoading: boolean;
  onRefresh: () => void;
}

const STATE_ICONS: Record<string, { icon: any; color: string }> = {
  'new': { icon: TrendingUp, color: 'text-blue-600' },
  'seen': { icon: Eye, color: 'text-gray-600' },
  'applied': { icon: CheckCircle2, color: 'text-green-600' },
  'interview_scheduled': { icon: Clock, color: 'text-yellow-600' },
  'interviewed': { icon: Clock, color: 'text-purple-600' },
  'rejected': { icon: XCircle, color: 'text-red-600' },
  'offer_received': { icon: CheckCircle2, color: 'text-emerald-600' },
  'accepted': { icon: CheckCircle2, color: 'text-emerald-700' },
  'declined': { icon: XCircle, color: 'text-orange-600' },
  'ignored': { icon: FileX, color: 'text-gray-400' },
  'discarded': { icon: FileX, color: 'text-red-400' },
  'closed': { icon: FileX, color: 'text-gray-400' },
};

export default function StatsPanel({ stats, isLoading, onRefresh }: StatsPanelProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-32"></div>
          <div className="space-y-2">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-4 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <TrendingUp className="h-8 w-8 mx-auto mb-2" />
          <p>Unable to load statistics</p>
          <button
            onClick={onRefresh}
            className="mt-2 text-sm text-primary-600 hover:text-primary-700"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  const totalJobs = stats.total_jobs;
  const aiEnrichedPercentage = totalJobs > 0 ? Math.round((stats.ai_enriched_count / totalJobs) * 100) : 0;

  return (
    <div className="space-y-6">
        NOT IMPLEMENTED ASK CLAUDE
    </div>
  );
}