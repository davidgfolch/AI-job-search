import { useState } from 'react';
import type { Job } from '../../api/ViewerApi';
import { useCompanySalaryHistory } from '../../hooks/useSalaryHistory';
import SalaryHistoryModal from './SalaryHistoryModal';

interface SalaryHistoryIndicatorProps {
    job: Job;
}

export default function SalaryHistoryIndicator({ job }: SalaryHistoryIndicatorProps) {
    const [showModal, setShowModal] = useState(false);
    const { data: history, isLoading } = useCompanySalaryHistory(job.company);

    if (isLoading) {
        return (
            <li className="info-row">Company salary history: <span className="loading-dots">⏳</span>
            </li>
        );
    }

    if (!history || history.length === 0) return null;

    const salaries = [...new Set(history.map(e => e.salary))];
    const companies = [...new Set(history.map(e => e.company_raw))];

    return (
        <>
            <li className="info-row">Company salary history:&nbsp;
                <span className="salary-value-text">
                    {salaries.slice(0, 3).join(' | ')}{salaries.length > 3 ? '...' : ''}
                    {companies.length > 1 && <span style={{ opacity: 0.6, fontSize: '0.85em' }}> ({companies.length} companies)</span>}
                </span>
                <button className="config-btn" onClick={() => setShowModal(true)} title="View full history">📊</button>
            </li>
            <SalaryHistoryModal job={job} isOpen={showModal} onClose={() => setShowModal(false)} records={history} />
        </>
    );
}