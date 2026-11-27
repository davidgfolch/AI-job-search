import type { RefObject } from 'react';
import type { Job } from '../api/ViewerApi';
import JobDetail from './JobDetail';

interface JobDetailPanelsProps {
    mobileHidden?: boolean;
    selectedJob: Job | null;
    duplicatedJob: Job | null;
    collapsedPanel: 'none' | 'left' | 'right';
    detailScrollRef?: RefObject<HTMLDivElement | null>;
    onUpdate: (data: Partial<Job>) => void;
    onOpenDuplicated: (id: number) => void;
    onCloseDuplicated: () => void;
}

export default function JobDetailPanels({
    mobileHidden, selectedJob, duplicatedJob, collapsedPanel, detailScrollRef,
    onUpdate, onOpenDuplicated, onCloseDuplicated,
}: JobDetailPanelsProps) {
    return (
        <div id="viewer-right" className={`viewer-right ${!selectedJob || mobileHidden ? 'mobile-hidden' : ''}`}
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