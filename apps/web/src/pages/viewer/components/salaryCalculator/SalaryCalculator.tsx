import { useState, useEffect, useDeferredValue } from 'react';
import { salaryApi } from '../../api/ViewerSalaryApi';
import type { SalaryCalculationResponse } from '../../api/salary';
import type { Job } from '../../api/jobs';
import { formatCalculationForComments, removePreviousSalaryCalculation } from './salaryFormatters';
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
                // Calculate hours_x_day based on mode
                if (deferredCalcMode === 'hoursPerWeek') {
                    // N hours per week / 5 days = hours per day
                    hoursPerDay = deferredCalcHoursPerWeek / 5;
                    rateTypeToUse = 'Hourly';
                } else if (deferredCalcMode === 'daysPerMonth') {
                    // N days per month, use daily rate
                    // Backend expects hours_x_day, but for daily rate it's not used
                    // We need to adjust the calculation: rate * N days * 11 months
                    // Since backend does: rate * 23.3 * 11
                    // We can adjust the rate: (N / 23.3) * rate
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
        const debounce = setTimeout(calculate, 500); // 500ms debounce to avoid spamming while typing
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
            <div className="salary-calculator-controls general-filters salary-calculator-controls-override">
                <div className="compact-filter">
                    Mode:
                    <select
                        className="compact-select"
                        value={calcMode}
                        onChange={(e) => setCalcMode(e.target.value as CalcMode)}>
                        <option value="classic">Classic</option>
                        <option value="hoursPerWeek">Hours/Week</option>
                        <option value="daysPerMonth">Days/Month</option>
                    </select>
                </div>

                {calcMode === 'classic' && (
                    <>
                        <div className="compact-filter">
                            Rate:
                            <input
                                className="compact-input salary-rate-input"
                                type="number"
                                value={calcRate}
                                onChange={(e) => setCalcRate(Number(e.target.value))}/>
                        </div>
                        <div className="compact-filter">
                            Type:
                            <select
                                className="compact-select"
                                value={calcRateType}
                                onChange={(e) => setCalcRateType(e.target.value as 'Hourly' | 'Daily')}>
                                <option value="Hourly">Hourly</option>
                                <option value="Daily">Daily</option>
                            </select>
                        </div>
                    </>
                )}
                {calcMode === 'hoursPerWeek' && (
                    <>
                        <div className="compact-filter">
                            Hourly Rate:
                            <input
                                className="compact-input salary-rate-input"
                                type="number"
                                value={calcRate}
                                onChange={(e) => setCalcRate(Number(e.target.value))}
                            />
                        </div>
                        <div className="compact-filter">
                            Hours/Week:
                            <input
                                className="compact-input salary-rate-input"
                                type="number"
                                value={calcHoursPerWeek}
                                onChange={(e) => setCalcHoursPerWeek(Number(e.target.value))}
                            />
                        </div>
                    </>
                )}
                {calcMode === 'daysPerMonth' && (
                    <>
                        <div className="compact-filter">
                            Daily Rate:
                            <input
                                className="compact-input salary-rate-input"
                                type="number"
                                value={calcRate}
                                onChange={(e) => setCalcRate(Number(e.target.value))}/>
                        </div>
                        <div className="compact-filter">
                            Days/Month:
                            <input
                                className="compact-input salary-rate-input"
                                type="number"
                                value={calcDaysPerMonth}
                                onChange={(e) => setCalcDaysPerMonth(Number(e.target.value))}/>
                        </div>
                    </>
                )}

                <div className="compact-filter">
                    Month Rate (Freelance):
                    <select
                        className="compact-select"
                        value={calcFreelanceRate}
                        onChange={(e) => setCalcFreelanceRate(Number(e.target.value))}>
                        <option value="80">80</option>
                        <option value="300">300</option>
                    </select>
                </div>
            </div>
            {calcResult && (
                <div className="salary-calculator-results">
                    <div>Gr/ year: <span className="salary-value">{calcResult.gross_year}</span> <span className="salary-equation">({calcResult.parsed_equation})</span></div>
                    <div>Tax year: <span className="salary-value">{calcResult.year_tax}</span> <span className="salary-equation">({calcResult.year_tax_equation})</span></div>
                    <div>Net year: <span className="salary-value">{calcResult.net_year}</span> <span className="salary-equation">({calcResult.gross_year} - {calcResult.year_tax} - {calcResult.freelance_tax})</span></div>
                    <div>Net month: <span className="salary-value">{calcResult.net_month}</span></div>
                    {job && onUpdate && (
                        <button 
                            onClick={handleSave}
                            className="config-btn salary-toggle-btn"
                            style={{ marginTop: '10px' }}
                            title="Save calculation to job comments">
                            💾 Save to Comments
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
