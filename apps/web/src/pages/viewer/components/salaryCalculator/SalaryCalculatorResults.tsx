import type { SalaryCalculationResponse } from '../../api/salary';

interface SalaryCalculatorResultsProps {
    calcResult: SalaryCalculationResponse | null;
}

export function SalaryCalculatorResults({ calcResult }: SalaryCalculatorResultsProps) {
    if (!calcResult) return null;

    return (
        <div className="salary-calculator-results">
            <div>Gr/ year: <span className="salary-value">{calcResult.gross_year}</span> <span className="salary-equation">({calcResult.parsed_equation})</span></div>
            <div>Tax year: <span className="salary-value">{calcResult.year_tax}</span> <span className="salary-equation">({calcResult.year_tax_equation})</span></div>
            <div>Net year: <span className="salary-value">{calcResult.net_year}</span> <span className="salary-equation">({calcResult.gross_year} - {calcResult.year_tax} - {calcResult.freelance_tax})</span></div>
            <div>Net month: <span className="salary-value">{calcResult.net_month}</span></div>
        </div>
    );
}
