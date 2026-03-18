interface CustomTooltipProps {
    active?: boolean;
    payload?: Array<{ color: string; name: string; value: number; payload: { otherDetails?: Record<string, number> } }>;
    label?: string;
    showDateLabel?: boolean;
}

const formatDate = (dateStr: string | number | undefined): string => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return String(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label, showDateLabel = true }) => {
    if (active && payload && payload.length) {
        return (
            <div style={{ backgroundColor: 'white', padding: '10px', border: '1px solid #ccc', color: "gray" }}>
                {showDateLabel && <p style={{ fontWeight: "bold" }}>{formatDate(label)}</p>}
                {payload.map((entry, index) => (
                    <div key={index} style={{ color: entry.color }}>
                        {entry.name}: {entry.value}
                        {entry.name === 'Other' && entry.payload.otherDetails && (
                            <div style={{ fontSize: '0.8em', marginLeft: '10px', color: '#666' }}>
                                {Object.entries(entry.payload.otherDetails).map(([source, count]) => (
                                    <div key={source}>{source}: {count as number}</div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

export default CustomTooltip;