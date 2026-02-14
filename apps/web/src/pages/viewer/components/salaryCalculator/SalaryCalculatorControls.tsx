type CalcMode = 'classic' | 'hoursPerWeek' | 'daysPerMonth';

interface SalaryCalculatorControlsProps {
    calcMode: CalcMode;
    setCalcMode: (mode: CalcMode) => void;
    calcRate: number;
    setCalcRate: (rate: number) => void;
    calcRateType: 'Hourly' | 'Daily';
    setCalcRateType: (type: 'Hourly' | 'Daily') => void;
    calcFreelanceRate: number;
    setCalcFreelanceRate: (rate: number) => void;
    calcHoursPerWeek: number;
    setCalcHoursPerWeek: (hours: number) => void;
    calcDaysPerMonth: number;
    setCalcDaysPerMonth: (days: number) => void;
}

function ModeSelector({ value, onChange }: { value: CalcMode; onChange: (v: CalcMode) => void }) {
    return (
        <div className="compact-filter">
            Mode:
            <select className="compact-select" value={value} onChange={(e) => onChange(e.target.value as CalcMode)}>
                <option value="classic">Classic</option>
                <option value="hoursPerWeek">Hours/Week</option>
                <option value="daysPerMonth">Days/Month</option>
            </select>
        </div>
    );
}

function RateInput({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
    return (
        <div className="compact-filter">
            {label}:
            <input className="compact-input salary-rate-input" type="number" value={value} onChange={(e) => onChange(Number(e.target.value))} />
        </div>
    );
}

function RateTypeSelector({ value, onChange }: { value: 'Hourly' | 'Daily'; onChange: (v: 'Hourly' | 'Daily') => void }) {
    return (
        <div className="compact-filter">
            Type:
            <select className="compact-select" value={value} onChange={(e) => onChange(e.target.value as 'Hourly' | 'Daily')}>
                <option value="Hourly">Hourly</option>
                <option value="Daily">Daily</option>
            </select>
        </div>
    );
}

function FreelanceSelector({ value, onChange }: { value: number; onChange: (v: number) => void }) {
    return (
        <div className="compact-filter">
            Month Rate (Freelance):
            <select className="compact-select" value={value} onChange={(e) => onChange(Number(e.target.value))}>
                <option value="80">80</option>
                <option value="300">300</option>
            </select>
        </div>
    );
}

export function SalaryCalculatorControls(props: SalaryCalculatorControlsProps) {
    const { calcMode, setCalcMode, calcRate, setCalcRate, calcRateType, setCalcRateType, calcFreelanceRate, setCalcFreelanceRate, calcHoursPerWeek, setCalcHoursPerWeek, calcDaysPerMonth, setCalcDaysPerMonth } = props;

    return (
        <div className="salary-calculator-controls general-filters salary-calculator-controls-override">
            <ModeSelector value={calcMode} onChange={setCalcMode} />

            {calcMode === 'classic' && (
                <>
                    <RateInput label="Rate" value={calcRate} onChange={setCalcRate} />
                    <RateTypeSelector value={calcRateType} onChange={setCalcRateType} />
                </>
            )}
            {calcMode === 'hoursPerWeek' && (
                <>
                    <RateInput label="Hourly Rate" value={calcRate} onChange={setCalcRate} />
                    <RateInput label="Hours/Week" value={calcHoursPerWeek} onChange={setCalcHoursPerWeek} />
                </>
            )}
            {calcMode === 'daysPerMonth' && (
                <>
                    <RateInput label="Daily Rate" value={calcRate} onChange={setCalcRate} />
                    <RateInput label="Days/Month" value={calcDaysPerMonth} onChange={setCalcDaysPerMonth} />
                </>
            )}

            <FreelanceSelector value={calcFreelanceRate} onChange={setCalcFreelanceRate} />
        </div>
    );
}
