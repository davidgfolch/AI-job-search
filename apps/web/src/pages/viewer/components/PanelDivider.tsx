import './PanelDivider.css';
import type { ResizeHandleProps } from '../hooks/usePanelResize';

interface PanelDividerProps {
    collapsedPanel: 'none' | 'left' | 'right';
    onCollapse: (panel: 'left' | 'right') => void;
    onReset: () => void;
    listRatio: number;
    resizeHandleProps: ResizeHandleProps;
    isDragging: boolean;
    resizeEnabled: boolean;
}

export default function PanelDivider({ collapsedPanel, onCollapse, onReset, listRatio, resizeHandleProps, isDragging, resizeEnabled }: PanelDividerProps) {
    const leftCollapsed = collapsedPanel === 'left';
    const rightCollapsed = collapsedPanel === 'right';
    const dragHandle = (
        <div id="panel-resize-handle" className={`divider-drag-handle${isDragging ? ' dragging' : ''}`}
            role="separator" aria-orientation="vertical" aria-label="Resize list and detail panels"
            aria-valuenow={Math.round(listRatio * 100)} aria-valuemin={20} aria-valuemax={80}
            aria-disabled={!resizeEnabled} tabIndex={resizeEnabled ? 0 : -1}
            title="Drag or use arrow keys to resize the panels"
            onDoubleClick={onReset}
            {...resizeHandleProps} />
    );

    return (
        <div id="panel-divider" className={`viewer-divider${isDragging ? ' dragging' : ''}`}>
            {dragHandle}
            <div className="divider-buttons">
                {collapsedPanel !== 'none' && <button id="panel-reset" className="reset-btn" onClick={onReset} title="Show both panels">↔</button>}
                <button id="panel-collapse-list" className={`collapse-btn${leftCollapsed ? ' active' : ''}`} onClick={() => onCollapse('left')}
                    title={leftCollapsed ? 'Restore list' : 'Collapse list'} aria-pressed={leftCollapsed}>&lt;</button>
                <button id="panel-collapse-detail" className={`collapse-btn${rightCollapsed ? ' active' : ''}`} onClick={() => onCollapse('right')}
                    title={rightCollapsed ? 'Restore detail' : 'Collapse detail'} aria-pressed={rightCollapsed}>&gt;</button>
            </div>
        </div>
    );
}
