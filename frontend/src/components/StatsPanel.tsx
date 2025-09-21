import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend
} from 'recharts';
import { 
  Briefcase, 
  Users, 
  CheckCircle, 
  XCircle, 
  Clock, 
  TrendingUp,
  Calendar,
  MapPin,
  DollarSign,
  Cpu,
  Eye,
  Send,
  MessageSquare,
  AlertCircle
} from 'lucide-react';

// Types for statistics data
interface JobStats {
  total_jobs: number;
  new_jobs_today: number;
  new_jobs_week: number;
  ai_enriched: number;
  not_ai_enriched: number;
  by_status: {
    [key: string]: number;
  };
  by_source: {
    [key: string]: number;
  };
  by_location: {
    [key: string]: number;
  };
  salary_stats: {
    avg_salary: number;
    min_salary: number;
    max_salary: number;
    jobs_with_salary: number;
  };
  technology_stats: {
    [key: string]: number;
  };
  daily_applications: Array<{
    date: string;
    count: number;
  }>;
  response_rate: number;
  avg_response_time: number;
}

// Mock data - replace with actual API calls
const mockStats: JobStats = {
  total_jobs: 1247,
  new_jobs_today: 23,
  new_jobs_week: 156,
  ai_enriched: 890,
  not_ai_enriched: 357,
  by_status: {
    'New': 234,
    'Seen': 445,
    'Applied': 156,
    'Interview': 23,
    'Rejected': 234,
    'Closed': 89,
    'Discarded': 66
  },
  by_source: {
    'LinkedIn': 523,
    'Infojobs': 298,
    'Glassdoor': 201,
    'Tecnoempleo': 145,
    'Indeed': 80
  },
  by_location: {
    'Madrid': 312,
    'Barcelona': 245,
    'Valencia': 123,
    'Sevilla': 89,
    'Bilbao': 67,
    'Remote': 411
  },
  salary_stats: {
    avg_salary: 45000,
    min_salary: 25000,
    max_salary: 85000,
    jobs_with_salary: 567
  },
  technology_stats: {
    'JavaScript': 234,
    'Python': 198,
    'React': 167,
    'Node.js': 145,
    'Java': 123,
    'TypeScript': 109,
    'Docker': 98,
    'AWS': 87
  },
  daily_applications: [
    { date: '2024-01-01', count: 5 },
    { date: '2024-01-02', count: 8 },
    { date: '2024-01-03', count: 12 },
    { date: '2024-01-04', count: 6 },
    { date: '2024-01-05', count: 15 },
    { date: '2024-01-06', count: 9 },
    { date: '2024-01-07', count: 11 }
  ],
  response_rate: 18.5,
  avg_response_time: 7.2
};

// Colors for charts
const COLORS = {
  primary: '#3b82f6',
  secondary: '#10b981',
  accent: '#f59e0b',
  danger: '#ef4444',
  warning: '#f97316',
  info: '#06b6d4',
  purple: '#8b5cf6',
  pink: '#ec4899'
};

const PIE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#f97316', '#06b6d4', '#8b5cf6', '#ec4899'];

const StatsPanel: React.FC = () => {
  const [stats, setStats] = useState<JobStats>(mockStats);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'sources' | 'technologies' | 'applications'>('overview');

  // Simulate data fetching
  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      try {
        // Replace with actual API call
        // const response = await fetch('/api/stats');
        // const data = await response.json();
        // setStats(data);
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        setStats(mockStats);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  // Prepare data for charts
  const statusData = Object.entries(stats.by_status).map(([status, count]) => ({
    name: status,
    value: count,
    percentage: ((count / stats.total_jobs) * 100).toFixed(1)
  }));

  const sourceData = Object.entries(stats.by_source).map(([source, count]) => ({
    name: source,
    count,
    percentage: ((count / stats.total_jobs) * 100).toFixed(1)
  }));

  const locationData = Object.entries(stats.by_location).map(([location, count]) => ({
    name: location,
    count,
    percentage: ((count / stats.total_jobs) * 100).toFixed(1)
  })).slice(0, 8); // Top 8 locations

  const technologyData = Object.entries(stats.technology_stats).map(([tech, count]) => ({
    name: tech,
    count,
    percentage: ((count / stats.total_jobs) * 100).toFixed(1)
  })).slice(0, 10); // Top 10 technologies

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Job Search Statistics</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart },
            { id: 'sources', label: 'Sources', icon: MapPin },
            { id: 'technologies', label: 'Technologies', icon: Cpu },
            { id: 'applications', label: 'Applications', icon: Send }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
                <Briefcase className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_jobs.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">
                  +{stats.new_jobs_today} today
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">AI Enriched</CardTitle>
                <Cpu className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.ai_enriched.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">
                  {((stats.ai_enriched / stats.total_jobs) * 100).toFixed(1)}% of total
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Applications Sent</CardTitle>
                <Send className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.by_status.Applied || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {stats.response_rate}% response rate
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Salary</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">€{stats.salary_stats.avg_salary.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">
                  {stats.salary_stats.jobs_with_salary} jobs with salary
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Job Status Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Job Status Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name}: ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Top Locations */}
            <Card>
              <CardHeader>
                <CardTitle>Top Locations</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={locationData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill={COLORS.primary} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Weekly Applications Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Daily Applications Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats.daily_applications}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke={COLORS.secondary} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Sources Tab */}
      {activeTab === 'sources' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Job Sources Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={sourceData} layout="horizontal">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={80} />
                    <Tooltip />
                    <Bar dataKey="count" fill={COLORS.info} />
                  </BarChart>
                </ResponsiveContainer>
                
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Source Statistics</h3>
                  {sourceData.map((source, index) => (
                    <div key={source.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div 
                          className="w-4 h-4 rounded"
                          style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }}
                        />
                        <span className="font-medium">{source.name}</span>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">{source.count}</div>
                        <div className="text-sm text-gray-500">{source.percentage}%</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Technologies Tab */}
      {activeTab === 'technologies' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Most Demanded Technologies</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={technologyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill={COLORS.purple} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {technologyData.map((tech, index) => (
              <Card key={tech.name}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold">{tech.name}</h3>
                      <p className="text-sm text-gray-500">{tech.count} jobs</p>
                    </div>
                    <Badge variant="secondary">{tech.percentage}%</Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Applications Tab */}
      {activeTab === 'applications' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Response Rate</CardTitle>
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.response_rate}%</div>
                <p className="text-xs text-muted-foreground">
                  Average response time: {stats.avg_response_time} days
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Interviews</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.by_status.Interview || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {(((stats.by_status.Interview || 0) / (stats.by_status.Applied || 1)) * 100).toFixed(1)}% of applications
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                <CheckCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(((stats.by_status.Interview || 0) / (stats.by_status.Applied || 1)) * 100).toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  Interview to application ratio
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Application Pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(stats.by_status).map(([status, count]) => {
                  const percentage = (count / stats.total_jobs) * 100;
                  const getStatusColor = (status: string) => {
                    switch (status.toLowerCase()) {
                      case 'applied': return 'bg-blue-500';
                      case 'interview': return 'bg-green-500';
                      case 'rejected': return 'bg-red-500';
                      case 'closed': return 'bg-gray-500';
                      case 'seen': return 'bg-yellow-500';
                      case 'new': return 'bg-purple-500';
                      default: return 'bg-gray-400';
                    }
                  };

                  return (
                    <div key={status} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">{status}</span>
                        <span className="text-sm text-gray-500">{count} jobs</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`${getStatusColor(status)} h-2 rounded-full transition-all duration-500`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default StatsPanel;