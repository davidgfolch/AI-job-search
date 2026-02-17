import { useState, useEffect, useDeferredValue } from 'react';
import { salaryApi } from '../../api/ViewerSalaryApi';
import type { SalaryCalculationResponse } from '../../api/salary';
import type { Job } from '../../api/jobs';
import { updateCommentsWithSalaryCalc, type CalcMode, type SalaryCalculatorParams } from './salaryFormatters';
import { SalaryCalculatorControls } from './SalaryCalculatorControls';
import { SalaryCalculatorResults } from './SalaryCalculatorResults';
import '../Filters.css';
import './SalaryCalculator.css';

interface SalaryCalculatorProps {
    onClose?: () => void;
    job?: Job;
    onUpdate?: (data: Partial<Job>) => void;
    initialParams?: SalaryCalculatorParams | null;
    allSavedParams?: SalaryCalculatorParams[];
}

const formatSavedLabel = (params: SalaryCalculatorParams): string => {
    const rate = params.calcRateType === 'Hourly' ? `${params.calcRate}€/h` : `${params.calcRate}€/d`;
    return `${params.calcMode} · ${rate}`;
};

export default function SalaryCalculator({ onClose, job, onUpdate, initialParams, allSavedParams = [] }: SalaryCalculatorProps) {
    const [calcMode, setCalcMode] = useState<CalcMode>(initialParams?.calcMode ?? 'classic');
    const [calcRate, setCalcRate] = useState(initialParams?.calcRate ?? 40);
    const [calcRateType, setCalcRateType] = useState<'Hourly' | 'Daily'>(initialParams?.calcRateType ?? 'Hourly');
    const [calcFreelanceRate, setCalcFreelanceRate] = useState(initialParams?.calcFreelanceRate ?? 80);
    const [calcHoursPerWeek, setCalcHoursPerWeek] = useState(initialParams?.calcHoursPerWeek ?? 40);
    const [calcDaysPerMonth, setCalcDaysPerMonth] = useState(initialParams?.calcDaysPerMonth ?? 20);
    const [calcResult, setCalcResult] = useState<SalaryCalculationResponse | null>(null);

    const loadSavedParams = (index: number) => {
        const params = allSavedParams[index];
        if (!params) return;
        setCalcMode(params.calcMode);
        setCalcRate(params.calcRate);
        setCalcRateType(params.calcRateType);
        setCalcFreelanceRate(params.calcFreelanceRate);
        setCalcHoursPerWeek(params.calcHoursPerWeek);
        setCalcDaysPerMonth(params.calcDaysPerMonth);
    };

    const deferredCalcRate = useDeferredValue(calcRate);
    const deferredCalcRateType = useDeferredValue(calcRateType);
    const deferredCalcFreelanceRate = useDeferredValue(calcFreelanceRate);
    const deferredCalcMode = useDeferredValue(calcMode);
    const deferredCalcHoursPerWeek = useDeferredValue(calcHoursPerWeek);
    const deferredCalcDaysPerMonth = useDeferredValue(calcDaysPerMonth);

    const handleSave = () => {
        if (job && onUpdate) {
            const newParams = { calcMode, calcRate, calcRateType, calcFreelanceRate, calcHoursPerWeek, calcDaysPerMonth };
            const updatedComments = updateCommentsWithSalaryCalc(job.comments || '', newParams);
            onUpdate({ comments: updatedComments });
        }
    };

    useEffect(() => {
        const calculate = async () => {
            try {
                let hoursPerDay = 8;
                let rateToUse = deferredCalcRate;
                let rateTypeToUse = deferredCalcRateType;
                if (deferredCalcMode === 'hoursPerWeek') {
                    hoursPerDay = deferredCalcHoursPerWeek / 5;
                    rateTypeToUse = 'Hourly';
                } else if (deferredCalcMode === 'daysPerMonth') {
                    rateToUse = (deferredCalcDaysPerMonth / 23.3) * deferredCalcRate;
                    rateTypeToUse = 'Daily';
                }
                const result = await salaryApi.calculate({
                    rate: rateToUse,
                    rate_type: rateTypeToUse,
                    hours_x_day: hoursPerDay,
                    freelance_rate: deferredCalcFreelanceRate
                });
                setCalcResult(result);
            } catch (error) {
                console.error('Error calculating salary:', error);
            }
        };
        const debounce = setTimeout(calculate, 500);
        return () => clearTimeout(debounce);
    }, [deferredCalcRate, deferredCalcRateType, deferredCalcFreelanceRate, deferredCalcMode, deferredCalcHoursPerWeek, deferredCalcDaysPerMonth]);

    return (
        <div className="salary-calculator boolean-filters">
            <div className="salary-calculator-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 className="section-label salary-calculator-title">Salary Calculator</h3>
                {onClose && (
                    <button 
                        onClick={onClose}
                        className="close-btn"
                        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', padding: '0 5px' }}
                        aria-label="Close calculator">
                        ✖</button>
                )}
            </div>
            <SalaryCalculatorControls
                savedSelector={allSavedParams.length > 1 ? (
                    <div className="compact-filter">
                        <select
                            className="compact-select"
                            defaultValue=""
                            onChange={(e) => { loadSavedParams(Number(e.target.value)); e.target.value = ''; }}>
                            <option value="" disabled>Saved...</option>
                            {allSavedParams.map((p, i) => (
                                <option key={i} value={i}>{formatSavedLabel(p)}</option>
                            ))}
                        </select>
                    </div>
                ) : undefined}
                calcMode={calcMode}
                setCalcMode={setCalcMode}
                calcRate={calcRate}
                setCalcRate={setCalcRate}
                calcRateType={calcRateType}
                setCalcRateType={setCalcRateType}
                calcFreelanceRate={calcFreelanceRate}
                setCalcFreelanceRate={setCalcFreelanceRate}
                calcHoursPerWeek={calcHoursPerWeek}
                setCalcHoursPerWeek={setCalcHoursPerWeek}
                calcDaysPerMonth={calcDaysPerMonth}
                setCalcDaysPerMonth={setCalcDaysPerMonth}
            >
                {job && onUpdate && (
                    <button 
                        onClick={handleSave}
                        className="config-btn salary-toggle-btn"
                        title="Save calculation to job comments">
                        💾 Save
                    </button>
                )}
            </SalaryCalculatorControls>
            <SalaryCalculatorResults calcResult={calcResult} />
        </div>
    );
}
