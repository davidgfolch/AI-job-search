import type { Job } from '../api/jobs';
import './JobTable.css';

interface JobTableProps {
    jobs: Job[];
    selectedJob: Job | null;
    onJobSelect: (job: Job) => void;
}

export default function JobTable({ jobs, selectedJob, onJobSelect }: JobTableProps) {
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
                    {jobs.map((job) => (
                        <tr
                            key={job.id}
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
