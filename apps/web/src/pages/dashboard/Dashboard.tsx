import PageHeader from '../common/components/PageHeader';
import { useDashboard } from './hooks/useDashboard';
import ServiceCard from './components/ServiceCard';
import OllamaStatus from './components/OllamaStatus';
import RecentErrors from './components/RecentErrors';
import './Dashboard.css';

export default function Dashboard() {
    const { data, isLoading, isError } = useDashboard();

    if (isLoading) return <div className="dashboard-loading">Loading dashboard...</div>;
    if (isError || !data) return <div className="dashboard-error">Failed to load dashboard data</div>;

    const runningCount = data.services.filter(s => s.status === 'running').length;
    const totalCount = data.services.length;

    return (
        <>
            <PageHeader title="Dashboard" />
            <main className="dashboard-main">
                <div className="dashboard-summary">
                    <div className="summary-item">
                        <span className="summary-value">{runningCount}/{totalCount}</span>
                        <span className="summary-label">Services Running</span>
                    </div>
                    <div className="summary-item">
                        <span className={`summary-value ${data.ollama.reachable ? '' : 'summary-value--error'}`}>
                            {data.ollama.reachable ? 'Connected' : 'Disconnected'}
                        </span>
                        <span className="summary-label">Ollama</span>
                    </div>
                    <div className="summary-item">
                        <span className="summary-value">
                            {data.services.reduce((acc, s) => acc + s.metrics.pendingJobs, 0)}
                        </span>
                        <span className="summary-label">Total Pending</span>
                    </div>
                </div>

                <div className="dashboard-top-row">
                    <OllamaStatus ollama={data.ollama} />
                </div>

                <div className="dashboard-services-grid">
                    {data.services.map(service => (
                        <ServiceCard key={service.name} service={service} />
                    ))}
                </div>

                <RecentErrors services={data.services} />
            </main>
        </>
    );
}
