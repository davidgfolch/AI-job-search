import { BOOLEAN_FILTERS } from '../constants';

interface StatusButtonsProps {
    statusState: Record<string, boolean>;
    handleStatusToggle: (key: string) => void;
}

export default function StatusButtons({ statusState, handleStatusToggle }: StatusButtonsProps) {
    return (
        <div className="status-form">
            <div className="status-pills">
                {BOOLEAN_FILTERS.map((filter: { key: string, label: string }) => (
                    <button key={filter.key} className={`status-pill ${statusState[filter.key] ? 'active' : ''}`}
                        onClick={() => handleStatusToggle(filter.key as string)}
                        type="button">
                        {filter.label}
                    </button>
                ))}
            </div>
        </div>
    );
}
