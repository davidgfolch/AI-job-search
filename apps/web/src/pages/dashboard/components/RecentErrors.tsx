import type { ServiceStatus } from '../api/DashboardApi';
import './RecentErrors.css';

interface Props {
    services: ServiceStatus[];
}

export default function RecentErrors({ services }: Props) {
    const allErrors = services
        .filter(s => s.recentErrors.length > 0)
        .flatMap(s => s.recentErrors.map(e => ({ ...e, serviceName: s.displayName })))
        .sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''))
        .slice(0, 15);

    if (allErrors.length === 0) {
        return (
            <div className="recent-errors recent-errors--empty">
                <h3>Recent Errors</h3>
                <div className="no-errors">No recent errors found</div>
            </div>
        );
    }

    return (
        <div className="recent-errors">
            <h3>Recent Errors ({allErrors.length})</h3>
            <div className="errors-list">
                {allErrors.map((err, i) => (
                    <div key={i} className={`error-entry error-entry--${err.level}`}>
                        <span className="error-service">{err.serviceName}</span>
                        <span className="error-time">
                            {err.timestamp ? new Date(err.timestamp).toLocaleString() : ''}
                        </span>
                        <span className="error-event">{err.event}</span>
                        <span className="error-message" title={err.message}>{err.message}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
