import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import ReactMarkdownCustom from '../../common/components/core/ReactMarkdownCustom';
import { jobsApi, type Job } from "../api/ViewerApi";
import './JobDetail.css';
import './Filters.css';
import './FilterConfigurations.css';
import SalaryCalculator from './salaryCalculator/SalaryCalculator';
import { parseSalaryCalculationFromComments, parseAllSalaryCalculationsFromComments } from './salaryCalculator/salaryFormatters';
import { STATE_FIELDS } from '../constants';
import JobDetailHeader from './job-detail/JobDetailHeader';
import JobDetailInfo from './job-detail/JobDetailInfo';
import JobDetailCompactHeader from './job-detail/JobDetailCompactHeader';

interface JobDetailProps {
    job: Job;
    onUpdate?: (data: Partial<Job>) => void;
    onOpenDuplicated?: (id: number) => void;
    onClose?: () => void;
    hideDuplicatedButton?: boolean;
}

export default function JobDetail({ job, onUpdate, onOpenDuplicated, onClose, hideDuplicatedButton }: JobDetailProps) {
    const { data: appliedCompanyJobs = [], isLoading: loadingApplied } = useQuery({
        queryKey: ['appliedCompanyJobs', job.company, job.client],
        queryFn: async () => {
            if (!job.company) return [];
            const jobs = await jobsApi.getAppliedJobsByCompany(job.company, job.client || undefined);
            if (jobs.length > 60) { jobs.splice(60); jobs[60 - 1].created = '...'; }
            return jobs;
        },
        enabled: !!job.company,
        staleTime: 5 * 60 * 1000,
    });

    const contentRef = useRef<HTMLDivElement>(null);
    const savedCalcParams = useMemo(() => parseSalaryCalculationFromComments(job.comments), [job.comments]);
    const allSavedCalcParams = useMemo(() => parseAllSalaryCalculationsFromComments(job.comments), [job.comments]);
    const [showCalculator, setShowCalculator] = useState(false);
    const [isScrolled, setIsScrolled] = useState(false);

    const handleScroll = useCallback(() => {
        if (contentRef.current) setIsScrolled(contentRef.current.scrollTop > 50);
    }, []);

    useEffect(() => setShowCalculator(!!savedCalcParams), [job.id, savedCalcParams]);

    useEffect(() => { if (contentRef.current) contentRef.current.scrollTop = 0; }, [job]);

    useEffect(() => {
        const content = contentRef.current;
        if (content) { content.addEventListener('scroll', handleScroll); return () => content.removeEventListener('scroll', handleScroll); }
    }, [handleScroll]);

    return (
        <div className="job-detail">
            <JobDetailHeader job={job} onCloseDuplicated={onClose} onOpenDuplicated={hideDuplicatedButton ? undefined : onOpenDuplicated} />
            <div className="job-detail-scroll-wrapper">
                <div className="job-status-floating">
                    {STATE_FIELDS.filter(field => job[field as keyof Job] === true).map(status => (
                        <span key={status} className={`status-tag status-${status}`}>{status.replace(/_/g, ' ')}</span>
                    ))}
                </div>
                <div className="job-detail-content" ref={contentRef}>
                    {isScrolled && <JobDetailCompactHeader job={job} />}
                    <JobDetailInfo job={job} appliedCompanyJobs={appliedCompanyJobs} loadingApplied={loadingApplied} onUpdate={onUpdate} showCalculator={showCalculator} onToggleCalculator={() => setShowCalculator(!showCalculator)} />
                    {showCalculator && <SalaryCalculator key={job.id} onClose={() => setShowCalculator(false)} job={job} onUpdate={onUpdate} initialParams={savedCalcParams} allSavedParams={allSavedCalcParams} />}
                    {job.comments && (
                        <div className="job-comments"><h3>Comments</h3><div className="markdown-content"><ReactMarkdownCustom>{job.comments}</ReactMarkdownCustom></div></div>
                    )}
                    {job.markdown && (
                        <div className="job-markdown"><div className="markdown-content"><ReactMarkdownCustom>{job.markdown}</ReactMarkdownCustom></div></div>
                    )}
                </div>
            </div>
        </div>
    );
}
