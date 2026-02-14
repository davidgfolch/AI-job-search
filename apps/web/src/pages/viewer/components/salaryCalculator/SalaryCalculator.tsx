import { useState, useEffect, useDeferredValue } from 'react';
import { salaryApi } from '../../api/ViewerSalaryApi';
import type { SalaryCalculationResponse } from '../../api/salary';
import type { Job } from '../../api/jobs';
import { formatCalculationForComments, removePreviousSalaryCalculation } from './salaryFormatters';
import { SalaryCalculatorControls } from './SalaryCalculatorControls';
import { SalaryCalculatorResults } from './SalaryCalculatorResults';
import '../Filters.css';
import './SalaryCalculator.css';

interface SalaryCalculatorProps {
    onClose?: () => void;
    job?: Job;
    onUpdate?: (data: Partial<Job>) => void;
}

type CalcMode = 'classic' | 'hoursPerWeek' | 'daysPerMonth';

export default function SalaryCalculator({ onClose, job, onUpdate }: SalaryCalculatorProps) {
    const [calcMode, setCalcMode] = useState<CalcMode>('classic');
    const [calcRate, setCalcRate] = useState(40);
    const [calcRateType, setCalcRateType] = useState<'Hourly' | 'Daily'>('Hourly');
    const [calcFreelanceRate, setCalcFreelanceRate] = useState(80);
    const [calcHoursPerWeek, setCalcHoursPerWeek] = useState(40);
    const [calcDaysPerMonth, setCalcDaysPerMonth] = useState(20);
    const [calcResult, setCalcResult] = useState<SalaryCalculationResponse | null>(null);

    const deferredCalcRate = useDeferredValue(calcRate);
    const deferredCalcRateType = useDeferredValue(calcRateType);
    const deferredCalcFreelanceRate = useDeferredValue(calcFreelanceRate);
    const deferredCalcMode = useDeferredValue(calcMode);
    const deferredCalcHoursPerWeek = useDeferredValue(calcHoursPerWeek);
    const deferredCalcDaysPerMonth = useDeferredValue(calcDaysPerMonth);

    const handleSave = () => {
        if (calcResult && job && onUpdate) {
            const formattedCalculation = formatCalculationForComments({
                result: calcResult,
                calcMode, calcRate, calcRateType, calcFreelanceRate,
                calcHoursPerWeek, calcDaysPerMonth
            });
            let updatedComments = removePreviousSalaryCalculation(job.comments || '');
            updatedComments += formattedCalculation;
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
            />
            <SalaryCalculatorResults
                calcResult={calcResult}
                showSaveButton={!!(job && onUpdate)}
                onSave={handleSave}
            />
        </div>
    );
}
