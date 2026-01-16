import { useViewer } from '../hooks/useViewer';
import JobList from '../components/JobList';
import JobDetail from '../components/JobDetail';
import JobEditForm from '../components/JobEditForm';
import JobActions from '../components/JobActions';
import Filters from '../components/Filters';
import MessageContainer from '../components/core/MessageContainer';
import ViewTabs from '../components/ViewTabs';
import ConfirmModal from '../components/core/ConfirmModal';
import './Viewer.css';

export default function Viewer() {
    const { state, status, actions } = useViewer();
    const isBulk = state.selectionMode === 'all' || state.selectedIds.size > 1;

    return (
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
                    onFiltersChange={(newFilters) => actions.setFilters({ ...state.filters, ...newFilters, page: 1 })}
                    onMessage={(text, type) => actions.setMessage({ text, type })} 
                    onConfigNameChange={actions.setActiveConfigName} />
                <div className="viewer-content">
                    <div className="viewer-left">
                        <div className="tab-group">
                            <div className="tab-buttons">
                                <ViewTabs 
                                    activeTab={state.activeTab} 
                                    onTabChange={actions.setActiveTab} 
                                    hasNewJobs={state.hasNewJobs}
                                    newJobsCount={state.newJobsCount}
                                    onReload={actions.refreshJobs}
                                />
                                {state.activeTab === 'list' && (
                                    <div className="list-summary">
                                        <span className="green">{state.allJobs.length}</span>/<span className="green">{state.data?.total || 0}</span>&nbsp;loaded |&nbsp;
                                        <span className="green">{state.selectionMode === 'all' ? (state.data?.total || 0) : state.selectedIds.size}</span>&nbsp;Selected
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
                                        isLoadingMore={status.isLoadingMore}
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
                    <div className="viewer-right">
                        {state.selectedJob ? (
                            <JobDetail 
                                key={state.selectedJob.id}
                                job={state.selectedJob} 
                                onUpdate={actions.updateJob} 
                                onCreateNew={() => actions.setActiveTab('create')}
                                onDelete={actions.deleteJob}
                            />
                        ) : (
                            <div className="no-selection">
                                Select a job to view details
                                <br/>
                                <button className="create-job-btn" style={{ marginTop: '20px' }}
                                    onClick={() => actions.setActiveTab('create')}>
                                    Create Job
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
