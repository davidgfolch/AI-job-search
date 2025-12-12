import { useViewer } from '../hooks/useViewer';
import JobList from '../components/JobList';
import JobDetail from '../components/JobDetail';
import JobEditForm from '../components/JobEditForm';
import JobActions from '../components/JobActions';
import Filters from '../components/Filters';
import MessageContainer from '../components/MessageContainer';
import ViewTabs from '../components/ViewTabs';
import './Viewer.css';

export default function Viewer() {
    const { state, status, actions } = useViewer();

    return (
        <div className="viewer">
            <div className="viewer-container">
                <MessageContainer message={state.message} error={status.error}
                    onDismissMessage={() => actions.setMessage(null)} />
                <Filters filters={state.filters}
                    onFiltersChange={(newFilters) => actions.setFilters({ ...state.filters, ...newFilters, page: 1 })}
                    onMessage={(text, type) => actions.setMessage({ text, type })} />
                <div className="viewer-content">
                    <div className="viewer-left">
                        <div className="tab-group">
                            <div className="tab-buttons">
                                <ViewTabs activeTab={state.activeTab} onTabChange={actions.setActiveTab} />
                                {state.selectedJob && (
                                    <JobActions
                                        job={state.selectedJob}
                                        filters={state.filters}
                                        onSeen={actions.seenJob}
                                        onApplied={actions.appliedJob}
                                        onDiscarded={actions.discardedJob}
                                        onClosed={actions.closedJob}
                                        onIgnore={actions.ignoreJob}
                                        onNext={actions.nextJob}
                                        onPrevious={actions.previousJob}
                                        hasNext={status.hasNext}
                                        hasPrevious={status.hasPrevious}
                                    />
                                )}
                            </div>
                            <div className="tab-content">
                                {state.activeTab === 'list' ? (
                                    <JobList
                                        isLoading={status.isLoading}
                                        error={status.error}
                                        jobs={state.allJobs}
                                        selectedJob={state.selectedJob}
                                        onJobSelect={actions.selectJob}
                                        onLoadMore={actions.loadMore}
                                        isLoadingMore={status.isLoadingMore}
                                        totalResults={state.data?.total || 0}
                                        hasMore={state.allJobs.length < (state.data?.total || 0)}
                                    />
                                ) : (<JobEditForm job={state.selectedJob} onUpdate={actions.updateJob} />
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="viewer-right">
                        {state.selectedJob ? <JobDetail job={state.selectedJob} /> : <div className="no-selection">Select a job to view details</div>}
                    </div>
                </div>
            </div>
        </div>
    );
}
