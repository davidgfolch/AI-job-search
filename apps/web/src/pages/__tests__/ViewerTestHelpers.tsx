import { screen, fireEvent, waitFor, act } from '@testing-library/react';
import { expect } from 'vitest';
import { jobsApi } from '../../api/jobs';
import { mockJobs } from './ViewerTestUtils';

export const mockJobsApiDefault = () => {
  (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
  (jobsApi.getJob as any).mockResolvedValue(mockJobs[0]);
};

export const waitForJobList = async () => {
  await waitFor(() => expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0));
};

export const selectJob = (jobName: string) => {
  fireEvent.click(screen.getByRole('cell', { name: jobName }));
};

export const switchToTab = (tabName: string) => {
  fireEvent.click(screen.getByText(tabName));
};

export const clickFilterButton = (filterName: string) => {
  const buttons = screen.getAllByRole('button', { name: new RegExp(filterName, 'i') });
  fireEvent.click(buttons[0]);
};

export const verifyJobDetails = async (description: string, company: string) => {
  expect(await screen.findByText(description, { selector: '.markdown-content p' })).toBeInTheDocument();
  expect(screen.getAllByText(company)).toHaveLength(2);
};

export const verifySummary = (text: RegExp) => {
  const summary = screen.getByText(/ loaded \| /);
  expect(summary).toHaveTextContent(text);
};

export const triggerInfiniteScroll = async (callback: any) => {
  await act(async () => {
    callback([{ isIntersecting: true }]);
  });
};
