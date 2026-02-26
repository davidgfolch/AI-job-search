import type { Job } from '../../../viewer/api/ViewerApi';

interface SalaryActionsProps {
    onToggleCalculator: () => void;
    onUpdate?: (data: Partial<Job>) => void;
}

import { settingsApi } from '../../../settings/api/SettingsApi';

export default function SalaryActions({ onToggleCalculator, onUpdate }: SalaryActionsProps) {
    const handleGrossYearClick = async () => {
        try {
            const envSettings = await settingsApi.getEnvSettings();
            const url = envSettings.UI_GROSS_YEAR_URL || 'https://tecalculo.com/calculadora-de-sueldo-neto';
            window.open(url, '_blank');
        } catch (error) {
            console.error('Failed to get UI_GROSS_YEAR_URL', error);
            window.open('https://tecalculo.com/calculadora-de-sueldo-neto', '_blank');
        }
    };

    return (
        <>
            <button 
                className="config-btn salary-toggle-btn"
                onClick={onToggleCalculator}>
                🧮 Freelance</button>
            <button 
                className="config-btn salary-toggle-btn"
                onClick={handleGrossYearClick}>
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
