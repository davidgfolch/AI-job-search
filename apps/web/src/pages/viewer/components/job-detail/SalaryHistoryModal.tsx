import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, type Job, type SalaryHistoryEntry } from '../../api/ViewerApi';
import { Modal } from '../../../common/components/core/Modal';
import ConfirmModal from '../../../common/components/core/ConfirmModal';
import { useConfirmationModal } from '../../../common/hooks/useConfirmationModal';
import { useSalaryHistory } from '../../hooks/useSalaryHistory';
import './SalaryHistoryModal.css';

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
    const queryClient = useQueryClient();
    const confirmModal = useConfirmationModal();
    const [deleteError, setDeleteError] = useState<string | null>(null);
    const { data: fetchedHistory, isLoading } = useSalaryHistory(
        !records && isOpen ? job.id : undefined,
    );
    const history = records ?? fetchedHistory;

    const deleteMutation = useMutation({
        mutationFn: (recordId: string) => jobsApi.deleteSalaryHistoryEntry(recordId),
        onSuccess: () => {
            setDeleteError(null);
            queryClient.invalidateQueries({ queryKey: ['salaryHistory', job.id] });
            queryClient.invalidateQueries({ queryKey: ['companySalaryHistory'] });
        },
        onError: (error: Error) => setDeleteError(error.message),
    });

    const handleDelete = (entry: SalaryHistoryEntry) => {
        confirmModal.confirm(
            `Delete the ${entry.salary} entry for ${entry.company_raw}?`,
            () => deleteMutation.mutate(entry.id),
        );
    };

    const pendingId = deleteMutation.isPending ? deleteMutation.variables : undefined;

    return (
        <>
            <Modal isOpen={isOpen} onClose={onClose} title="Salary History" className="expanded">
                {isLoading && <p>Loading history...</p>}
                {deleteError && <p className="salary-history-error">{deleteError}</p>}
                {!isLoading && (!history || history.length === 0) && (
                    <p>No salary history recorded yet. The background scanner will pick this up.</p>
                )}
                {!isLoading && history && history.length > 0 && (
                    <div className="salary-history-table-container">
                        <table className="salary-history-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Company</th>
                                    <th>Role</th>
                                    <th>Salary</th>
                                    <th>Source</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {history.map((entry) => (
                                    <tr key={entry.id}>
                                        <td className="salary-history-date">{formatDate(entry.recorded_at)}</td>
                                        <td>{entry.company_raw}</td>
                                        <td>{entry.title}</td>
                                        <td className="salary-history-salary">{entry.salary}</td>
                                        <td>{entry.source}</td>
                                        <td>
                                            <button
                                                className="salary-history-delete-btn"
                                                onClick={() => handleDelete(entry)}
                                                disabled={pendingId === entry.id}
                                                title="Delete salary history entry"
                                            >🗑️</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </Modal>
            <ConfirmModal
                isOpen={confirmModal.isOpen}
                title="Delete salary history entry"
                message={confirmModal.message}
                onConfirm={confirmModal.handleConfirm}
                onCancel={confirmModal.close}
            />
        </>
    );
}
