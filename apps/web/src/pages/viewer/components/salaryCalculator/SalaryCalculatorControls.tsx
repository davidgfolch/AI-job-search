type CalcMode = 'classic' | 'hoursPerWeek' | 'daysPerMonth';
import { FormField } from '../../../common/components/core/FormField';

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
    savedSelector?: React.ReactNode;
    children?: React.ReactNode;
}

function ModeSelector({ value, onChange }: { value: CalcMode; onChange: (v: CalcMode) => void }) {
    return (
        <FormField id="calc-mode" label="Mode:" className="compact-filter">
            <select id="calc-mode" name="calc-mode" className="compact-select" value={value} onChange={(e) => onChange(e.target.value as CalcMode)}>
                <option value="classic">Classic</option>
                <option value="hoursPerWeek">Hours/Week</option>
                <option value="daysPerMonth">Days/Month</option>
            </select>
        </FormField>
    );
}

function RateInput({ label, id, name, value, onChange }: { label: string; id: string; name: string; value: number; onChange: (v: number) => void }) {
    return (
        <FormField id={id} label={`${label}:`} className="compact-filter">
            <input id={id} name={name} className="compact-input salary-rate-input" type="number" value={value} onChange={(e) => onChange(Number(e.target.value))} />
        </FormField>
    );
}

function RateTypeSelector({ value, onChange }: { value: 'Hourly' | 'Daily'; onChange: (v: 'Hourly' | 'Daily') => void }) {
    return (
        <FormField id="calc-rate-type" label="Type:" className="compact-filter">
            <select id="calc-rate-type" name="calc-rate-type" className="compact-select" value={value} onChange={(e) => onChange(e.target.value as 'Hourly' | 'Daily')}>
                <option value="Hourly">Hourly</option>
                <option value="Daily">Daily</option>
            </select>
        </FormField>
    );
}

function FreelanceSelector({ value, onChange }: { value: number; onChange: (v: number) => void }) {
    return (
        <FormField id="calc-freelance-rate" label="Month Rate (Freelance):" className="compact-filter">
            <select id="calc-freelance-rate" name="calc-freelance-rate" className="compact-select" value={value} onChange={(e) => onChange(Number(e.target.value))}>
                <option value="80">80</option>
                <option value="300">300</option>
            </select>
        </FormField>
    );
}

export function SalaryCalculatorControls(props: SalaryCalculatorControlsProps) {
    const { calcMode, setCalcMode, calcRate, setCalcRate, calcRateType, setCalcRateType, calcFreelanceRate, setCalcFreelanceRate, calcHoursPerWeek, setCalcHoursPerWeek, calcDaysPerMonth, setCalcDaysPerMonth, savedSelector, children } = props;

    return (
        <div className="salary-calculator-controls general-filters salary-calculator-controls-override">
            {savedSelector}
            <ModeSelector value={calcMode} onChange={setCalcMode} />

            {calcMode === 'classic' && (
                <>
                    <RateInput id="calc-rate-classic" name="calc-rate-classic" label="Rate" value={calcRate} onChange={setCalcRate} />
                    <RateTypeSelector value={calcRateType} onChange={setCalcRateType} />
                </>
            )}
            {calcMode === 'hoursPerWeek' && (
                <>
                    <RateInput id="calc-hourly-rate" name="calc-hourly-rate" label="Hourly Rate" value={calcRate} onChange={setCalcRate} />
                    <RateInput id="calc-hours-week" name="calc-hours-week" label="Hours/Week" value={calcHoursPerWeek} onChange={setCalcHoursPerWeek} />
                </>
            )}
            {calcMode === 'daysPerMonth' && (
                <>
                    <RateInput id="calc-daily-rate" name="calc-daily-rate" label="Daily Rate" value={calcRate} onChange={setCalcRate} />
                    <RateInput id="calc-days-month" name="calc-days-month" label="Days/Month" value={calcDaysPerMonth} onChange={setCalcDaysPerMonth} />
                </>
            )}

            <FreelanceSelector value={calcFreelanceRate} onChange={setCalcFreelanceRate} />
            {children}
        </div>
    );
}
