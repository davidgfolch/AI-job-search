import type { Job } from '../../api/jobs';

interface SalaryActionsProps {
    onToggleCalculator: () => void;
    onUpdate?: (data: Partial<Job>) => void;
}

export default function SalaryActions({ onToggleCalculator, onUpdate }: SalaryActionsProps) {
    return (
        <>
            <button 
                className="config-btn salary-toggle-btn"
                onClick={onToggleCalculator}>
                🧮 Freelance</button>
            <button 
                className="config-btn salary-toggle-btn"
                onClick={() => window.open('https://tecalculo.com/calculadora-de-sueldo-neto', '_blank')}>
                🧮 Gross year</button>
            {onUpdate && (
                <button
                    className="config-btn salary-toggle-btn salary-delete-btn"
                    onClick={() => onUpdate({ salary: null })}
                    title="Delete salary information">
                    🗑️</button>
            )}
        </>
    );
}
