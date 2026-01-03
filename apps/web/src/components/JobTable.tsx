import { useEffect, useRef } from 'react';
import type { Job } from '../api/jobs';
import './JobTable.css';

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
                    </tr>
                </thead>
                <tbody>
                    {jobs.map((job, index) => (
                        <tr
                            key={job.id}
                            ref={index === jobs.length - 1 ? observerTarget : undefined}
                            className={selectedJob?.id === job.id ? 'selected' : ''}
                            onClick={() => onJobSelect(job)}
                        >
                            <td className="checkbox-column" onClick={(e) => e.stopPropagation()}>
                                <input 
                                    type="checkbox" 
                                    checked={selectionMode === 'all' || selectedIds.has(job.id)}
                                    onChange={() => onToggleSelectJob(job.id)}
                                />
                            </td>
                            <td className="salary-column">{job.salary || '-'}</td>
                            <td>{job.title || '-'}</td>
                            <td>{job.company || '-'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
