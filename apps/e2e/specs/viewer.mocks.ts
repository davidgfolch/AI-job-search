export const MOCK_JOB_1 = {
    id: 1,
    title: 'Frontend Engineer',
    company: 'Tech Corp',
    salary: '120k',
    location: 'Remote',
    url: 'http://example.com/1',
    markdown: 'Job Description',
    web_page: 'LinkedIn',
    created: '2023-01-01',
    modified: null,
    flagged: false,
    like: false,
    ignored: false,
    seen: false,
    applied: false,
    discarded: false,
    closed: false,
    ai_enriched: true,
    required_technologies: 'React',
    optional_technologies: 'TypeScript',
    client: null,
    comments: null,
    cv_match_percentage: 95,
};

export const MOCK_JOB_2 = {
    id: 2,
    title: 'Backend Developer',
    company: 'Data Inc',
    salary: '130k',
    location: 'New York',
    url: 'http://example.com/2',
    markdown: 'Backend Description',
    web_page: 'Indeed',
    created: '2023-01-02',
    modified: null,
    flagged: false,
    like: false,
    ignored: false,
    seen: false,
    applied: false,
    discarded: false,
    closed: false,
    ai_enriched: true,
    required_technologies: 'Python',
    optional_technologies: 'FastAPI',
    client: null,
    comments: null,
    cv_match_percentage: 88,
};

export const MOCK_JOBS_LIST = {
    items: [MOCK_JOB_1, MOCK_JOB_2],
    total: 2,
    page: 1,
    size: 20,
};

export const MOCK_SEARCH_BACKEND = {
    items: [MOCK_JOB_2],
    total: 1,
    page: 1,
    size: 20,
};

// Enough jobs for the default page size (20) to leave a second page, so pagination can be exercised.
export const PAGE_SIZE = 20;
export const PAGINATED_JOB_COUNT = 25;
export const PAGINATED_JOBS = Array.from({ length: PAGINATED_JOB_COUNT }, (_, index) => ({
    ...MOCK_JOB_1,
    id: index + 1,
    title: `Paginated Job ${index + 1}`,
    company: `Paginated Company ${index + 1}`,
    salary: `${100 + index}k`,
    created: `2023-01-${String((index % 28) + 1).padStart(2, '0')}`,
}));

export const paginatedJobsResponse = (page: number, size: number) => ({
    items: PAGINATED_JOBS.slice((page - 1) * size, page * size),
    total: PAGINATED_JOB_COUNT,
    page,
    size,
});

export const SALARY_CALC_COMMENT = '<!-- SALARY_CALC_DATA:{"calcMode":"classic","calcRate":40,"calcRateType":"Hourly","calcFreelanceRate":80,"calcHoursPerWeek":40,"calcDaysPerMonth":20} -->';

export const MOCK_JOB_WITH_CALC_COMMENTS = {
    ...MOCK_JOB_1,
    comments: SALARY_CALC_COMMENT,
};

export const MOCK_JOB_NO_SALARY = {
    ...MOCK_JOB_1,
    salary: null,
};

export const SALARY_HISTORY_ENTRIES = [
    {
        job_id: 1,
        company_raw: 'Tech Corp',
        company_normalized: 'tech corp',
        title: 'Frontend Engineer',
        salary: '120k',
        recorded_at: '2023-06-01T10:00:00',
        source: 'LinkedIn',
    },
    {
        job_id: 3,
        company_raw: 'Tech Corp',
        company_normalized: 'tech corp',
        title: 'Senior Frontend Engineer',
        salary: '140k',
        recorded_at: '2023-07-01T10:00:00',
        source: 'Indeed',
    },
];
