import type { InfrastructureService } from '../api/DashboardApi';
import './InfrastructurePanel.css';

interface Props {
    entries: InfrastructureService[];
}

function statusLabel(entry: InfrastructureService): string {
    if (entry.kind === 'ollama') return entry.reachable ? 'Connected' : 'Disconnected';
    if (entry.kind === 'activity') return entry.reachable ? 'Active' : 'Idle';
    return entry.reachable ? 'Up' : 'Down';
}

export default function InfrastructurePanel({ entries }: Props) {
    return (
        <section className="dashboard-infrastructure">
            <h2 className="infrastructure-title">Infrastructure</h2>
            <div className="infrastructure-grid">
                {entries.map(entry => (
                    <div key={entry.name} className={`service-pill infra-card infra-card--${entry.kind}`} data-testid={`infra-${entry.name}`}>
                        <span className={`status-dot status-dot--${entry.reachable ? 'running' : 'error'}`} />
                        <div className="infra-card-body">
                            <span className="service-pill-label">{entry.displayName}</span>
                            <span className={`service-pill-value ${entry.reachable ? '' : 'service-pill-value--error'}`}>
                                {statusLabel(entry)}
                            </span>
                            {entry.kind === 'ollama' && entry.serverIp && (
                                <span className="service-pill-address">
                                    {entry.serverIp} <span className="service-pill-scope">· {entry.isLan ? 'LAN' : 'local'}</span>
                                </span>
                            )}
                            {entry.kind !== 'ollama' && entry.url && (
                                <span className="service-pill-address">{entry.url}</span>
                            )}
                            {entry.kind === 'activity' && entry.lastActivity && (
                                <span className="infra-card-detail">Last: {new Date(entry.lastActivity).toLocaleString()}</span>
                            )}
                            {entry.kind !== 'activity' && entry.detail && (
                                <span className="infra-card-detail">{entry.detail}</span>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
}
