import type { OllamaStatus as OllamaStatusType } from '../api/DashboardApi';
import './OllamaStatus.css';

interface Props {
    ollama: OllamaStatusType;
}

export default function OllamaStatus({ ollama }: Props) {
    const { reachable, serverUrl, serverIp, isLan, recentErrors } = ollama;
    const address = serverIp ? (serverUrl ? `${serverIp}` : serverIp) : null;
    const scope = isLan ? 'LAN' : 'local';
    return (
        <div className={`ollama-status ollama-status--${reachable ? 'ok' : 'error'}`}>
            <div className="ollama-status-header">
                <span className={`status-dot status-dot--${reachable ? 'running' : 'error'}`} />
                <h3 className="ollama-status-title">Ollama</h3>
                <span className="ollama-status-label">{reachable ? 'Reachable' : 'Unreachable'}</span>
            </div>
            {address && (
                <span className="ollama-status-address">
                    {reachable ? '' : 'last: '}{address} <span className="ollama-status-scope">· {scope}</span>
                </span>
            )}
            {!reachable && recentErrors.length > 0 && (
                <div className="ollama-status-errors">
                    {recentErrors.map((err, i) => (
                        <div key={i} className="ollama-error-entry">
                            <span className="ollama-error-time">
                                {err.timestamp ? new Date(err.timestamp).toLocaleString() : ''}
                            </span>
                            <span className="ollama-error-msg">{err.message}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
