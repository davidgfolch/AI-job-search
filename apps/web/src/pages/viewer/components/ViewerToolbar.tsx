import ViewTabs from './ViewTabs';
import JobActions from './JobActions';
import type { Job, JobListParams } from '../api/ViewerApi';
import type { TabType } from '../hooks/useViewer';

interface ViewerToolbarProps {
    activeTab: TabType;
    onTabChange: (tab: TabType) => void;
    onDelete: (count: number) => void;
    selectedCount: number;
    hasSelection: boolean;
    loadedCount: number;
    totalCount: number;
    isLoadingMore: boolean;
    job: Job | null;
    filters: JobListParams;
    onSeen: () => void;
    onApplied: () => void;
    onDiscarded: () => void;
    onClosed: () => void;
    onIgnore: () => void;
    onNext: () => void;
    onPrevious: () => void;
    hasNext: boolean;
    hasPrevious: boolean;
    isBulk: boolean;
    onCloseMobile: () => void;
    showDetailClose: boolean;
}

export default function ViewerToolbar({ activeTab, onTabChange, onDelete, selectedCount, hasSelection, loadedCount, totalCount, isLoadingMore, job, filters, onSeen, onApplied, onDiscarded, onClosed, onIgnore, onNext, onPrevious, hasNext, hasPrevious, isBulk, onCloseMobile, showDetailClose }: ViewerToolbarProps) {
    return (
        <div id="viewer-toolbar" className="viewer-toolbar">
            <div className="tab-buttons">
                <ViewTabs activeTab={activeTab} onTabChange={onTabChange} onDelete={onDelete} selectedCount={selectedCount} hasSelection={hasSelection} />
                {activeTab === 'list' && (
                    <div className="list-summary">
                        <div className="spinner" style={{ position: 'relative', float: 'left', visibility: isLoadingMore ? 'visible' : 'hidden' }}></div>
                        <span className="green">{loadedCount}</span>/<span className="green">{totalCount}</span> loaded
                        <br/>
                        <span className="green">{selectedCount}</span> Selected
                    </div>
                )}
                {hasSelection && (
                    <div className="list-header-actions">
                        <JobActions job={job} filters={filters} onSeen={onSeen} onApplied={onApplied} onDiscarded={onDiscarded} onClosed={onClosed} onIgnore={onIgnore} onNext={onNext} onPrevious={onPrevious} hasNext={hasNext} hasPrevious={hasPrevious} isBulk={isBulk} />
                    </div>
                )}
                {showDetailClose && (
                    <button id="detail-close-button" className="tab-button detail-close-button" onClick={onCloseMobile} title="Close detail" aria-label="Close detail">✕</button>
                )}
            </div>
        </div>
    );
}
