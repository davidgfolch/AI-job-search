import type { RefObject } from 'react';
import type { Job, JobListParams } from '../api/ViewerApi';
import JobDetail from './JobDetail';

interface JobDetailPanelsProps {
    selectedJob: Job | null;
    duplicatedJob: Job | null;
    collapsedPanel: 'none' | 'left' | 'right';
    filters?: JobListParams;
    detailScrollRef?: RefObject<HTMLDivElement | null>;
    onUpdate: (data: Partial<Job>) => void;
    onOpenDuplicated: (id: number) => void;
    onCloseMobile: () => void;
    onCloseDuplicated: () => void;
    onNext: () => void;
    onPrevious: () => void;
    hasNext: boolean;
    hasPrevious: boolean;
    onSeen: () => void;
    onApplied: () => void;
    onDiscarded: () => void;
    onClosed: () => void;
    onIgnore: () => void;
}

export default function JobDetailPanels({
    selectedJob, duplicatedJob, collapsedPanel, filters, detailScrollRef,
    onUpdate, onOpenDuplicated, onCloseMobile, onCloseDuplicated, onNext, onPrevious,
    hasNext, hasPrevious, onSeen, onApplied, onDiscarded, onClosed, onIgnore,
}: JobDetailPanelsProps) {
    return (
        <div className={`viewer-right ${!selectedJob ? 'mobile-hidden' : ''}`}
            style={duplicatedJob ? { display: 'flex', gap: '1rem', flexDirection: 'row' } : collapsedPanel === 'right' ? { display: 'none' } : undefined}>
            {selectedJob ? (
                <>
                    <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                        <JobDetail
                            key={selectedJob.id}
                            job={selectedJob}
                            onUpdate={onUpdate}
                            onOpenDuplicated={onOpenDuplicated}
                            hideDuplicatedButton={!!duplicatedJob}
                            onCloseMobile={onCloseMobile}
                            onNext={onNext}
                            onPrevious={onPrevious}
                            hasNext={hasNext}
                            hasPrevious={hasPrevious}
                            filters={filters}
                            onSeen={onSeen}
                            onApplied={onApplied}
                            onDiscarded={onDiscarded}
                            onClosed={onClosed}
                            onIgnore={onIgnore}
                            detailScrollRef={detailScrollRef} />
                    </div>
                    {duplicatedJob && (
                        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', borderLeft: '1px solid var(--border-color)', paddingLeft: '1rem' }}>
                            <JobDetail
                                key={duplicatedJob.id}
                                job={duplicatedJob}
                                onUpdate={onUpdate} // Allows updating the duplicated job too
                                onClose={onCloseDuplicated}
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
    );
}