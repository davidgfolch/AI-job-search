import { useEffect, useRef } from 'react';
import type { Job } from '../api/jobs';
import './JobTable.css';
import { STATE_BASE_FIELDS } from '../hooks/contants';
import { calculateLapsedTime, calculateLapsedTimeDetail } from '../utils/dateUtils';

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
    onToggleSelectAll
}: JobTableProps) {
    const observerTarget = useRef<HTMLTableRowElement>(null);

    useEffect(() => {
        if (!onLoadMore || !hasMore) return;
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting) {
                    onLoadMore();
                }
            },
            { threshold: 0.1, rootMargin: '100px' }
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
    }, [onLoadMore, hasMore, jobs.length]);

    return (
        <div className="job-table-container">
            <table className="job-table">
                <thead>
                    <tr>
                        <th className="checkbox-column">
                            <input 
                                type="checkbox" 
                                checked={selectionMode === 'all'}
                                onChange={onToggleSelectAll}
                                title="Select All"
                            />
                        </th>
                        <th className="salary-column">Salary</th>
                        <th>Title</th>
                        <th>Company</th>
                        <th className="status-column">Status</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
                    {jobs.map((job, index) => (
                        <tr
                            key={job.id}
                            ref={index === jobs.length - 1 ? observerTarget : undefined}
                            className={selectedJob?.id === job.id ? 'selected' : ''}
                            onClick={() => onJobSelect(job)}>
                            <td className="checkbox-column" onClick={(e) => e.stopPropagation()}>
                                <input 
                                    type="checkbox" 
                                    checked={selectionMode === 'all' || selectedIds.has(job.id)}
                                    onChange={() => onToggleSelectJob(job.id)}
                                    onClick={(e) => e.stopPropagation()}
                                />
                            </td>
                            <td className="salary-column">{job.salary || '-'}</td>
                            <td>{job.title || '-'}</td>
                            <td>{job.company || '-'}</td>
                            <td className="status-column">
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
                            <td title={calculateLapsedTimeDetail(job.created)}>{calculateLapsedTime(job.created)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
