import { useEffect, useRef, useCallback } from 'react';
import type { Job } from '../api/ViewerApi';
import './JobTable.css';
import { STATE_BASE_FIELDS } from '../constants';
import { calculateLapsedTime, calculateLapsedTimeDetail } from '../../common/utils/dateUtils';

interface JobTableProps {
    jobs: Job[];
    selectedJob: Job | null;
    onJobSelect: (job: Job) => void;
    onLoadMore?: () => void;
    hasMore?: boolean;
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
    selectedIds,
    selectionMode,
    onToggleSelectJob,
    onToggleSelectAll,
    containerRef,
}: JobTableProps) {
    const observerTarget = useRef<HTMLTableRowElement>(null);
    const isLoadingRef = useRef(false);

    const debouncedOnLoadMore = useCallback(() => {
        if (!isLoadingRef.current) {
            isLoadingRef.current = true;
            onLoadMore();
            setTimeout(() => {
                isLoadingRef.current = false;
            }, 1000);
        }
    }, [onLoadMore]);

    useEffect(() => {
        if (!onLoadMore || !hasMore) return;
        
        const observer = new IntersectionObserver(
            (entries) => {
                const entry = entries[0];
                if (entry.isIntersecting && !isLoadingRef.current) {
                    const container = containerRef.current;
                    if (container) {
                        const hasScrollbar = container.scrollHeight > container.clientHeight;
                        if (hasScrollbar) {
                            debouncedOnLoadMore();
                        }
                    }
                }
            },
            { threshold: 0.1, rootMargin: '50px' }
        );
        const currentTarget = observerTarget.current;
        if (currentTarget) {
            observer.observe(currentTarget);
        }
        return () => {
            if (currentTarget) {
                observer.unobserve(currentTarget);
            }
        };
    }, [onLoadMore, hasMore, debouncedOnLoadMore]);

    // Reset loading state when jobs change (new data loaded)
    useEffect(() => {
        isLoadingRef.current = false;
    }, [jobs]);

    // Fallback scroll listener as backup for IntersectionObserver
    useEffect(() => {
        if (!onLoadMore || !hasMore || isLoadingRef.current) return;
        const container = containerRef.current;
        if (!container) return;
        const handleScroll = () => {
            if (isLoadingRef.current) return;
            const { scrollTop, scrollHeight, clientHeight } = container;
            const scrollThreshold = 100; // pixels from bottom
            const isNearBottom = scrollTop + clientHeight >= scrollHeight - scrollThreshold;
            if (isNearBottom && scrollHeight > clientHeight) {
                debouncedOnLoadMore();
            }
        };
        container.addEventListener('scroll', handleScroll, { passive: true });
        return () => {
            container.removeEventListener('scroll', handleScroll);
        };
    }, [onLoadMore, hasMore, debouncedOnLoadMore]);

    const selectedRowRef = useRef<HTMLTableRowElement>(null);

    useEffect(() => {
        if (selectedJob && selectedRowRef.current) {
            selectedRowRef.current.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest',
                inline: 'nearest'
            });
        }
    }, [selectedJob?.id]);

    return (
        <div className="job-table-container" ref={containerRef}>
            <table className="job-table">
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
                    {jobs.map((job, index) => {
                        const isSelected = selectedJob?.id === job.id;
                        const isLastRow = index === jobs.length - 1;
                        return (
                            <tr
                                id={`job-row-${job.id}`}
                                key={job.id}
                                ref={isSelected ? selectedRowRef : (isLastRow ? observerTarget : undefined)}
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
        </div>
    );
}
