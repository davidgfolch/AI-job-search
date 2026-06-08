import './PanelDivider.css';

interface PanelDividerProps {
    collapsedPanel: 'none' | 'left' | 'right';
    onCollapse: (panel: 'left' | 'right') => void;
    onReset: () => void;
}

export default function PanelDivider({ collapsedPanel, onCollapse, onReset }: PanelDividerProps) {
    return (
        <div className="viewer-divider">
            {collapsedPanel === 'none' ? (
                <>
                    <button className="collapse-btn" onClick={() => onCollapse('left')} title="Collapse list">&lt;</button>
                    <button className="collapse-btn" onClick={() => onCollapse('right')} title="Collapse detail">&gt;</button>
                </>
            ) : (
                <>
                    <button className="reset-btn" onClick={onReset} title="Show both panels">↔</button>
                    {collapsedPanel === 'left' ? (
                        <button className="collapse-btn" onClick={() => onCollapse('right')} title="Collapse detail">&gt;</button>
                    ) : (
                        <button className="collapse-btn" onClick={() => onCollapse('left')} title="Collapse list">&lt;</button>
                    )}
                </>
            )}
        </div>
    );
}
