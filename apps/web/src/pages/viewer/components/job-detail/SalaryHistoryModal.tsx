import type { Job, SalaryHistoryEntry } from '../../api/ViewerApi';
import { Modal } from '../../../common/components/core/Modal';
import { useSalaryHistory } from '../../hooks/useSalaryHistory';

interface SalaryHistoryModalProps {
    job: Job;
    isOpen: boolean;
    onClose: () => void;
    records?: SalaryHistoryEntry[];
}

const formatDate = (d: string) => {
    return new Date(d).toLocaleString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
};

export default function SalaryHistoryModal({ job, isOpen, onClose, records }: SalaryHistoryModalProps) {
    const { data: fetchedHistory, isLoading } = useSalaryHistory(
        !records && isOpen ? job.id : undefined,
    );
    const history = records ?? fetchedHistory;

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Salary History" className="expanded">
            {isLoading && <p>Loading history...</p>}
            {!isLoading && (!history || history.length === 0) && (
                <p>No salary history recorded yet. The background scanner will pick this up.</p>
            )}
            {!isLoading && history && history.length > 0 && (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ borderBottom: '2px solid var(--border-color)', textAlign: 'left' }}>
                            <th style={{ padding: '0.5rem' }}>Date</th>
                            <th style={{ padding: '0.5rem' }}>Company</th>
                            <th style={{ padding: '0.5rem' }}>Role</th>
                            <th style={{ padding: '0.5rem' }}>Salary</th>
                            <th style={{ padding: '0.5rem' }}>Source</th>
                        </tr>
                    </thead>
                    <tbody>
                        {history.map((entry, i) => (
                            <tr key={i} style={{ borderBottom: '1px solid var(--border-color)' }}>
                                <td style={{ padding: '0.5rem', whiteSpace: 'nowrap' }}>{formatDate(entry.recorded_at)}</td>
                                <td style={{ padding: '0.5rem' }}>{entry.company_raw}</td>
                                <td style={{ padding: '0.5rem' }}>{entry.title}</td>
                                <td style={{ padding: '0.5rem', fontWeight: 600 }}>{entry.salary}</td>
                                <td style={{ padding: '0.5rem' }}>{entry.source}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </Modal>
    );
}
