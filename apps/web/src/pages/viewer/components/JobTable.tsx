import { useRef } from 'react';
import type { Job } from '../api/ViewerApi';
import './JobTable.css';
import { STATE_BASE_FIELDS } from '../constants';
import { useAutoLoadMore } from '../hooks/useAutoLoadMore';
import { useScrollSelectedIntoView } from '../hooks/useScrollSelectedIntoView';
import { calculateLapsedTime, calculateLapsedTimeDetail } from '../../common/utils/dateUtils';

interface JobTableProps {
    jobs: Job[];
    selectedJob: Job | null;
    onJobSelect: (job: Job) => void;
    onLoadMore?: () => void;
    hasMore?: boolean;
    isLoadingMore?: boolean;
    selectedIds: Set<number>;
    selectionMode: 'none' | 'manual' | 'all';
    onToggleSelectJob: (id: number) => void;
    onToggleSelectAll: () => void;
    containerRef: React.RefObject<HTMLDivElement>;
}

export default function JobTable({ 
    jobs, 
    selectedJob, 
    onJobSelect, 
    onLoadMore, 
    hasMore,
    isLoadingMore,
    selectedIds,
    selectionMode,
    onToggleSelectJob,
    onToggleSelectAll,
    containerRef,
}: JobTableProps) {
    const sentinelRef = useRef<HTMLDivElement>(null);
    const contentRef = useRef<HTMLTableElement>(null);

    useAutoLoadMore({
        contentRef,
        sentinelRef,
        itemCount: jobs.length,
        hasMore,
        isLoading: isLoadingMore,
        onLoadMore,
    });

    const selectedRowRef = useRef<HTMLTableRowElement>(null);

    useScrollSelectedIntoView({ containerRef, rowRef: selectedRowRef, selectedId: selectedJob?.id });

    return (
        <div className="job-table-container" ref={containerRef} tabIndex={-1}>
            <table className="job-table" ref={contentRef}>
                <thead>
                    <tr>
                        <th className="checkbox-column">
                            <input 
                                id="job-table-select-all"
                                name="select_all"
                                type="checkbox" 
                                checked={selectionMode === 'all'}
                                onChange={onToggleSelectAll}
                                title="Select All"
                            />
                        </th>
                        <th className="salary-column text-no-wrap">Salary</th>
                        <th className="title-column text-no-wrap">Title</th>
                        <th className="company-column text-no-wrap">Company</th>
                        <th className="status-column text-no-wrap">Status</th>
                        <th className="created-column text-no-wrap">Created</th>
                    </tr>
                </thead>
                <tbody>
                    {jobs.map((job) => {
                        const isSelected = selectedJob?.id === job.id;
                        return (
                            <tr
                                id={`job-row-${job.id}`}
                                key={job.id}
                                ref={isSelected ? selectedRowRef : undefined}
                                className={isSelected ? 'selected' : ''}
                                onClick={() => onJobSelect(job)}>
                            <td className="checkbox-column" onClick={(e) => e.stopPropagation()}>
                                <input 
                                    id={`job-table-select-${job.id}`}
                                    name={`select_job_${job.id}`}
                                    type="checkbox" 
                                    checked={selectionMode === 'all' || selectedIds.has(job.id)}
                                    onChange={() => onToggleSelectJob(job.id)}
                                    onClick={(e) => e.stopPropagation()}
                                />
                            </td>
                            <td className="salary-column text-no-wrap">{job.salary || '-'}</td>
                            <td className="title-column text-no-wrap">{job.title || '-'}</td>
                            <td className="company-column text-no-wrap">{job.company || '-'}</td>
                            <td className="status-column text-no-wrap">
                                <div className="status-badges">
                                    {job.comments && (
                                        <span className="status-badge status-comments"title="Has comments">📝</span>
                                    )}
                                    {STATE_BASE_FIELDS.filter(field => job[field as keyof Job] === true).map(status => (
                                        <span 
                                            key={status} 
                                            className={`status-badge status-${status}`}
                                            title={status.replace(/_/g, ' ')}>
                                            {status.charAt(0).toUpperCase()}
                                        </span>
                                    ))}
                                </div>
                            </td>
                            <td className="created-column text-no-wrap" title={calculateLapsedTimeDetail(job.created)}>{calculateLapsedTime(job.created)}</td>
                        </tr>
                        );
                    })}
                </tbody>
            </table>
            {/* Stable bottom-of-list marker. It must not be a table row: a row that gets replaced when a
                page is appended would leave the IntersectionObserver watching a mid-list element. */}
            <div ref={sentinelRef} className="job-table-sentinel" aria-hidden="true" />
        </div>
    );
}
