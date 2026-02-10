import { useViewer } from "./hooks/useViewer";
import { useCallback } from "react";
import JobList from './components/JobList';
import JobDetail from './components/JobDetail';
import JobEditForm from './components/JobEditForm';
import JobActions from './components/JobActions';
import Filters from './components/Filters';
import MessageContainer from '../common/components/core/MessageContainer';
import ViewTabs from './components/ViewTabs';
import ConfirmModal from '../common/components/core/ConfirmModal';
import './Viewer.css';
import PageHeader from "../common/components/PageHeader";

export default function Viewer() {
    const { state, status, actions } = useViewer();
    const isBulk = state.selectionMode === 'all' || state.selectedIds.size > 1;

    const handleFiltersChange = useCallback((newFilters: any) => {
        actions.setFilters({ ...state.filters, ...newFilters, page: 1 });
    }, [actions.setFilters, state.filters]);

    const handleMessage = useCallback((text: string, type: 'success' | 'error') => {
        actions.setMessage({ text, type });
    }, [actions.setMessage]);

    return (
        <>
            <PageHeader title="Jobs"/>
            <main className="app-main">
                <div className="viewer">
                    <ConfirmModal
                        isOpen={state.confirmModal.isOpen}
                        message={state.confirmModal.message}
                        onConfirm={state.confirmModal.onConfirm}
                        onCancel={actions.closeConfirmModal}
                    />
                    <div className="viewer-container">
                        <MessageContainer message={state.message} error={status.error}
                            onDismissMessage={() => actions.setMessage(null)} />
                        <Filters filters={state.filters}
                            onFiltersChange={handleFiltersChange}
                            onMessage={handleMessage} 
                            onConfigNameChange={actions.setActiveConfigName} />
                        <div className="viewer-content">
                            <div className="viewer-left" style={{ display: state.mergedJob ? 'none' : 'flex' }}>
                                <div className="tab-group">
                                    <div className="tab-buttons">
                                        <ViewTabs 
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
                                        />
                                        {state.activeTab === 'list' && (
                                            <div className="list-summary">
                                                <div className="spinner" style={{position: 'relative', float: 'left', visibility: status.isLoadingMore ? 'visible' : 'hidden'}}></div>
                                                <span className="green">{state.allJobs.length}</span>/<span className="green">{state.data?.total || 0}</span> loaded
                                                <br/>
                                                <span className="green">{state.selectionMode === 'all' ? (state.data?.total || 0) : state.selectedIds.size}</span> Selected
                                            </div>
                                        )}
                                        {(state.selectedJob || state.selectionMode === 'all' || state.selectedIds.size > 0) && (
                                            <JobActions
                                                job={state.selectedJob}
                                                filters={state.filters}
                                                onSeen={actions.seenJob}
                                                onApplied={actions.appliedJob}
                                                onDiscarded={actions.discardedJob}
                                                onClosed={actions.closedJob}
                                                onIgnore={isBulk ? actions.ignoreSelected : actions.ignoreJob}
                                                onDelete={actions.deleteSelected}
                                                onNext={actions.nextJob}
                                                onPrevious={actions.previousJob}
                                                hasNext={status.hasNext}
                                                hasPrevious={status.hasPrevious}
                                                isBulk={isBulk}
                                                activeConfigName={state.activeConfigName}
                                                selectedCount={state.selectionMode === 'all' ? (state.data?.total || 0) : state.selectedIds.size}
                                            />
                                        )}
                                    </div>
                                    <div className="tab-content">
                                        <div style={{ display: state.activeTab === 'list' ? 'flex' : 'none', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                                            <JobList
                                                isLoading={status.isLoading}
                                                error={status.error}
                                                jobs={state.allJobs}
                                                selectedJob={state.selectedJob}
                                                onJobSelect={actions.selectJob}
                                                onLoadMore={actions.loadMore}
                                                hasMore={state.allJobs.length < (state.data?.total || 0)}
                                                selectedIds={state.selectedIds}
                                                selectionMode={state.selectionMode}
                                                onToggleSelectJob={actions.toggleSelectJob}
                                                onToggleSelectAll={actions.toggleSelectAll}
                                            />
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
                            <div className="viewer-right" style={state.mergedJob ? { display: 'flex', gap: '1rem', flexDirection: 'row' } : undefined}>
                                {state.selectedJob ? (
                                    <>
                                        <div style={state.mergedJob ? { flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' } : { flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                                            <JobDetail 
                                                key={state.selectedJob.id}
                                                job={state.selectedJob} 
                                                onUpdate={actions.updateJob} 
                                                onOpenMerged={actions.openMergedJob}
                                                hideMergedButton={!!state.mergedJob}
                                            />
                                        </div>
                                        {state.mergedJob && (
                                            <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', borderLeft: '1px solid var(--border-color)', paddingLeft: '1rem' }}>
                                                <JobDetail 
                                                    key={state.mergedJob.id}
                                                    job={state.mergedJob} 
                                                    onUpdate={actions.updateJob} // Allows updating the merged job too
                                                    onClose={actions.closeMergedJob}
                                                />
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <div className="no-selection">
                                        Select a job to view details
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </>
    );
}
