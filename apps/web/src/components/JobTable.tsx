import { useEffect, useRef } from 'react';
import type { Job } from '../api/jobs';
import './JobTable.css';

interface JobTableProps {
    jobs: Job[];
    selectedJob: Job | null;
    onJobSelect: (job: Job) => void;
    onLoadMore?: () => void;
    hasMore?: boolean;
}

export default function JobTable({ jobs, selectedJob, onJobSelect, onLoadMore, hasMore }: JobTableProps) {
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
                        <th>Salary</th>
                        <th>Title</th>
                        <th>Company</th>
                    </tr>
                </thead>
                <tbody>
                    {jobs.map((job, index) => (
                        <tr
                            key={job.id}
                            ref={index === jobs.length - 3 ? observerTarget : null}
                            className={selectedJob?.id === job.id ? 'selected' : ''}
                            onClick={() => onJobSelect(job)}
                        >
                            <td>{job.salary || '-'}</td>
                            <td>{job.title || '-'}</td>
                            <td>{job.company || '-'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
