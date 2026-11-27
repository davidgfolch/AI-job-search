import './ToggleSwitch.css';

interface ToggleSwitchProps {
    checked: boolean;
    onChange: () => void;
    label: string;
    labelText?: string;
}

export default function ToggleSwitch({ checked, onChange, label, labelText }: ToggleSwitchProps) {
    return (
        <button type="button" className="toggle-switch" role="switch" aria-checked={checked} aria-label={label} title={label} onClick={onChange}>
            <span className="toggle-switch-track" aria-hidden="true"><span className="toggle-switch-knob" /></span>
            {labelText && <span className="toggle-switch-label">{labelText}</span>}
        </button>
    );
}
