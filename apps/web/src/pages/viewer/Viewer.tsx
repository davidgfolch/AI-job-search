import { useViewer } from "./hooks/useViewer";
import { useCallback, useRef, useState } from "react";
import JobList from './components/JobList';
import JobEditForm from './components/JobEditForm';
import JobDetailPanels from './components/JobDetailPanels';
import ViewerToolbar from './components/ViewerToolbar';
import ShortcutBadge from './components/ShortcutBadge';
import AppliedModal from './components/AppliedModal';
import Filters from './components/Filters';
import MessageContainer from '../common/components/core/MessageContainer';
import PanelDivider from './components/PanelDivider';
import ConfirmModal from '../common/components/core/ConfirmModal';
import './Viewer.css';
import PageHeader from "../common/components/PageHeader";
import { BOOLEAN_FILTERS } from './constants';
import type { JobListParams } from './api/ViewerApi';
import { useDefaultComment } from '../common/hooks/useDefaultComment';
import { useJobShortcuts } from './hooks/useJobShortcuts';
import ShortcutsControls from './components/ShortcutsControls';
import { useViewerShortcuts } from './hooks/useViewerShortcuts';
import { ShortcutsContext } from './shortcutsContext';
import { usePanelResize } from './hooks/usePanelResize';

export default function Viewer() {
    const { state, status, actions } = useViewer();
    const { comment: defaultComment } = useDefaultComment();
    const isBulk = state.selectionMode === 'all' || state.selectedIds.size > 1;
    const jobListRef = useRef<HTMLDivElement>(null);
    const detailScrollRef = useRef<HTMLDivElement>(null);
    const [configCount, setConfigCount] = useState<number>();
    const { collapsedPanel, leftHidden, contentProps, dividerProps, resetPanels } = usePanelResize(!!state.duplicatedJob);
    const handleShortcut = useViewerShortcuts(actions, state.selectedJob, isBulk, jobListRef, detailScrollRef);
    const loadPinnedByPositionRef = useRef<(index: number) => void>(() => {});
    const [pinnedShortcuts, setPinnedShortcuts] = useState<{ name: string; index: number }[]>([]);
    const handlePinnedShortcutReady = useCallback((handler: (index: number) => void, shortcuts: { name: string; index: number }[]) => {
        loadPinnedByPositionRef.current = handler;
        setPinnedShortcuts(prev => {
            if (prev.length === shortcuts.length && prev.every((p, i) => p.name === shortcuts[i].name && p.index === shortcuts[i].index)) {
                return prev;
            }
            return shortcuts;
        });
    }, []);
    const handlePinnedConfigShortcut = useCallback((index: number) => {
        loadPinnedByPositionRef.current(index);
    }, []);
    const { enabled: shortcutsEnabled, toggleEnabled: toggleShortcuts, shortcuts, modifierPressed } = useJobShortcuts({ onAction: handleShortcut, onPinnedConfigShortcut: handlePinnedConfigShortcut });

    const handleFiltersChange = useCallback((newFilters: JobListParams) => {
        const isSearchOrFilterChange = newFilters.search !== state.filters.search || 
            BOOLEAN_FILTERS.some(filter => newFilters[filter.key] !== state.filters[filter.key]);
        const newPage = newFilters.page === 1 || isSearchOrFilterChange ? 1 : state.filters.page;        
        if (jobListRef.current) {
            jobListRef.current.scrollTop = 0;
        }
        actions.setFilters({ ...state.filters, ...newFilters, page: newPage });
    }, [actions.setFilters, state.filters]);
    const detailVisibleMobile = state.activeTab === 'list' && !!state.selectedJob;

const handleMessage = useCallback((text: string, type: 'success' | 'error') => {
        actions.setMessage({ text, type });
    }, [actions.setMessage]);

    return (
        <ShortcutsContext.Provider value={{ shortcuts, modifierPressed }}>
            <PageHeader title="Jobs">
                <ShortcutsControls enabled={shortcutsEnabled} onToggle={toggleShortcuts} shortcuts={shortcuts} pinnedShortcuts={pinnedShortcuts} />
            </PageHeader>
            <main className="app-main">
                <div className="viewer">
                    <ConfirmModal
                        isOpen={state.confirmModal.isOpen}
                        message={state.confirmModal.message}
                        onConfirm={state.confirmModal.onConfirm}
                        onCancel={actions.closeConfirmModal}
                    />
                    <AppliedModal
                        isOpen={state.appliedModal.isOpen}
                        defaultComment={defaultComment}
                        onConfirm={state.appliedModal.onConfirm}
                        onCancel={state.appliedModal.onCancel}
                    />
                    <div className="viewer-container">
                        <MessageContainer message={state.message} error={status.apiError || status.error}
                            onDismissMessage={actions.dismissMessage} />
                        <Filters filters={state.filters}
                            onFiltersChange={handleFiltersChange}
                            onMessage={handleMessage} 
                            onConfigNameChange={actions.setActiveConfigName}
                            onReloadConfig={actions.reloadJobList}
                            configCount={configCount}
                            onConfigsLoaded={setConfigCount}
                            onPinnedShortcutReady={handlePinnedShortcutReady}
                            modalityValues={state.modalityValues} />
                        <ViewerToolbar
                            activeTab={state.activeTab}
                            onTabChange={actions.setActiveTab}
                            onDelete={(count) => {
                                if (state.selectionMode === 'all' || state.selectedIds.size > 0) {
                                    actions.deleteSelected(count);
                                } else if (state.selectedJob) {
                                    actions.deleteJob();
                                }
                            }}
                            selectedCount={state.selectionMode === 'all' ? (state.data?.total || 0) : state.selectedIds.size}
                            hasSelection={!!(state.selectedJob || state.selectionMode === 'all' || state.selectedIds.size > 0)}
                            loadedCount={state.allJobs.length}
                            totalCount={state.data?.total || 0}
                            isLoadingMore={status.isLoadingMore}
                            job={state.selectedJob}
                            filters={state.filters}
                            onSeen={actions.seenJob}
                            onApplied={actions.appliedJob}
                            onDiscarded={actions.discardedJob}
                            onClosed={actions.closedJob}
                            onIgnore={isBulk ? actions.ignoreSelected : actions.ignoreJob}
                            onNext={actions.nextJob}
                            onPrevious={actions.previousJob}
                            hasNext={status.hasNext}
                            hasPrevious={status.hasPrevious}
                            isBulk={isBulk}
                            onCloseMobile={actions.closeSelectedJob}
                            showDetailClose={!!state.selectedJob && state.activeTab === 'list'}
                        />
                        <div className="viewer-content" {...contentProps}>
                            <div id="viewer-left" className={`viewer-left ${detailVisibleMobile ? 'mobile-hidden' : ''}`} style={{ display: leftHidden && state.activeTab === 'list' ? 'none' : 'flex' }}>
                                <div className="tab-group">
                                    <div className="tab-content">
                                        <div style={{ display: state.activeTab === 'list' ? 'flex' : 'none', flexDirection: 'column', height: '100%', overflow: 'hidden', position: 'relative' }}>
                                            <JobList
                                                isLoading={status.isLoading}
                                                error={status.apiError || status.error}
                                                jobs={state.allJobs}
                                                selectedJob={state.selectedJob}
                                                onJobSelect={actions.selectJob}
                                                onLoadMore={actions.loadMore}
                                                hasMore={state.allJobs.length < (state.data?.total || 0)}
                                                isLoadingMore={status.isLoadingMore}
                                                selectedIds={state.selectedIds}
                                                selectionMode={state.selectionMode}
                                                onToggleSelectJob={actions.toggleSelectJob}
                                                onToggleSelectAll={actions.toggleSelectAll}
                                                containerRef={jobListRef}
                                            />
                                            <ShortcutBadge display={shortcuts.listFocus.display} visible={modifierPressed} />
                                        </div>
                                        <div style={{ display: state.activeTab === 'create' ? 'block' : 'none', height: '100%' }}>
                                            <JobEditForm 
                                                job={null} 
                                                onUpdate={() => {}} 
                                                onCreate={actions.createJob} 
                                                mode="create" 
                                                key={state.creationSessionId}
                                            />
                                        </div>
                                        <div style={{ display: state.activeTab === 'edit' ? 'block' : 'none', height: '100%' }}>
                                            <JobEditForm job={state.selectedJob} onUpdate={actions.updateJob} />
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <PanelDivider {...dividerProps} onReset={resetPanels} />
                                <JobDetailPanels
                                    mobileHidden={!detailVisibleMobile}
                                    selectedJob={state.selectedJob}
                                    duplicatedJob={state.duplicatedJob}
                                    collapsedPanel={collapsedPanel}
                                    detailScrollRef={detailScrollRef}
                                    onUpdate={actions.updateJob}
                                    onOpenDuplicated={actions.openDuplicatedJob}
                                    onCloseDuplicated={actions.closeDuplicatedJob}
                                />
                        </div>
                    </div>
                </div>
            </main>
        </ShortcutsContext.Provider>
    );
}
