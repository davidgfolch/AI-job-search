import { screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import JobDetail from "../JobDetail";
import type { Job } from '../../api/ViewerApi';
import { jobsApi } from '../../api/ViewerApi';
import { skillsApi } from '../../../skillsManager/api/SkillsManagerApi';
import { renderWithProviders, createMockJobs, createMockJob } from "../../test/test-utils";

vi.mock('../../api/ViewerApi', () => ({
    jobsApi: {
        getJobs: vi.fn(),
        getJob: vi.fn(),
        updateJob: vi.fn(),
        getAppliedJobsByCompany: vi.fn(),
    },
}));

vi.mock('../../../skillsManager/api/SkillsManagerApi', () => ({
    skillsApi: {
        getSkills: vi.fn(),
    }
}));

const mockJob = createMockJob({
    markdown: 'Job Description Content',
    required_technologies: 'React, TypeScript',
    comments: 'Initial comment',
});

describe('JobDetail', () => {
    beforeEach(() => {
        vi.resetAllMocks();
        (jobsApi.getAppliedJobsByCompany as any).mockResolvedValue([]);
        (skillsApi.getSkills as any).mockResolvedValue([]);
    });

    it('renders basic job details, link, and CV match', async () => {
        renderWithProviders(<JobDetail job={mockJob} />);
        await waitFor(() => expect(screen.getByText('Software Engineer')).toBeInTheDocument());

        expect(screen.getByText('Tech Corp')).toBeInTheDocument();
        expect(screen.getByText('Job Description Content')).toBeInTheDocument();
        expect(screen.getByText('React')).toBeInTheDocument();
        expect(screen.getByText('100k')).toBeInTheDocument();
        expect(screen.getByText('Initial comment')).toBeInTheDocument();
        expect(screen.getByText('90%')).toBeInTheDocument(); // CV Match

        const link = screen.getByText('Software Engineer');
        expect(link).toHaveAttribute('href', 'http://example.com');
        expect(link).toHaveAttribute('target', '_blank');
    });

    it.each([
        ['easy_apply', 'easy apply'],
        ['ai_enriched', 'ai enriched'],
        ['interview', 'interview'],
    ])('displays %s status when true', async (prop, text) => {
        const job = { ...mockJob, [prop]: true };
        renderWithProviders(<JobDetail job={job as Job} />);
        await waitFor(() => expect(screen.getByText(text)).toBeInTheDocument());
    });

    it('does not display optional fields when they are null', async () => {
        const job: Job = { ...mockJob, company: null, salary: null, comments: null };
        renderWithProviders(<JobDetail job={job} />);
        await waitFor(() => expect(screen.queryByText('Software Engineer')).toBeInTheDocument());
        
        expect(screen.queryByText('Company:')).not.toBeInTheDocument();
        expect(screen.queryByText('100k')).not.toBeInTheDocument();
        expect(screen.queryByText('Initial comment')).not.toBeInTheDocument();
    });

    describe('Interactions', () => {
        it('toggles salary calculator and handles external link', async () => {
            const windowOpenSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
            renderWithProviders(<JobDetail job={mockJob} />);
            await waitFor(() => screen.getByText('🧮 Freelance'));

            fireEvent.click(screen.getByText('🧮 Freelance'));
            expect(screen.getByText('Salary Calculator')).toBeInTheDocument();
            fireEvent.click(screen.getByLabelText('Close calculator'));
            expect(screen.queryByText('Salary Calculator')).not.toBeInTheDocument();

            fireEvent.click(screen.getByText('🧮 Gross year'));
            expect(windowOpenSpy).toHaveBeenCalledWith('https://tecalculo.com/calculadora-de-sueldo-neto', '_blank');
            windowOpenSpy.mockRestore();
        });

        it('handles salary deletion', async () => {
            const onUpdateMock = vi.fn();
            renderWithProviders(<JobDetail job={mockJob} onUpdate={onUpdateMock} />);
            await waitFor(() => screen.getByTitle('Delete salary information'));
            
            fireEvent.click(screen.getByTitle('Delete salary information'));
            expect(onUpdateMock).toHaveBeenCalledWith({ salary: null });
        });



        it('handles ai_enrich_error presence and copy', async () => {
            const jobWithError: Job = { ...mockJob, ai_enrich_error: 'Test Error' };
            const writeTextMock = vi.fn();
            Object.assign(navigator, { clipboard: { writeText: writeTextMock } });

            const { rerender } = renderWithProviders(<JobDetail job={jobWithError} />);
            await waitFor(() => expect(screen.getByText('Test Error')).toBeInTheDocument());

            fireEvent.click(screen.getByText('Test Error'));
            expect(writeTextMock).toHaveBeenCalledWith('Test Error');

            rerender(<JobDetail job={{ ...mockJob, ai_enrich_error: null }} />);
            expect(screen.queryByText('Enrich Error:')).not.toBeInTheDocument();
        });
    });

    it('displays created/modified dates correctly with 5min threshold', async () => {
        const job: Job = {
            ...mockJob,
            company: 'Test Co',
            web_page: 'http://e.com',
            created: '2023-01-01T10:00:00',
            modified: '2023-01-01T10:04:59', // < 5 mins
        };
        const { rerender } = renderWithProviders(<JobDetail job={job} />);
        await waitFor(() => expect(screen.getByText(/10:00/)).toBeInTheDocument());
        expect(screen.queryByText(/modified/)).not.toBeInTheDocument();

        rerender(<JobDetail job={{ ...job, modified: '2023-01-01T10:05:00' }} />); // >= 5 mins
        expect(screen.getAllByText(/modified/)[0]).toBeInTheDocument();
        expect(screen.getByText(/10:05/)).toBeInTheDocument();
    });
});
