import { useViewer } from '../hooks/useViewer';
import JobList from '../components/JobList';
import JobDetail from '../components/JobDetail';
import JobEditForm from '../components/JobEditForm';
import JobActions from '../components/JobActions';
import Filters from '../components/Filters';
import Messages from '../components/Messages';
import './Viewer.css';

export default function Viewer() {
    const {
        filters,
        setFilters,
        allJobs,
        isLoadingMore,
        selectedJob,
        activeTab,
        setActiveTab,
        message,
        setMessage,
        isLoading,
        error,
        data,
        handleJobSelect,
        handleJobUpdate,
        handleIgnoreJob,
        handleSeenJob,
        handleAppliedJob,
        handleDiscardedJob,
        handleClosedJob,
        handleNextJob,
        handlePreviousJob,
        handleLoadMore,
        hasNext,
        hasPrevious,
    } = useViewer();

    return (
        <div className="viewer">
            <div className="viewer-container">
                {message && (<Messages message={message.text} type={message.type} onDismiss={() => setMessage(null)} />)}
                {error && (<Messages message={`Error loading jobs: ${String(error)}`} type="error" onDismiss={() => { }} />)}
                <Filters filters={filters} onFiltersChange={(newFilters) => setFilters({ ...filters, ...newFilters, page: 1 })}
                    onMessage={(text, type) => setMessage({ text, type })} />
                <div className="viewer-content">
                    <div className="viewer-left">
                        <div className="tab-group">
                            <div className="tab-buttons">
                                <button className={`tab-button ${activeTab === 'list' ? 'active' : ''}`} onClick={() => setActiveTab('list')}>
                                    List
                                </button>
                                <button className={`tab-button ${activeTab === 'edit' ? 'active' : ''}`} onClick={() => setActiveTab('edit')}>
                                    Edit
                                </button>
                                {selectedJob && (
                                    <JobActions
                                        job={selectedJob}
                                        filters={filters}
                                        onSeen={handleSeenJob}
                                        onApplied={handleAppliedJob}
                                        onDiscarded={handleDiscardedJob}
                                        onClosed={handleClosedJob}
                                        onIgnore={handleIgnoreJob}
                                        onNext={handleNextJob}
                                        onPrevious={handlePreviousJob}
                                        hasNext={hasNext}
                                        hasPrevious={hasPrevious}
                                    />
                                )}
                            </div>
                            <div className="tab-content">
                                {activeTab === 'list' ? (
                                    <JobList
                                        isLoading={isLoading}
                                        error={error}
                                        jobs={allJobs}
                                        selectedJob={selectedJob}
                                        onJobSelect={handleJobSelect}
                                        onLoadMore={handleLoadMore}
                                        isLoadingMore={isLoadingMore}
                                        totalResults={data?.total || 0}
                                        hasMore={allJobs.length < (data?.total || 0)}
                                    />
                                ) : (<JobEditForm job={selectedJob} onUpdate={handleJobUpdate} />
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="viewer-right">
                        {selectedJob ? <JobDetail job={selectedJob} /> : <div className="no-selection">Select a job to view details</div>}
                    </div>
                </div>
            </div>
        </div>
    );
}
