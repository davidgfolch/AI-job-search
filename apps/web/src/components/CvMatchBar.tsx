import './CvMatchBar.css';

interface CvMatchBarProps {
    percentage: number;
}

export default function CvMatchBar({ percentage }: CvMatchBarProps) {
    const clampedPercentage = Math.min(100, Math.max(0, percentage));
    return (
        <div className="cv-match-bar-container" title={`${percentage}% Match`}>
            <div 
                className="cv-match-bar-fill" 
                style={{ width: `${clampedPercentage}%` }}
            />
            <span className="cv-match-text">{percentage}%</span>
        </div>
    );
}
