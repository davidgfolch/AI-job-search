import PageHeader from '../common/components/PageHeader';
import { useDashboard, REFRESH_INTERVAL_MS } from './hooks/useDashboard';
import ServiceCard from './components/ServiceCard';
import RecentErrors from './components/RecentErrors';
import './Dashboard.css';

export default function Dashboard() {
    const { data, isLoading, isError } = useDashboard();

    if (isLoading) return <div className="dashboard-loading">Loading dashboard...</div>;
    if (isError || !data) return <div className="dashboard-error">Failed to load dashboard data</div>;

    const runningCount = data.services.filter(s => s.status === 'running').length;
    const totalCount = data.services.length;
    const refreshedAt = data.timestamp ? new Date(data.timestamp).toLocaleString() : '-';

    return (
        <>
            <PageHeader title="Dashboard" />
            <main className="dashboard-main">
                <div className="dashboard-last-updated">
                    <span className="last-updated-label">Last updated:</span>
                    <span className="last-updated-value">{refreshedAt}</span>
                    <span className="last-updated-refresh">Autorefresh every {REFRESH_INTERVAL_MS / 1000}s</span>
                </div>
                <div className="dashboard-summary">
                    <div className="summary-item">
                        <span className="summary-value">{runningCount}/{totalCount}</span>
                        <span className="summary-label">Services Running</span>
                    </div>
                    <div className="summary-item">
                        <span className="summary-value">
                            {data.services.reduce((acc, s) => acc + s.metrics.pendingJobs, 0)}
                        </span>
                        <span className="summary-label">Total Pending</span>
                    </div>
                    <div className="summary-item">
                        <span className="summary-value">{data.deployment === 'docker' ? 'Docker' : 'Host'}</span>
                        <span className="summary-label">Deployment</span>
                    </div>
                </div>

                <div className="dashboard-top-row">
                    <div className="service-pill service-pill--ai-backend">
                        <span className="status-dot status-dot--running" />
                        <span className="service-pill-label">AI Backend</span>
                        <span className="service-pill-value">{data.aiBackend}</span>
                    </div>
                    <div className="service-pill service-pill--ollama">
                        <span className={`status-dot status-dot--${data.ollama.reachable ? 'running' : 'error'}`} />
                        <span className="service-pill-label">Ollama</span>
                        <span className={`service-pill-value ${data.ollama.reachable ? '' : 'service-pill-value--error'}`}>
                            {data.ollama.reachable ? 'Connected' : 'Disconnected'}
                        </span>
                        {data.ollama.serverIp && (
                            <span className="service-pill-address">
                                {data.ollama.serverIp} <span className="service-pill-scope">· {data.ollama.isLan ? 'LAN' : 'local'}</span>
                            </span>
                        )}
                    </div>
                    <div className="service-pill service-pill--prometheus">
                        <span className={`status-dot status-dot--${data.prometheus.reachable ? 'running' : 'error'}`} />
                        <span className="service-pill-label">Prometheus</span>
                        <span className={`service-pill-value ${data.prometheus.reachable ? '' : 'service-pill-value--error'}`}>
                            {data.prometheus.reachable ? 'Up' : 'Down'}
                        </span>
                        <span className="service-pill-address">{data.prometheus.url}</span>
                    </div>
                    <div className="service-pill service-pill--grafana">
                        <span className={`status-dot status-dot--${data.grafana.reachable ? 'running' : 'error'}`} />
                        <span className="service-pill-label">Grafana</span>
                        <span className={`service-pill-value ${data.grafana.reachable ? '' : 'service-pill-value--error'}`}>
                            {data.grafana.reachable ? 'Up' : 'Down'}
                        </span>
                        <span className="service-pill-address">{data.grafana.url}</span>
                    </div>
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
