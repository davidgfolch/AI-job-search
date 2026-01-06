import { useState, useEffect } from 'react';
import { salaryApi } from '../api/salary';
import type { SalaryCalculationResponse } from '../api/salary';
import './Filters.css';
import './SalaryCalculator.css';

interface SalaryCalculatorProps {
    onClose?: () => void;
}

export default function SalaryCalculator({ onClose }: SalaryCalculatorProps) {
    const [calcRate, setCalcRate] = useState(40);
    const [calcRateType, setCalcRateType] = useState<'Hourly' | 'Daily'>('Hourly');
    const [calcFreelanceRate, setCalcFreelanceRate] = useState(80);
    const [calcResult, setCalcResult] = useState<SalaryCalculationResponse | null>(null);

    useEffect(() => {
        const calculate = async () => {
            try {
                const result = await salaryApi.calculate({
                    rate: calcRate,
                    rate_type: calcRateType,
                    hours_x_day: 8,
                    freelance_rate: calcFreelanceRate
                });
                setCalcResult(result);
            } catch (error) {
                console.error('Error calculating salary:', error);
            }
        };
        const debounce = setTimeout(calculate, 500); // 500ms debounce to avoid spamming while typing
        return () => clearTimeout(debounce);
    }, [calcRate, calcRateType, calcFreelanceRate]);

    return (
        <div className="salary-calculator boolean-filters">
            <div className="salary-calculator-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 className="section-label salary-calculator-title">Salary Calculator</h3>
                {onClose && (
                    <button 
                        onClick={onClose}
                        className="close-btn"
                        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', padding: '0 5px' }}
                        aria-label="Close calculator"
                    >
                        ✖
                    </button>
                )}
            </div>
            <div className="salary-calculator-controls general-filters salary-calculator-controls-override">
                <div className="compact-filter">
                    Rate:
                    <input
                        className="compact-input salary-rate-input"
                        type="number"
                        value={calcRate}
                        onChange={(e) => setCalcRate(Number(e.target.value))}
                    />
                </div>
                <div className="compact-filter">
                    Type:
                    <select
                        className="compact-select"
                        value={calcRateType}
                        onChange={(e) => setCalcRateType(e.target.value as 'Hourly' | 'Daily')}
                    >
                        <option value="Hourly">Hourly</option>
                        <option value="Daily">Daily</option>
                    </select>
                </div>
                <div className="compact-filter">
                    Month Rate (Freelance):
                    <select
                        className="compact-select"
                        value={calcFreelanceRate}
                        onChange={(e) => setCalcFreelanceRate(Number(e.target.value))}
                    >
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
                </div>
            )}
        </div>
    );
}
