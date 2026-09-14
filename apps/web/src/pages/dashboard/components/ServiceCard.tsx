import type { ServiceStatus } from '../api/DashboardApi';
import './ServiceCard.css';

const STATUS_LABELS: Record<string, string> = {
    running: 'Running',
    stopped: 'Stopped',
    error: 'Error',
};

interface Props {
    service: ServiceStatus;
}

export default function ServiceCard({ service }: Props) {
    const { displayName, status, lastActivity, usesOllama, metrics } = service;
    return (
        <div className={`service-card service-card--${status}`}>
            <div className="service-card-header">
                <span className={`status-dot status-dot--${status}`} />
                <h3 className="service-card-name">{displayName}</h3>
                <span className="service-card-status">{STATUS_LABELS[status]}</span>
            </div>
            <div className="service-card-body">
                <div className="service-card-metrics">
                    <div className="metric">
                        <span className="metric-value">{metrics.pendingJobs}</span>
                        <span className="metric-label">Pending</span>
                    </div>
                    <div className="metric">
                        <span className="metric-value">{metrics.succeeded}</span>
                        <span className="metric-label">Succeeded</span>
                    </div>
                    <div className="metric metric--error">
                        <span className="metric-value">{metrics.failed}</span>
                        <span className="metric-label">Failed</span>
                    </div>
                </div>
                {usesOllama && (
                    <div className="service-card-tag">Ollama</div>
                )}
                {lastActivity && (
                    <div className="service-card-last-activity">
                        Last: {new Date(lastActivity).toLocaleTimeString()}
                    </div>
                )}
                {metrics.lastError && (
                    <div className="service-card-last-error" title={metrics.lastError}>
                        Last error: {metrics.lastError.substring(0, 60)}
                        {metrics.lastError.length > 60 ? '...' : ''}
                    </div>
                )}
            </div>
        </div>
    );
}
