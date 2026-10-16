# Graph Report - ai-job-search  (2026-10-16)

## Corpus Check
- 949 files · ~420,191 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 91 file(s) not represented in the graph (top: .css 34, (none) 21, .bat 17)

## Summary
- 7613 nodes · 16906 edges · 711 communities (270 shown, 441 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1470 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ac067429`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- green
- GmailService
- useViewer.ts
- aiEnrichNew/test/config_test.py
- typing
- TestAttributes
- TestGlassdoorAuthenticator
- Viewer.tsx
- JobDetailInfo.tsx
- metrics_collector_test.py
- BaseExecutor
- TestLinkedinNavigator
- PersistenceManager
- GmailConnectionError
- MysqlUtil
- PageHeader
- ollama_discovery_test.py
- TestTecnoempleoCompanyReader
- sys
- ContextLoader
- prometheus_exporter_test.py
- observability.py
- enrich_jobs
- vitest
- aiEnrich3/dataExtractor.py
- enrichment_service.py
- viewer.helpers.ts
- ViewerTestUtils.tsx
- Most Important Improvements for this Monorepo
- aiEnrichSkill/test/config_test.py
- TecnoempleoNavigator
- WatcherRepository
- QueryExecutor
- salary_history_repository_test.py
- SeleniumService
- companyExtractor_test.py
- ai_helpers.py
- compilerOptions
- InfojobsNavigator
- yellow
- useSqlEditor.ts
- TestJobRepository
- TestIndeedNavigator
- filter_configurations_service_test.py
- filter_configuration_test.py
- ViewerApi.ts
- retry
- rawToJson
- mysql_discovery_test.py
- AnswerResult
- SalaryCalculator
- skills.py
- filter_configurations_repository_test.py
- scrapper_scheduler_test.py
- persistence_manager_test.py
- api/test/settings_test.py
- TestScraplingService
- LinkedinExecutor
- configurations.spec.ts
- devDependencies
- logIdleWait
- FilterConfigurationsService
- dataExtractor
- TestTecnoempleoNavigator
- StatisticsRepository
- configurations.helpers.ts
- company_normalizer_test.py
- time
- Job Scrappers
- aiEnrich/dataExtractor.py
- enrichment_service_test.py
- skills_test.py
- seleniumSocketConnRetry
- Examples
- JobWriteRepository
- App.tsx
- Statistics.tsx
- compilerOptions
- Plan 0: Observability (Foundation for All Improvements)
- routes.py
- CompanySynonymRepository
- TestIndeedScraplingNavigator
- console_render_test.py
- TestJobQueries
- TestIndeedService
- IndeedScraplingNavigator
- DashboardApi.ts
- get
- manifest.json
- WakeableTimer
- jobs_test.py
- BrowserService
- connection_manager_test.py
- architecture_test.py
- stringUtil.py
- ConcreteNavigator
- query_openrouter
- Screenshots
- .layout_check.cjs
- configure_logging
- selenium/test/conftest.py
- Skill
- ScrapperStateCalculator
- mockRepo
- scheduler_test.py
- TestInfojobsNavigator
- testSetup.ts
- AGENTS.md
- patch
- graphify-html-grouped.py
- JobTable.test.tsx
- e2e/package.json
- generate_config_view_sql
- aiEnrich3/pipeline.py
- AGENTS.md
- resolve_ollama_url
- keep_system_awake.py
- TestQuestionAnsweringService
- company_synonyms.py
- process_skill_enrichment
- create_mock_db
- CombinedStatsRepository
- extract_boolean_filters
- DriverUtil
- Advanced usages
- TestEmailReader
- .conn
- AI Job Search — Metrics & Observability
- settings_service.py
- Querying elements
- FastCVMatcher
- WatcherService
- AI Job Search API
- JobDeleteRepository
- SkillsRepository
- json
- exceptionUtil_test.py
- MongoDbProvider
- AI Job Search Web UI
- JobSnapshotService
- dependencies
- os
- panel.js
- AI Form Filler
- cron/test/main_test.py
- ollama_client_test.py
- CVLoader
- Plan C: Two-Stage Pipeline (aiEnrich3 Fast Path + aiEnrich LLM Fallback)
- Plan E: Prompt & Token Optimization (Quick Wins)
- Installation Steps
- ollama_client.py
- README.md
- extractors/test/modality_extractor_test.py
- SnapshotsRepository
- statistics_service_test.py
- CronStateRepository
- CompanySalaryHistoryScanner
- FilterConfigurationsRepository
- environmentUtil.py
- Plan F: Combined / Recommended Approach
- AiEnrichRepository
- jobs_service_test.py
- backendDiscovery.ts
- jobQueryService_test.py
- jobs_applied_test.py
- @testing-library/react
- JobsRepository
- patch
- FilterConfigurations.tsx
- systemUtil.py
- JobSnapshotRepository
- get_logger
- Plan D: GGUF Quantized Models via llama-cpp-python
- aiEnrichSkill
- useAutoLoadMore.fixtures.tsx
- _process_job_safe
- validationUtils.ts
- Auto-merge (staging gate)
- FilterConfigSelector
- graphify-inject-edges.py
- TestBaseService
- observability_test.py
- StatisticsArchivedService
- service_mock
- IndeedAuthenticator
- Common Library
- api/test/main_test.py
- log_file_path
- DdlRepository
- TODO
- process_batch
- Workflow
- TestApiRoutes
- JobDeleteService
- dashboard_repository_test.py
- Company Salary History Scanner
- IndeedNavigator
- ScrapperStateRepository
- mysql_sync.py
- frontend-coverage-gate.mjs
- process_batch
- commonlib
- ScrapperStateRepository
- TestLinkedinDetailReader
- log_capture.py
- Version Bumper Instructions
- captured_records
- terminalUtil.py
- TestTransactionManager
- aiEnrich/test/dataExtractor_test.py
- GlassdoorExecutor_test.py
- InfojobsExecutor_test.py
- append_jsonl
- Quick Start Commands for Docker Development
- CompanySynonymService
- company_synonym_service_test.py
- TestGlassdoorNavigator
- watcher_refresh.spec.ts
- .checkboxUnselect
- cvMatcher.py
- mysqlUtil.py
- Undetected ChromeDriver Usage
- .test_message_is_the_first_named_field
- filter_configurations_test.py
- get_skill_context
- AI Job Enrichment
- SkillsManager.tsx
- Settings.tsx
- Fetchers basics
- OpenAIProvider
- metrics_collector.py
- TestStealthScripts
- exceptionHandler.py
- post
- run_pipeline
- getEnv
- resolve_mysql_host
- ollama_config_test.py
- .fetch
- docs-sync.py
- Plan B: RAG Cache Layer (Skip LLM Inference for Similar Jobs)
- resolve_ollama_host
- scripts
- pandas
- ScraplingService
- TestScrapperConfig
- JobsService
- web/package.json
- E2E Implementer Instructions
- Adaptive scraping
- Proxy management and handling Blocks
- job_delete_service_test.py
- AI Job Search Default Development Guide
- Components
- _probe_inference
- TestTecnoempleoSalaryReader
- aiEnrichNew/services/job_enrichment_service.py
- JobQueryRepository
- Plan A: Direct Ollama API (Remove CrewAI)
- Test Implementer Instructions
- TestDelegation
- AI Enrichment — Speed Improvement Plans
- wake_timer_test.py
- TestConfiguration
- Examples
- content.js
- IndeedGmailService
- ping_ollama
- TestGetConnection
- SalaryHistoryService
- aiEnrichSkill/main.py
- Fix scrapper job failures logged on 2026-10-09
- .test_bound_name_is_kept_without_an_app_frame
- Agentic SDLC
- sleep
- parametrize
- uninstall.sh
- uninstall-menu.ps1
- MockBaseExecutor
- sqlUtil.py
- log_writer_test.py
- JobReadRepository
- graphify.sh
- backend/conftest.py
- Scrapling Examples
- SalaryHistoryRepository
- skills_manager.spec.ts
- coverage.config.ts
- docker-build.md
- rotate_if_needed
- TestJobBooleanKeys
- TestElementLookup
- CustomConverter
- tsconfig.json
- View Backend Logs Instructions
- TestContextManager
- test-sandbox.sh
- pytest
- nvidia-linux-restart.sh
- test.sh
- Solution
- scrapper_coverage_gate.py
- query_ollama
- TestGetConnectionPoolError
- requests
- aiEnrich/run.sh
- aiEnrichNew/run.sh
- aiEnrichSkill/run.sh
- aiFormFiller/run.sh
- TestTryTargets
- execute_with_error_handler
- backend/run.sh
- cron/run.sh
- scrapper/run.sh
- docker-build.js
- docker-entrypoint.sh
- Migrating from BeautifulSoup to Scrapling
- MockMysqlUtil
- TestProcessAndLoadRow
- statistics_test.py
- aiEnrich/test/config_test.py
- browser_service_test.py
- 1. PYTHON MODULES (Backend & Commonlib)
- get_pipeline
- TestBooleanFilterKeys
- web/run.sh
- Contribute
- docs-sync.js
- .claude/rules/architecture-guidelines.md
- .claude/skills/skill-builder/SKILL.md
- TestResolveDbHost
- aiEnrichNew
- consoleTimer
- install.sh
- backup.sh
- restore.sh
- runMysql.sh
- TestKeywordPagination
- get_local_ip
- LocalHFProvider
- docker-build.py
- Documentation Sync (mandatory, automatic)
- request_logging_test.py
- TestProbeMysql
- Phase 8 — Tests and docs
- TestInitPool
- mock_mysql_connect
- SalaryCalculator.tsx
- Database changes require explicit user permission
- ddl.sql
- Debug GitHub Actions & Dependabot Runs with `gh`
- Crawlee Page Analyst Instructions
- sync.sh
- db-mutation.js
- TestSeleniumSocketConnRetry
- .update_from_ai

## God Nodes (most connected - your core abstractions)
1. `vitest` - 155 edges
2. `MysqlUtil` - 147 edges
3. `@testing-library/react` - 117 edges
4. `SeleniumService` - 96 edges
5. `PersistenceManager` - 85 edges
6. `react` - 80 edges
7. `yellow()` - 77 edges
8. `getEnv()` - 71 edges
9. `get_logger()` - 69 edges
10. `configure_logging()` - 66 edges

## Surprising Connections (you probably didn't know these)
- ``apps/aiEnrich/src/aiEnrich/rag_cache.py`` --references--> `FastCVMatcher`  [INFERRED]
  .opencode/plans/aiEnrich-improvements/02_rag_cache.md → apps/aiCvMatcher/src/aiCvMatcher/cvMatcher.py
- `2. Naming Conventions` --references--> `sut()`  [INFERRED]
  .claude/skills/test-implementer/SKILL.md → apps/backend/services/test/company_synonym_service_test.py
- `Configuration` --references--> `configure_logging()`  [INFERRED]
  READMEs/README_DEVELOPMENT.md → apps/commonlib/commonlib/observability.py
- `Prometheus Exporter (`commonlib/prometheus_exporter.py`)` --references--> `build_log_metrics()`  [INFERRED]
  READMEs/README_METRICS.md → apps/commonlib/commonlib/prometheus_exporter.py
- `Data Flow` --references--> `MetricsCollector`  [INFERRED]
  READMEs/README_METRICS.md → apps/commonlib/commonlib/services/metrics_collector.py

## Import Cycles
- None detected.

## Communities (711 total, 441 thin omitted)

### Community 2 - "green"
Cohesion: 0.11
Nodes (19): _cues(), extract_modality(), join(), blue(), cyan(), green(), magenta(), printHR() (+11 more)

### Community 5 - "useViewer.ts"
Cohesion: 0.15
Nodes (23): getModalityValues(), useModalityValues(), DEFAULT_FILTERS, createWrapper(), jobs, Props, renderWithUrl(), base() (+15 more)

### Community 8 - "aiEnrichNew/test/config_test.py"
Cohesion: 0.15
Nodes (15): get_batch_size(), get_enrich_timeout_job(), get_input_max_len(), get_job_system_prompt(), should_cleanup_gpu(), build_job_prompt_messages(), map_db_job_to_domain(), test_build_job_prompt_messages() (+7 more)

### Community 9 - "typing"
Cohesion: 0.09
Nodes (8): drop_config_view_sql(), _get_view_name(), invalidate_watcher_view(), htmlToMarkdown(), removeInvalidScapes(), removeLinks(), validate(), BaseService

### Community 11 - "TestAttributes"
Cohesion: 0.08
Nodes (5): TestAttributes, TestClearInputbox, TestScrollAndClick, TestSendKeys, TestWaits

### Community 17 - "Viewer.tsx"
Cohesion: 0.08
Nodes (41): PinnedConfigurations(), JobDetailHeader(), JobDetailHeaderProps, JobActions(), JobActionsProps, JobDetailPanels(), PanelDivider(), PanelDividerProps (+33 more)

### Community 18 - "JobDetailInfo.tsx"
Cohesion: 0.10
Nodes (23): CvMatchBar(), CvMatchBarProps, SalaryHistoryEntry, AppliedJobsWarning(), AppliedJobsWarningProps, JobDetailCompactHeader(), JobDetailCompactHeaderProps, formatDateTime() (+15 more)

### Community 22 - "metrics_collector_test.py"
Cohesion: 0.09
Nodes (10): get_prometheus_metrics(), f(), MetricsCollector, collector(), reset_singleton(), test_load_corrupted_file(), test_persist_and_load(), test_persist_if_due_skips_when_recent() (+2 more)

### Community 23 - "BaseExecutor"
Cohesion: 0.07
Nodes (15): cleanUnresolvedTrace(), BaseExecutor, mocks(), run_mocks(), TestPreloadRun, base_mysql(), indeed_executor(), indeed_navigator() (+7 more)

### Community 28 - "PersistenceManager"
Cohesion: 0.06
Nodes (19): getDatetimeNowStr(), summarize(), mock_env_vars(), mock_mysql(), mock_persistence_manager(), mock_selenium(), mock_env_vars(), mock_mysql() (+11 more)

### Community 31 - "GmailConnectionError"
Cohesion: 0.10
Nodes (7): EmailNotFoundError, GmailConnectionError, GmailTimeoutError, VerificationCodeExtractionError, EmailReader, _message_ref(), TestEmailExceptions

### Community 36 - "PageHeader"
Cohesion: 0.13
Nodes (14): Dropdown(), DropdownProps, HeaderMenu(), PageHeader(), PageHeaderProps, companySynonymsApi, SynonymGroup, CompanySynonymsManager() (+6 more)

### Community 39 - "ollama_discovery_test.py"
Cohesion: 0.12
Nodes (8): discover_ollama_hosts(), get_local_subnets(), _scan_hosts(), _scan_port(), TestDiscoverOllamaHosts, TestGetLocalSubnets, TestScanHosts, TestScanPort

### Community 41 - "sys"
Cohesion: 0.12
Nodes (12): filter_deps(), is_external_dep(), main(), generate_labels(), main(), _skip_label(), cleanup_all_e2e_databases(), get_e2e_connection() (+4 more)

### Community 42 - "ContextLoader"
Cohesion: 0.12
Nodes (5): init_routes(), ContextLoader, create_app(), TestContextLoader, TestMain

### Community 43 - "prometheus_exporter_test.py"
Cohesion: 0.16
Nodes (15): build_log_metrics(), build_prometheus_metrics(), test_build_log_metrics_file_oserror(), test_build_log_metrics_invalid_json_lines(), test_build_log_metrics_no_files(), test_build_log_metrics_survives_non_object_lines(), test_build_log_metrics_survives_null_job_id(), test_build_log_metrics_survives_record_without_job_id() (+7 more)

### Community 44 - "observability.py"
Cohesion: 0.10
Nodes (6): getAndCheckEnvVars(), join(), debug(), pageExists(), BaseNavigator, TestElementService

### Community 45 - "enrich_jobs"
Cohesion: 0.22
Nodes (4): enrich_jobs(), _fetch_and_sort_jobs(), retry_failed_job(), TestJobEnrichmentService

### Community 47 - "vitest"
Cohesion: 0.05
Nodes (46): notificationService, persistenceApi, persistenceDefaults, filterConfigsApi, FilterConfiguration, FilterConfigurationCreate, FilterConfigurationUpdate, mockConfig (+38 more)

### Community 50 - "aiEnrich3/dataExtractor.py"
Cohesion: 0.17
Nodes (16): get_batch_size(), get_input_max_len(), get_job_enabled(), get_skill_enabled(), getEnvBool(), dataExtractor(), run(), test_get_batch_size() (+8 more)

### Community 51 - "enrichment_service.py"
Cohesion: 0.14
Nodes (15): get_enrich_limit(), build_skill_prompt_messages(), parse_skill_enrichment_result(), test_build_skill_prompt_messages(), test_parse_skill_enrichment_result(), _enrich_huggingface(), _enrich_ollama(), timed_generate() (+7 more)

### Community 52 - "viewer.helpers.ts"
Cohesion: 0.16
Nodes (18): SALARY_CALC_RESPONSE, searchJobs(), setupBulkJobsRoute(), setupDefaultJobsRoute(), setupJobUpdateRoute(), setupPaginatedJobsRoute(), setupStateChangeJobsRoute(), toggleFiltersIfNeeded() (+10 more)

### Community 54 - "ViewerTestUtils.tsx"
Cohesion: 0.22
Nodes (19): MockFilters(), MockJobActions(), MockJobDetail(), MockJobEditForm(), MockJobList(), MockReactMarkdownCustom(), MockSelectableJobList(), MockViewTabs() (+11 more)

### Community 58 - "Most Important Improvements for this Monorepo"
Cohesion: 0.08
Nodes (23): 2.1 Component File Size Analysis, 2.2 Custom Hooks Pattern (Good Practice), 2.3 Architecture Test Coverage, 2.4 Common Components & Reusability, 2.5 API Layer Organization, 2. REACT FRONTEND (apps/web), 3.1 Service Architecture, 3. SCRAPPER MODULE (apps/scrapper) (+15 more)

### Community 62 - "aiEnrichSkill/test/config_test.py"
Cohesion: 0.15
Nodes (28): get_batch_size(), get_enabled(), get_hf_model_id(), get_hf_repetition_penalty(), get_hf_temperature(), get_hf_top_p(), get_input_max_len(), get_max_new_tokens() (+20 more)

### Community 63 - "TecnoempleoNavigator"
Cohesion: 0.06
Nodes (12): TecnoempleoExecutor, mock_env_vars(), mock_mysql(), mock_persistence_manager(), mock_selenium(), TestTecnoempleoExecutor, TestTecnoempleoService, TecnoempleoCompanyReader (+4 more)

### Community 64 - "WatcherRepository"
Cohesion: 0.21
Nodes (6): test_create_view_failure_is_logged(), test_get_watcher_stats_empty_ids(), test_get_watcher_stats_from_view(), test_parse_json_filters_returns_empty_on_invalid_json(), _filter_signature(), WatcherRepository

### Community 71 - "SeleniumService"
Cohesion: 0.09
Nodes (3): SeleniumService, service(), TestConstruction

### Community 72 - "companyExtractor_test.py"
Cohesion: 0.19
Nodes (7): get_max_validation_retries(), build_company_prompt(), resolve_unspecified_company(), query_returning(), repo(), TestBuildCompanyPrompt, TestResolveUnspecifiedCompany

### Community 74 - "ai_helpers.py"
Cohesion: 0.13
Nodes (28): combineTaskResults(), _expand_parenthesized_skills(), flatten_skill_groups(), footer(), listsToString(), mapJob(), _normalizeModality(), printJob() (+20 more)

### Community 75 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection, moduleResolution (+14 more)

### Community 77 - "InfojobsNavigator"
Cohesion: 0.13
Nodes (3): InfojobsExecutor, TestInfojobsExecutor, InfojobsNavigator

### Community 78 - "yellow"
Cohesion: 0.12
Nodes (5): yellow(), GlassdoorExecutor, TestGlassdoorExecutor, TestGlassdoorNavigator, GlassdoorNavigator

### Community 79 - "useSqlEditor.ts"
Cohesion: 0.14
Nodes (17): DdlSchemaResponse, fetchDdlSchema(), mockApiClient, useSqlEditor(), UseSqlEditorProps, SqlEditor(), SqlEditorProps, getCaretCoordinates() (+9 more)

### Community 84 - "filter_configurations_service_test.py"
Cohesion: 0.08
Nodes (13): mock_repo(), service(), test_create_duplicate_name(), test_create_success(), test_delete_not_found(), test_delete_success(), test_get_all_seeds_when_empty(), test_get_all_skips_seeding_when_not_empty() (+5 more)

### Community 85 - "filter_configuration_test.py"
Cohesion: 0.30
Nodes (10): FilterConfiguration, FilterConfigurationCreate, FilterConfigurationUpdate, test_filter_configuration(), test_filter_configuration_create(), test_filter_configuration_create_pinned(), test_filter_configuration_create_watched(), test_filter_configuration_update_all_optional() (+2 more)

### Community 86 - "ViewerApi.ts"
Cohesion: 0.05
Nodes (60): HistoryInput(), HistoryInputProps, createDefaultJobMutationsProps(), createWrapper(), mocks, AppliedCompanyJob, Job, JobListParams (+52 more)

### Community 87 - "retry"
Cohesion: 0.09
Nodes (3): retry(), decorator(), TestRetry

### Community 88 - "rawToJson"
Cohesion: 0.09
Nodes (13): decode_unicode_escapes(), fixJsonEndCurlyBraces(), fixJsonInvalidAttribute(), fixJsonStartCurlyBraces(), LazyDecoder, printJsonException(), rawToJson(), TestDecodeUnicodeEscapes (+5 more)

### Community 89 - "mysql_discovery_test.py"
Cohesion: 0.15
Nodes (8): get_local_ip(), get_local_subnets(), _scan_hosts(), _scan_port(), TestGetLocalIp, TestGetLocalSubnets, TestScanHosts, TestScanPort

### Community 90 - "AnswerResult"
Cohesion: 0.15
Nodes (7): AIProvider, AnswerResult, OpenRouterProvider, TestAIProvider, TestAnswerResult, TestOpenRouterProvider, QuestionAnsweringService

### Community 95 - "SalaryCalculator"
Cohesion: 0.14
Nodes (15): calculate_salary(), SalaryCalculationRequest, SalaryService, test_calculate_salary(), test_calculate_salary_params(), SalaryCalculator, test_calculate_salary_hourly(), test_get_year_tax_equation() (+7 more)

### Community 97 - "skills.py"
Cohesion: 0.15
Nodes (14): bulk_create_skills(), create_skill(), delete_skill(), get_skill(), list_skills(), update_skill(), SkillBase, SkillCreate (+6 more)

### Community 98 - "filter_configurations_repository_test.py"
Cohesion: 0.10
Nodes (3): mock_db(), repo_with_mock(), test_create()

### Community 101 - "scrapper_scheduler_test.py"
Cohesion: 0.10
Nodes (19): Configuration, Cron — Background Scheduler, Docker, How it works, Registered jobs, Running, Structured logging, Tech Stack (+11 more)

### Community 102 - "persistence_manager_test.py"
Cohesion: 0.11
Nodes (14): test_add_failed_keyword(), test_clear_state(), test_finalize_scrapper(), test_get_failed_keywords(), test_get_last_execution(), test_get_state(), test_is_state_stale(), test_load_fallback_on_repo_error() (+6 more)

### Community 105 - "LinkedinExecutor"
Cohesion: 0.07
Nodes (5): LinkedinExecutor, TestLinkedinExecutor, LinkedinDetailReader, job_id_from_componentkey(), LinkedinNavigator

### Community 106 - "configurations.spec.ts"
Cohesion: 0.15
Nodes (7): BASE_URL, JobListRequests, openConfigDropdown(), clickConfig(), test, PAGE_SIZE, PAGINATED_JOB_COUNT

### Community 107 - "devDependencies"
Cohesion: 0.09
Nodes (22): devDependencies, baseline-browser-mapping, coverage-badges-cli, eslint, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 110 - "logIdleWait"
Cohesion: 0.12
Nodes (11): logIdleWait(), _caller_module(), stamp_caller_module(), TestLogIdleWait, Normalize logging to structured logs across `apps/*`, Phase 2 — cron (4 files, 16 prints), Phase 4 — backend (9 prints + 9 swallowed exceptions), Phase 6 — Infrastructure (+3 more)

### Community 111 - "FilterConfigurationsService"
Cohesion: 0.22
Nodes (7): create_configuration(), delete_configuration(), get_all_configurations(), get_configuration(), get_service(), update_configuration(), FilterConfigurationsService

### Community 112 - "dataExtractor"
Cohesion: 0.29
Nodes (3): dataExtractor(), TestDataExtractor, TestPingBackend

### Community 115 - "StatisticsRepository"
Cohesion: 0.37
Nodes (5): StatisticsRepository, test_get_history_stats_df(), test_get_history_stats_df_with_dates(), test_get_sources_by_date_df(), test_get_sources_by_hour_df()

### Community 118 - "configurations.helpers.ts"
Cohesion: 0.29
Nodes (15): setupApiSafetyNet(), setupAppBootstrapMocks(), setupModalityMock(), setupSalaryHistoryMocks(), setupTimezoneMock(), setupSynonymsMocks(), MOCK_FILTER_CONFIGS, setupConfigurationsJobsRoute() (+7 more)

### Community 119 - "company_normalizer_test.py"
Cohesion: 0.27
Nodes (10): is_unspecified_company(), normalize_company_name(), test_collapses_spaces(), test_empty_name(), test_is_not_unspecified_company(), test_is_unspecified_company(), test_lowercases_and_trims(), test_removes_parentheticals() (+2 more)

### Community 120 - "time"
Cohesion: 0.11
Nodes (27): enrich_jobs(), _fetch_and_sort_jobs(), _process_job_batch_local(), retry_failed_job(), _save_job_result(), _update_error_state(), mock_pipeline(), mock_repo() (+19 more)

### Community 125 - "Job Scrappers"
Cohesion: 0.11
Nodes (19): Architecture, Configuration, Console Output & Structured Logging, Coverage, Dual Architecture (Selenium vs Scrapling), Dynamic Cadency (Time-based), Features, Gmail Configuration (+11 more)

### Community 126 - "aiEnrich/dataExtractor.py"
Cohesion: 0.22
Nodes (20): get_backend(), get_job_enabled(), get_max_ollama_failures(), get_model(), get_ollama_base_url(), get_openrouter_base_url(), get_openrouter_fallback_model(), get_openrouter_model() (+12 more)

### Community 128 - "enrichment_service_test.py"
Cohesion: 0.20
Nodes (20): enrich_skills(), assert_failure_metric(), capture_process_batch_callbacks(), side_effect(), make_ollama_mocks(), run_enrich_ollama(), run_process_skill_batch(), test_enrich_huggingface() (+12 more)

### Community 129 - "skills_test.py"
Cohesion: 0.43
Nodes (6): test_create_skill(), test_delete_skill(), test_delete_skill_not_found(), test_list_skills(), test_update_skill(), test_update_skill_not_found()

### Community 133 - "Examples"
Cohesion: 0.10
Nodes (20): 1. Vanilla Playwright, 2. Real Chrome, 3. CDP Connection, Async Session Usage, Basic Usage, Browser Automation, Domain Blocking, Downloading Files (+12 more)

### Community 136 - "JobWriteRepository"
Cohesion: 0.29
Nodes (11): JobWriteRepository, _mock_db(), repo(), test_create_job(), test_update_job(), test_update_job_empty_data(), test_update_job_not_found(), test_update_jobs_by_filter() (+3 more)

### Community 137 - "App.tsx"
Cohesion: 0.11
Nodes (16): version, App(), CompanySynonymsManager, Dashboard, Settings, SkillsManager, Statistics, Viewer (+8 more)

### Community 140 - "Statistics.tsx"
Cohesion: 0.08
Nodes (40): buildDateParams(), FilterConfigStat, getFilterConfigStats(), getHistoryStats(), getSourcesByDate(), getSourcesByHour(), getSourcesByWeekday(), HistoryStat (+32 more)

### Community 142 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, moduleResolution, noEmit (+11 more)

### Community 143 - "Plan 0: Observability (Foundation for All Improvements)"
Cohesion: 0.09
Nodes (22): aiEnrich3, aiEnrich (3 files), aiEnrichNew, `apps/backend/api/metrics.py`, `apps/commonlib/commonlib/metrics_collector.py`, `apps/commonlib/commonlib/observability.py`, Architecture, Architecture (+14 more)

### Community 144 - "routes.py"
Cohesion: 0.27
Nodes (15): answer(), answer_batch(), follow_up(), health(), AnswerRequest, AnswerResponse, BatchAnswerItem, BatchAnswerRequest (+7 more)

### Community 145 - "CompanySynonymRepository"
Cohesion: 0.22
Nodes (12): CompanySynonymRepository, test_add_to_group(), test_add_to_group_failure_is_logged(), test_create_group(), test_create_group_empty(), test_find_synonyms(), test_find_synonyms_not_found(), test_list_groups() (+4 more)

### Community 146 - "TestIndeedScraplingNavigator"
Cohesion: 0.17
Nodes (8): create_mock_scrapling_service(), _make_navigator(), MockSelector, _new_dom_page(), css(), TestIndeedScraplingNavigator, create_mock_selector(), create_mock_selector()

### Community 148 - "console_render_test.py"
Cohesion: 0.10
Nodes (11): color_enabled(), console_mode(), _env(), render_console(), set_console_mode(), split_console_text(), stripAnsi(), console() (+3 more)

### Community 151 - "IndeedScraplingNavigator"
Cohesion: 0.10
Nodes (7): Supported Sites, IndeedScraplingExecutor, TestIndeedScraplingExecutor, _extract_location(), _extract_text(), IndeedScraplingNavigator, _modality_badge()

### Community 152 - "DashboardApi.ts"
Cohesion: 0.13
Nodes (18): dashboardApi, DashboardData, OllamaError, OllamaStatus, ServiceError, ServiceMetrics, ServiceStatus, OllamaStatus() (+10 more)

### Community 153 - "get"
Cohesion: 0.13
Nodes (20): get_enum_values(), get_schema(), get_timezone(), health_check(), get_archived_history_stats(), get_archived_sources_by_date(), get_archived_sources_by_hour(), get_archived_sources_by_weekday() (+12 more)

### Community 155 - "manifest.json"
Cohesion: 0.12
Nodes (15): background, service_worker, content_scripts, description, host_permissions, icons, 128, 16 (+7 more)

### Community 157 - "WakeableTimer"
Cohesion: 0.08
Nodes (25): Configuration, Structured logging, Logs, Logs, Logs, Architecture, Configuration, Structured logging (+17 more)

### Community 159 - "jobs_test.py"
Cohesion: 0.13
Nodes (19): get_service(), get_watcher_service(), get_query_from_mock(), mock_job_dict(), request_jobs(), mock_db_session(), mock_jobs_service(), mock_watcher_service() (+11 more)

### Community 160 - "BrowserService"
Cohesion: 0.08
Nodes (3): BrowserService, _events(), TestTabLogging

### Community 161 - "connection_manager_test.py"
Cohesion: 0.18
Nodes (8): _parse_host_targets(), _parse_ip_range(), test_parse_host_targets(), test_parse_host_targets_cleanup(), test_parse_ip_range(), test_parse_ip_range_diff_prefix(), test_parse_ip_range_end_before_start_raises(), test_parse_ip_range_three_octets()

### Community 162 - "architecture_test.py"
Cohesion: 0.12
Nodes (22): check_layer(), get_file_imports(), _validate_dependencies(), get_console_violations(), get_print_violations(), _is_log_call(), getLongFiles(), get_test_naming_violations() (+14 more)

### Community 163 - "stringUtil.py"
Cohesion: 0.26
Nodes (7): hasLen(), hasLenAnyText(), removeBlanks(), removeExtraEmptyLines(), removeNewLines(), toBool(), TestStringUtil

### Community 164 - "ConcreteNavigator"
Cohesion: 0.12
Nodes (3): ConcreteNavigator, TestBaseNavigator, TestStructuredLogging

### Community 166 - "query_openrouter"
Cohesion: 0.17
Nodes (11): _get_api_key(), _get_max_tokens(), _is_valid_json(), ping_openrouter(), query_openrouter(), _strip_fences(), _build_response(), make_choice_response() (+3 more)

### Community 167 - "Screenshots"
Cohesion: 0.06
Nodes (34): AI daemons & fullstack app logs, AI Job Search Monorepo  [![master CI](https://img.shields.io/github/actions/workflow/status/davidgfolch/AI-job-search/ci.yml?branch=master&label=master%20CI)](https://github.com/davidgfolch/AI-job-search/actions/workflows/ci.yml?branch=master)  [![staging CI](https://img.shields.io/github/actions/workflow/status/davidgfolch/AI-job-search/ci.yml?branch=staging&label=staging%20CI)](https://github.com/davidgfolch/AI-job-search/actions/workflows/ci.yml?branch=staging), Build the graph, CI / GitHub Automation, Cross-module edges, Distributed execution, Docker Compose Profiles, Documentation (+26 more)

### Community 168 - ".layout_check.cjs"
Cohesion: 0.10
Nodes (20): api, distinctBands, extX, fn, fs, html, internal, intMaxX (+12 more)

### Community 169 - "configure_logging"
Cohesion: 0.21
Nodes (6): configure_logging(), _env(), get_app_name(), _stamp_app_name(), TestConsoleField, TestAppNameResolution

### Community 170 - "selenium/test/conftest.py"
Cohesion: 0.27
Nodes (6): action_chains(), driver(), make_element(), no_sleep(), service(), wait_mock()

### Community 172 - "Skill"
Cohesion: 0.26
Nodes (9): Skill, SkillsService, test_bulk_create_skills(), test_bulk_create_skills_logs_failures(), test_create_skill(), test_delete_skill(), test_list_skills(), test_normalize_skill_name() (+1 more)

### Community 173 - "ScrapperStateCalculator"
Cohesion: 0.07
Nodes (12): get_tz(), getDatetimeNow(), getSeconds(), getTimeUnits(), parseDatetime(), TestDatetimeStr, TestGetTz, TestParseDatetime (+4 more)

### Community 174 - "mockRepo"
Cohesion: 0.16
Nodes (23): mockRepo(), test_config_for_job_exposes_priority_config(), test_count_pending_cv_match(), test_count_pending_enrichment(), test_get_enrichment_error_id_retry(), test_get_job_to_enrich(), test_get_job_to_match_cv(), test_get_job_to_retry() (+15 more)

### Community 175 - "scheduler_test.py"
Cohesion: 0.23
Nodes (18): _parse_cadency(), Scheduler, _log_events(), _MockJob, test_parse_cadency_days(), test_parse_cadency_default(), test_parse_cadency_hours(), test_parse_cadency_minutes() (+10 more)

### Community 177 - "testSetup.ts"
Cohesion: 0.17
Nodes (16): createAxiosInstanceMock(), createAxiosMock(), mockAxios, setupAxiosMock(), cleanupDOMMocks(), setupDOMMocks(), setupElementSizeMocks(), setupIntersectionObserverMock() (+8 more)

### Community 178 - "AGENTS.md"
Cohesion: 0.09
Nodes (21): Architecture, Build and Development Commands, Code Style, Configuration, Database, Database Safety (ask before any write), Documentation Sync (mandatory, automatic), E2E Tests (apps/e2e) (+13 more)

### Community 179 - "patch"
Cohesion: 0.13
Nodes (9): auto_discover_host(), discover_mysql_hosts(), verify_mysql(), TestAutoDiscoverHost, TestDiscoverMySQLHosts, TestVerifyMySQL, _probe_mysql(), _resolve_db_host() (+1 more)

### Community 180 - "graphify-html-grouped.py"
Cohesion: 0.11
Nodes (18): Always invoke through the repo scripts, graphify development, Hard rule: `graphify-out/graph.html` is repo-owned, Hard rule: never edit the uv-installed graphify package, How to change or improve graphify, Verify the install is pristine, When NOT to use this skill, Where customization actually lives (+10 more)

### Community 182 - "JobTable.test.tsx"
Cohesion: 0.09
Nodes (22): Keeping the Selected Job Visible, calculateLapsedTime(), calculateLapsedTimeDetail(), getDayDiff(), getLapsed(), getLapsedParts(), getLapsedTime(), LapsedTime (+14 more)

### Community 183 - "e2e/package.json"
Cohesion: 0.12
Nodes (16): devDependencies, coverage-badges-cli, monocart-coverage-reports, @playwright/test, @types/node, typescript, coverage-badges-cli, @types/node (+8 more)

### Community 184 - "generate_config_view_sql"
Cohesion: 0.23
Nodes (6): test_drop_config_view_sql(), test_generate_config_view_sql(), test_generate_config_view_sql_with_all_filters(), test_generate_config_view_sql_with_duplicated(), test_generate_config_view_sql_with_flat_boolean_filters(), generate_config_view_sql()

### Community 186 - "aiEnrich3/pipeline.py"
Cohesion: 0.10
Nodes (10): ExtractionPipeline, SalaryExtractor, SkillsExtractor, extractor(), test_extract_salary(), extractor(), test_extract_skills(), mock_pipeline_deps() (+2 more)

### Community 187 - "AGENTS.md"
Cohesion: 0.09
Nodes (22): AGENTS.md, Architecture Patterns, Backend (FastAPI Layered), Build & Test Commands, Code Style Guidelines, Database Safety (ask before any write), Definition of Done, Development & Linting (+14 more)

### Community 188 - "resolve_ollama_url"
Cohesion: 0.13
Nodes (5): _is_auto_spec(), resolve_ollama_url(), TestFallbackLoggedOnce, TestLanDiscoveryFallback, TestResolveOllamaUrl

### Community 190 - "keep_system_awake.py"
Cohesion: 0.18
Nodes (9): _clear_power_request(), _close_handle(), DetailedStructure, KeepSystemAwake, REASON_CONTEXT, ReasonUnion, _try_power_request(), _use_legacy_api() (+1 more)

### Community 191 - "TestQuestionAnsweringService"
Cohesion: 0.21
Nodes (4): TestQuestionAnsweringService, make_mock_cfg(), make_mock_provider(), TempFiles

### Community 193 - "company_synonyms.py"
Cohesion: 0.23
Nodes (11): add_to_group(), create_synonym_group(), get_synonyms(), list_synonym_groups(), remove_name(), SynonymAddRequest, SynonymGroup, SynonymGroupCreate (+3 more)

### Community 194 - "process_skill_enrichment"
Cohesion: 0.17
Nodes (13): log_no_pending_skills(), parse_skill_llm_output(), process_skill_enrichment(), test_parse_skill_llm_output(), test_process_skill_enrichment_check_empty_false(), test_process_skill_enrichment_description_with_error(), test_process_skill_enrichment_error_in_context(), test_process_skill_enrichment_error_in_generation() (+5 more)

### Community 195 - "create_mock_db"
Cohesion: 0.21
Nodes (13): test_add_to_group(), test_create_group(), test_create_group_invalid(), test_get_synonyms(), test_get_synonyms_not_found(), test_list_synonym_groups(), test_list_synonym_groups_empty(), test_remove_name() (+5 more)

### Community 196 - "CombinedStatsRepository"
Cohesion: 0.29
Nodes (6): CombinedStatsRepository, test_get_combined_history_stats_df(), test_get_combined_history_stats_df_with_dates(), test_get_combined_sources_by_date_df_with_dates(), test_get_combined_sources_by_hour_df_with_dates(), test_get_combined_sources_by_weekday_df_with_dates()

### Community 197 - "extract_boolean_filters"
Cohesion: 0.13
Nodes (3): build_where_params(), extract_boolean_filters(), TestExtractBooleanFilters

### Community 198 - "DriverUtil"
Cohesion: 0.17
Nodes (3): DriverUtil, _events(), TestDriverLogging

### Community 199 - "Advanced usages"
Cohesion: 0.11
Nodes (17): stream(), Advanced usages, Concurrency Control, Detailed Stats, How It Works, Knowing If You're Resuming, Lifecycle Hooks, Logging (+9 more)

### Community 202 - "AI Job Search — Metrics & Observability"
Cohesion: 0.12
Nodes (17): Accessing the Dashboard, Adding a New Enrichment Module, AI Job Search — Metrics & Observability, Architecture, Business Overview, Dashboard, Data Flow, Docker Volume Mounts for Logs (+9 more)

### Community 203 - "settings_service.py"
Cohesion: 0.17
Nodes (14): get_env_settings(), get_scrapper_state(), get_env_settings(), get_scrapper_state(), update_env_setting(), update_env_settings_bulk(), update_scrapper_state(), test_get_env_settings() (+6 more)

### Community 204 - "Querying elements"
Cohesion: 0.15
Nodes (13): Advanced examples, CSS/XPath selectors, Examples, Examples, Filters-based searching, Finding Similar Elements, Generating selectors, Querying elements (+5 more)

### Community 205 - "FastCVMatcher"
Cohesion: 0.19
Nodes (18): FastCVMatcher, mock_all(), patched_matcher(), reset_shared_state(), test_disabled(), test_footer_logs_summary(), test_init(), test_job_none() (+10 more)

### Community 206 - "WatcherService"
Cohesion: 0.22
Nodes (8): get_watcher_stats(), mock_repo(), test_get_watcher_stats(), test_get_watcher_stats_error_handling(), test_get_watcher_stats_naive_local_input(), test_get_watcher_stats_string_dates(), test_get_watcher_stats_timezone_mismatch(), WatcherService

### Community 207 - "AI Job Search API"
Cohesion: 0.12
Nodes (16): AI Job Search API, API Documentation, API Endpoints, Company Synonyms, Database, Features, How it affects the applied-by-company search, Installation (+8 more)

### Community 208 - "JobDeleteRepository"
Cohesion: 0.21
Nodes (11): JobDeleteRepository, mock_mysql(), test_delete_jobs_by_filter(), test_delete_jobs_by_ids(), test_delete_jobs_by_ids_empty(), test_delete_jobs_with_snapshots(), test_get_jobs_by_filter(), test_update_jobs_by_filter() (+3 more)

### Community 209 - "SkillsRepository"
Cohesion: 0.27
Nodes (14): SkillsRepository, test_create_skill(), test_delete_skill(), test_find_by_name_case_insensitive_found(), test_find_by_name_case_insensitive_invalid_json(), test_find_by_name_case_insensitive_not_found(), test_list_skills(), test_list_skills_invalid_json() (+6 more)

### Community 210 - "json"
Cohesion: 0.11
Nodes (20): ExtractionValidationError, parse_company_result(), parse_extraction_result(), query_and_parse(), query_company(), _query_retry(), _strip_code_fence(), validate_extraction_result() (+12 more)

### Community 211 - "exceptionUtil_test.py"
Cohesion: 0.16
Nodes (15): wrapper(), filter_trace_by_paths(), getProjectTraceItems(), try_or_warn(), fail_fn(), ok_fn(), test_cleanUnresolvedTrace(), test_filter_trace_by_paths_apps_only() (+7 more)

### Community 212 - "MongoDbProvider"
Cohesion: 0.22
Nodes (7): get_mongo_provider(), MongoDbProvider, test_get_database_returns_database(), test_get_database_write_returns_writer(), test_get_mongo_provider_caches(), test_get_mongo_provider_different_keys(), test_provider_creates_read_and_write_clients()

### Community 213 - "AI Job Search Web UI"
Cohesion: 0.12
Nodes (16): AI Job Search Web UI, Backend Discovery, Coverage, Environment Variables (`.env` & `.env.secrets`), Features, Infinite Scroll Pagination, Installation, Prerequisites (+8 more)

### Community 214 - "JobSnapshotService"
Cohesion: 0.10
Nodes (4): JobSnapshotService, mock_repo(), service(), test_maybe_create_snapshot_on_update()

### Community 215 - "dependencies"
Cohesion: 0.20
Nodes (10): dependencies, axios, prismjs, react, react-dom, react-markdown, react-router-dom, react-simple-code-editor (+2 more)

### Community 216 - "os"
Cohesion: 0.27
Nodes (4): createFolder(), getSrcPath(), listFiles(), TestFileSystemUtil

### Community 217 - "panel.js"
Cohesion: 0.16
Nodes (14): answerAll(), answerAllBtn, container, detectAllFields(), errorSection, errorText, fields, fillAllBtn (+6 more)

### Community 218 - "AI Form Filler"
Cohesion: 0.13
Nodes (15): 1. Prepare context documents, 2. Start the backend, 3. Install the browser extension, AI Form Filler, AI Providers, API Endpoints, Architecture, Development (+7 more)

### Community 219 - "cron/test/main_test.py"
Cohesion: 0.22
Nodes (12): run(), _events(), log_dir(), _raw_log(), _run_one_tick(), _StopLoop, test_run_configures_logging_before_connecting_to_mongo(), test_run_emits_lifecycle_events_in_order() (+4 more)

### Community 220 - "ollama_client_test.py"
Cohesion: 0.17
Nodes (8): _host_ip(), clean_fallback_urls(), clear_probe_cache(), inference_probe_ok(), no_lan_scan(), no_retry_sleep(), single(), TestHostIp

### Community 221 - "CVLoader"
Cohesion: 0.24
Nodes (4): CVLoader, extractTextFromPDF(), TestCVLoader, TestCVLoaderTextPath

### Community 222 - "Plan C: Two-Stage Pipeline (aiEnrich3 Fast Path + aiEnrich LLM Fallback)"
Cohesion: 0.12
Nodes (15): `apps/aiEnrich3/src/aiEnrich3/pipeline.py`, `apps/aiEnrich/pyproject.toml`, `apps/aiEnrich/src/aiEnrich/dataExtractor.py`, `apps/aiEnrich/src/aiEnrich/hybrid_extractor.py` (new), Architecture, Files to Modify, Goal, Implementation Order (+7 more)

### Community 223 - "Plan E: Prompt & Token Optimization (Quick Wins)"
Cohesion: 0.12
Nodes (15): Dependencies, E.1: Reduce Output Tokens (`num_predict`), E.2: Input Compression, E.3: Ollama JSON Mode, E.4: Optimized Prompt Template, E.5: Disable Skill Enrichment in Main Loop, Files to Modify, Goal (+7 more)

### Community 224 - "Installation Steps"
Cohesion: 0.10
Nodes (21): 1. Install Python 3.11, 2. Install Poetry (Python), 3. Install uv (Python), 4. Install Node.js & npm, 5. Install GitHub CLI (recommended), 6.1 ISP blocking the Ollama registry (e.g. Movistar), 6. Install Ollama & required models, 7.1 Install Google Chrome & system libraries (scrapper) (+13 more)

### Community 225 - "ollama_client.py"
Cohesion: 0.16
Nodes (9): TestProcessJobSafeBackend, _candidate_urls(), _discover_ollama_lan_url(), _generate_first_reachable(), _log_response(), OllamaResponse, _query_url(), _server_ready() (+1 more)

### Community 226 - "README.md"
Cohesion: 0.19
Nodes (6): AI CV Matcher, Quickstart, Requirements, aiEnrich3, Job selection, Setup

### Community 227 - "extractors/test/modality_extractor_test.py"
Cohesion: 0.20
Nodes (6): ExtractionResult, ModalityType, ModalityExtractor, extractor(), test_default_pipeline_is_pinned_to_cpu(), test_extract_modality()

### Community 228 - "SnapshotsRepository"
Cohesion: 0.21
Nodes (12): SnapshotsRepository, mock_connection(), test_get_history_stats_df(), test_get_history_stats_df_with_dates(), test_get_snapshot_count_by_platform(), test_get_snapshot_count_by_reason(), test_get_sources_by_date_df(), test_get_sources_by_date_df_with_dates() (+4 more)

### Community 229 - "statistics_service_test.py"
Cohesion: 0.14
Nodes (9): StatisticsService, mock_filter_repo(), mock_jobs_repo(), mock_repo(), service(), test_get_history_stats(), test_get_history_stats_with_dates(), test_get_sources_by_date() (+1 more)

### Community 230 - "CronStateRepository"
Cohesion: 0.12
Nodes (9): CronStateRepository, mock_mongo_provider(), repo(), CompanySalaryHistoryJob, test_job_has_name_and_cadency(), test_job_run_no_prior_state(), test_job_run_with_prior_state(), CronJob (+1 more)

### Community 231 - "CompanySalaryHistoryScanner"
Cohesion: 0.40
Nodes (9): CompanySalaryHistoryScanner, test_scanner_backfill_new_jobs(), test_scanner_imports(), test_scanner_incremental_new_jobs(), test_scanner_last_run_at_no_updates(), test_scanner_no_new_jobs(), test_scanner_updated_jobs_no_prior_record(), test_scanner_updated_jobs_salary_changed() (+1 more)

### Community 233 - "environmentUtil.py"
Cohesion: 0.09
Nodes (15): checkEnvReload(), _get_mtime(), getEnvAll(), getEnvBool(), getEnvByPrefix(), getEnvModified(), getEnvMultiline(), _logEnvLoaded() (+7 more)

### Community 234 - "Plan F: Combined / Recommended Approach"
Cohesion: 0.13
Nodes (14): Architecture, Comparison Script, Configuration, Goal, Gradual Rollout, Implementation Phases, Per-Phase Validation, Performance Budget (+6 more)

### Community 235 - "AiEnrichRepository"
Cohesion: 0.14
Nodes (5): LLM Backend Selection, Ollama backend (default), OpenRouter backend (cloud), _update_error_state(), AiEnrichRepository

### Community 236 - "jobs_service_test.py"
Cohesion: 0.11
Nodes (4): mock_db(), service(), test_bulk_update_jobs(), test_update_job_creates_snapshot()

### Community 237 - "backendDiscovery.ts"
Cohesion: 0.20
Nodes (9): cidrToHosts(), detectLocalSubnets(), discoverBackendUrl(), probeBackend(), scanPort(), createMockSocket(), socketFactory(), vite (+1 more)

### Community 238 - "jobQueryService_test.py"
Cohesion: 0.18
Nodes (4): mock_repo(), mock_synonym_service(), service(), test_get_applied_jobs_by_company_name_empty_company()

### Community 239 - "jobs_applied_test.py"
Cohesion: 0.21
Nodes (8): test_get_applied_jobs_by_company(), test_get_applied_jobs_by_company_empty_string(), test_get_applied_jobs_by_company_missing_parameter(), test_get_applied_jobs_by_company_special_characters(), test_get_applied_jobs_partial_search_exception(), test_get_applied_jobs_partial_search_exclusions(), test_get_applied_jobs_sql_injection(), test_get_applied_jobs_with_synonym_expansion()

### Community 240 - "@testing-library/react"
Cohesion: 0.07
Nodes (23): ConfirmModal(), ConfirmModalProps, Modal(), ModalProps, useAutoResizeTextArea(), useConfirmationModal(), EditSynonymGroupModal(), EditSynonymGroupModalProps (+15 more)

### Community 241 - "JobsRepository"
Cohesion: 0.09
Nodes (7): _execute_with_error_handler(), JobsRepository, mock_db(), repo(), test_fetch_job_row_and_columns(), test_update_job_empty_data(), test_update_job_found()

### Community 242 - "patch"
Cohesion: 0.24
Nodes (4): auto_discover_host(), verify_ollama(), TestAutoDiscoverHost, TestVerifyOllama

### Community 243 - "FilterConfigurations.tsx"
Cohesion: 0.15
Nodes (14): ConfigurationInput(), ConfigurationInputProps, byCompanyConfigs, TestConfig, testConfigs, ADDITIONAL_DEFAULTS, CLEAN_OLD_JOBS_CONFIG, FilterConfigurations() (+6 more)

### Community 244 - "systemUtil.py"
Cohesion: 0.29
Nodes (5): isDocker(), isLinuxOS(), isMacOS(), isWindowsOS(), TestSystemUtil

### Community 245 - "JobSnapshotRepository"
Cohesion: 0.08
Nodes (7): JobSnapshotRepository, mock_mysql(), repo(), test_build_snapshot_query_and_params(), test_build_snapshot_query_empty_job(), test_default_mysql_creates_instance(), test_save_snapshot()

### Community 246 - "get_logger"
Cohesion: 0.17
Nodes (4): get_logger(), TestConsoleEnd, TestFileOnlyRecords, Phase 0 — Root causes in `commonlib/observability.py`

### Community 247 - "Plan D: GGUF Quantized Models via llama-cpp-python"
Cohesion: 0.14
Nodes (13): `apps/aiEnrichNew/pyproject.toml`, `apps/aiEnrichNew/src/aiEnrichNew/llm_client.py`, `apps/aiEnrichNew/src/aiEnrichNew/llm_utils.py`, Architecture, Files to Modify, Goal, Implementation Order, Installation (+5 more)

### Community 248 - "aiEnrichSkill"
Cohesion: 0.18
Nodes (11): aiEnrichSkill, Backends, Configuration, Dependencies, General, HuggingFace Backend, Linux / Mac, Manual (+3 more)

### Community 249 - "useAutoLoadMore.fixtures.tsx"
Cohesion: 0.21
Nodes (20): fireIntersection(), fireResize(), fireScroll(), flushFrames(), Harness(), HarnessProps, hideSentinel(), installObserverMocks() (+12 more)

### Community 250 - "_process_job_safe"
Cohesion: 0.15
Nodes (9): _handle_error(), _process_job_safe(), _query_company(), _save(), build_extraction_prompt(), _ollama_reply(), _process_unspecified_job(), TestCompanyRequestWiring (+1 more)

### Community 251 - "validationUtils.ts"
Cohesion: 0.38
Nodes (6): getFilesRecursively(), getTestFiles(), extractImports(), ImportViolation, checkImportViolation(), validateFeatureFolder()

### Community 252 - "Auto-merge (staging gate)"
Cohesion: 0.13
Nodes (15): Adding a new app, Auto-merge (staging gate), Behavior, Change detection rules, CI / GitHub Actions Pipeline, Coverage gates, Dependabot, Ecosystems & cadency (+7 more)

### Community 253 - "FilterConfigSelector"
Cohesion: 0.05
Nodes (47): _getJobBatches(), test_build_jobs_where_clause_boolean_filters(), test_build_jobs_where_clause_created_after(), test_build_jobs_where_clause_modality(), test_build_jobs_where_clause_search(), test_build_jobs_where_clause_status(), test_parse_job_order(), _get_where() (+39 more)

### Community 254 - "graphify-inject-edges.py"
Cohesion: 0.25
Nodes (6): _belongs_to_module(), find_representative_node(), inject_edges(), load_graph(), main(), save_graph()

### Community 256 - "observability_test.py"
Cohesion: 0.22
Nodes (5): job_log_context(), _events(), fake_app(), log_dir(), TestJobLogContext

### Community 257 - "StatisticsArchivedService"
Cohesion: 0.16
Nodes (4): app(), mock_service(), test_archived_endpoints(), StatisticsArchivedService

### Community 258 - "service_mock"
Cohesion: 0.26
Nodes (3): service_mock(), TestKeyboardInterrupt, TestKeywordLoop

### Community 260 - "Common Library"
Cohesion: 0.25
Nodes (7): Common Library, Installation, MySQL connection, Resolution order, Supported host formats, Testing, Usage

### Community 262 - "log_file_path"
Cohesion: 0.23
Nodes (4): log_file_path(), _events(), _read(), TestJsonlRecords

### Community 263 - "DdlRepository"
Cohesion: 0.17
Nodes (10): test_get_schema(), DdlRepository, test_get_enum_values(), test_get_enum_values_not_enum(), test_get_enum_values_not_found(), test_get_keywords(), test_get_schema(), DdlService (+2 more)

### Community 264 - "TODO"
Cohesion: 0.17
Nodes (11): apps/aiEnrich, apps/aiEnrich3, apps/aiEnrichNew, apps/backend, apps/commonlib, apps/scrapper, apps/web, cross module tasks (+3 more)

### Community 266 - "Workflow"
Cohesion: 0.14
Nodes (13): 1. List open Dependabot PRs, 2. Process each PR (smallest PR number first), 3. Changelog / breaking-change gate, 4. Run the TDD pipeline for the module, 5. Sandbox build+run the affected docker-compose services and check logs — MANDATORY GATE, 6. Green result, 7. Red result, 8. Wrap-up (+5 more)

### Community 268 - "JobDeleteService"
Cohesion: 0.15
Nodes (3): JobDeleteService, extract_filter_params(), TestExtractFilterParams

### Community 269 - "dashboard_repository_test.py"
Cohesion: 0.09
Nodes (32): get_services_status(), DashboardRepository, resolve_log_path(), test_check_ollama_errors(), test_check_ollama_errors_no_matches(), test_check_ollama_errors_recency(), test_log_source_is_logged_as_source_module(), test_read_last_activity() (+24 more)

### Community 270 - "Company Salary History Scanner"
Cohesion: 0.17
Nodes (10): 1. New job backfill (`_fetch_jobs`), 2. Updated job detection (`_fetch_updated`), Company name matching, Company Salary History Scanner, Configuration, Data model, Duplicate prevention, How it works (+2 more)

### Community 271 - "IndeedNavigator"
Cohesion: 0.10
Nodes (3): IndeedExecutor, TestIndeedExecutor, IndeedNavigator

### Community 272 - "ScrapperStateRepository"
Cohesion: 0.29
Nodes (3): ScrapperStateRepository, mock_db(), repo_with_mock()

### Community 273 - "mysql_sync.py"
Cohesion: 0.09
Nodes (19): build_dump_cmd(), build_restore_cmd(), confirm(), dump_local(), dump_tables(), main(), make_dump_path(), preflight_target() (+11 more)

### Community 274 - "frontend-coverage-gate.mjs"
Cohesion: 0.13
Nodes (13): byKey(), drift, e2e, files, GATED, keyOf(), METRICS, MIN (+5 more)

### Community 275 - "process_batch"
Cohesion: 0.22
Nodes (8): get_gpu_cleanup(), process_batch(), test_get_gpu_cleanup_default_true(), test_cleanup_gpu(), test_process_batch_empty(), test_process_batch_inference_error(), test_process_batch_success(), test_process_batch_tokenizer_error()

### Community 276 - "commonlib"
Cohesion: 0.18
Nodes (11): ai-job-search, aiCvMatcher, aiEnrich, aiEnrich3, aiEnrichNew, aiEnrichSkill, aiFormFiller, api (+3 more)

### Community 279 - "log_capture.py"
Cohesion: 0.06
Nodes (9): mock_mysql(), mock_persistence_manager(), service(), TestLinkedinService, TestTecnoempleoService, assert_console_text(), assert_logged(), logged_calls() (+1 more)

### Community 280 - "Version Bumper Instructions"
Cohesion: 0.17
Nodes (11): 1. Detect Modified Apps, 2. Ask User for Bump Type, 3. Update the Version File, 4. Sync commonlib Dependency Version, 5. Version Reference Table, 6. Verify, aiFormFiller extension (extension/manifest.json):, npm apps (web, e2e — package.json): (+3 more)

### Community 281 - "captured_records"
Cohesion: 0.06
Nodes (27): printPage(), printScrapperTitle(), removeUrlParameter(), test_get_env_vars_missing_logs_error_without_secret_values(), test_join(), test_print_page(), test_print_scrapper_title(), test_remove_invalid_scapes() (+19 more)

### Community 282 - "terminalUtil.py"
Cohesion: 0.06
Nodes (30): red(), get_debug(), ScrapperScheduler, mocks(), runPreload(), create_executor(), process_page_url(), _get_executor_names() (+22 more)

### Community 284 - "aiEnrich/test/dataExtractor_test.py"
Cohesion: 0.29
Nodes (6): clean_env(), mock_deps(), test_get_backend(), test_get_openrouter_base_url(), test_get_openrouter_fallback_model(), test_get_openrouter_model()

### Community 285 - "GlassdoorExecutor_test.py"
Cohesion: 0.09
Nodes (14): find_last_duplicated(), test_find_last_duplicated_empty_args(), test_find_last_duplicated_exclude_id(), test_find_last_duplicated_found(), test_find_last_duplicated_joppy(), test_find_last_duplicated_not_found(), test_find_last_duplicated_unspecified_company(), mock_env_vars() (+6 more)

### Community 286 - "InfojobsExecutor_test.py"
Cohesion: 0.09
Nodes (9): mock_env_vars(), mock_mysql(), mock_persistence_manager(), mock_selenium(), silence_console(), TestInfojobsService, TestLoadRow, InfojobsService (+1 more)

### Community 287 - "append_jsonl"
Cohesion: 0.23
Nodes (5): append_jsonl(), make_jsonl_writer(), _events(), TestAppend, TestWriterFactory

### Community 288 - "Quick Start Commands for Docker Development"
Cohesion: 0.20
Nodes (10): All Services, Core Services (Backend + Web + Viewer), Development Tips, Quick Start Commands for Docker Development, Related Documentation, Scrapper (runs on the host, not in Docker), Service URLs, Troubleshooting (+2 more)

### Community 293 - "watcher_refresh.spec.ts"
Cohesion: 0.26
Nodes (7): MOCK_JOB_1, createJobsListRoute(), markJobAsApplied(), setupFilterConfigurationMock(), setupJobsMocks(), setupWatcherStatsMock(), verifyNoRefresh()

### Community 294 - ".checkboxUnselect"
Cohesion: 0.27
Nodes (3): _aria_checkbox(), _native_checkbox(), TestCheckboxUnselect

### Community 295 - "cvMatcher.py"
Cohesion: 0.21
Nodes (6): run(), app_events(), enabled(), test_run_configures_logging_before_first_event(), test_run_logs_disabled_and_exits(), test_run_polls_and_logs_the_idle_wait()

### Community 296 - "mysqlUtil.py"
Cohesion: 0.16
Nodes (4): get_connection(), getConnection(), _init_pool(), error()

### Community 297 - "Undetected ChromeDriver Usage"
Cohesion: 0.22
Nodes (8): Benefits, Configuration, How It Works, Option 1: Environment Variable (Recommended), Option 2: Programmatic, Overview, Troubleshooting, Undetected ChromeDriver Usage

### Community 299 - "filter_configurations_test.py"
Cohesion: 0.33
Nodes (9): test_create_configuration(), test_create_duplicate_name(), test_delete_configuration(), test_delete_missing_configuration_logs_rejection(), test_get_all_configurations(), test_get_configuration_by_id(), test_get_missing_configuration_logs_rejection(), test_update_configuration() (+1 more)

### Community 301 - "AI Job Enrichment"
Cohesion: 0.20
Nodes (10): 1. Install `uv` Package Manager, 2. Install Project Dependencies, AI Job Enrichment, Automated Loop, Configuration, Installation, Job selection, Manual Run (Dev) (+2 more)

### Community 302 - "SkillsManager.tsx"
Cohesion: 0.05
Nodes (59): FormField(), FormFieldProps, createHeadingRenderer(), getText(), ReactMarkdownCustom(), ReactMarkdownCustomProps, slugify(), downloadFile() (+51 more)

### Community 303 - "Settings.tsx"
Cohesion: 0.10
Nodes (32): API_BASE_URL, apiClient, MessageContainer(), MessageContainerProps, Messages(), MessagesProps, useDefaultComment(), useEnvSettings() (+24 more)

### Community 304 - "Fetchers basics"
Cohesion: 0.25
Nodes (6): Fetchers basics, Fetchers Overview, Introduction, Parser configuration in all fetchers, Response Object, Set parser config per request

### Community 306 - "metrics_collector.py"
Cohesion: 0.15
Nodes (11): get_job_enabled(), dataExtractor(), retry_failed_jobs(), get_pipeline(), run(), test_dataExtractor_calls_service(), test_retry_calls_service(), mock_dependencies() (+3 more)

### Community 308 - "exceptionHandler.py"
Cohesion: 0.20
Nodes (6): check_for_otp_error(), is_element_present(), raise_if_otp_invalid(), wait_for_cloudflare_filter(), wait_for_element_present(), TestExceptionHandler

### Community 309 - "post"
Cohesion: 0.30
Nodes (10): update_env_setting(), update_env_settings_bulk(), update_scrapper_state(), ScrapperStateUpdateDto, SettingsEnvBulkUpdateDto, SettingsEnvUpdateDto, test_scrapper_state_update_dto(), test_settings_env_bulk_update_dto() (+2 more)

### Community 310 - "run_pipeline"
Cohesion: 0.19
Nodes (6): retry_failed_jobs(), run(), run_pipeline(), TestMain, assert_any_idle(), TestPipeline

### Community 311 - "getEnv"
Cohesion: 0.24
Nodes (15): get_cv_path(), get_hf_model(), get_looking_for_path(), get_max_tokens(), get_openai_api_key(), get_openai_model(), get_openrouter_api_key(), get_openrouter_model() (+7 more)

### Community 313 - "ollama_config_test.py"
Cohesion: 0.12
Nodes (19): _probe_ollama(), get_num_ctx(), get_num_predict(), get_repeat_penalty(), ollama_probe_urls(), strip_provider_prefix(), clean_env(), test_num_ctx_bucketing() (+11 more)

### Community 314 - ".fetch"
Cohesion: 0.08
Nodes (23): Async Session Usage, Basic Usage, Browser Automation, Cloudflare and stealth options, Examples, Real-world example (Amazon), Session Benefits, Session Management (+15 more)

### Community 315 - "docs-sync.py"
Cohesion: 0.43
Nodes (4): already_reminded(), main(), needs_reminder(), remind_path()

### Community 316 - "Plan B: RAG Cache Layer (Skip LLM Inference for Similar Jobs)"
Cohesion: 0.12
Nodes (16): `apps/aiEnrich/pyproject.toml`, `apps/aiEnrich/src/aiEnrich/crew.py`, `apps/aiEnrich/src/aiEnrich/dataExtractor.py`, `apps/aiEnrich/src/aiEnrich/embedding_service.py`, `apps/aiEnrich/src/aiEnrich/rag_cache.py`, Architecture, Dependencies, Files to Create (+8 more)

### Community 318 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, dev, lint, preview, test

### Community 319 - "pandas"
Cohesion: 0.17
Nodes (16): mock_combined_repo(), mock_snapshots_repo(), mock_stats_repo(), service(), test_get_archived_history_stats(), test_get_archived_history_stats_empty(), test_get_archived_sources_by_date(), test_get_archived_sources_by_hour() (+8 more)

### Community 322 - "JobsService"
Cohesion: 0.12
Nodes (25): get_applied_jobs_by_company(), get_service(), bulk_delete_jobs(), bulk_update_jobs(), BulkJobDelete, BulkJobUpdate, create_job(), get_job() (+17 more)

### Community 323 - "web/package.json"
Cohesion: 0.12
Nodes (19): coverage-badges-cli, @types/node, typescript, name, private, type, baseline-browser-mapping, eslint (+11 more)

### Community 324 - "E2E Implementer Instructions"
Cohesion: 0.29
Nodes (6): 1. Location & Structure, 2. Naming Conventions, 3. Best Practices, 4. Architecture Verification, E2E Implementer Instructions, Usage

### Community 325 - "Adaptive scraping"
Cohesion: 0.08
Nodes (23): Adaptive scraping, How the adaptive scraping feature works, How to use adaptive feature, Known Issues, No Matches Found, Real-World Scenario, The CSS/XPath Selection way, The manual way (+15 more)

### Community 326 - "Proxy management and handling Blocks"
Cohesion: 0.20
Nodes (9): Blocked Request Handling, Custom Block Detection, Custom Rotation Strategies, Customizing Retries, Per-Request Proxy Override, Proxy management and handling Blocks, ProxyRotator, Random Rotation (+1 more)

### Community 327 - "job_delete_service_test.py"
Cohesion: 0.19
Nodes (7): mock_get_job(), mock_repo(), service(), service_with_callback(), test_build_snapshot_queries(), test_delete_by_ids_with_callback(), test_update_jobs_by_ids()

### Community 328 - "AI Job Search Default Development Guide"
Cohesion: 0.20
Nodes (10): Agentic SDLC, AI Job Search Default Development Guide, Coverage Gates, Development with VS Code, Documentation Sync, Frontend: web unit + e2e union, Related Documentation, Scrapper: production statements (+2 more)

### Community 329 - "Components"
Cohesion: 0.05
Nodes (30): QuotesSpider, Checkpoint System, Comparison with Scrapy, Components, Crawler Engine, Data Flow, Output, Scheduler (+22 more)

### Community 331 - "TestTecnoempleoSalaryReader"
Cohesion: 0.17
Nodes (3): TestTecnoempleoSalaryReader, Scrapling Implementer Instructions, Usage

### Community 332 - "aiEnrichNew/services/job_enrichment_service.py"
Cohesion: 0.23
Nodes (4): parse_job_enrichment_result(), test_parse_job_enrichment_result(), on_success(), _save_job_result()

### Community 333 - "JobQueryRepository"
Cohesion: 0.29
Nodes (3): JobQueryRepository, test_find_applied_by_company(), scapeRegexChars()

### Community 334 - "Plan A: Direct Ollama API (Remove CrewAI)"
Cohesion: 0.13
Nodes (14): `apps/aiEnrich/pyproject.toml`, `apps/aiEnrich/src/aiEnrich/crew.py`, `apps/aiEnrich/src/aiEnrich/ollama_client.py`, `apps/aiEnrich/src/aiEnrich/skillEnricher.py`, Architecture, Dependencies, Files to Create, Files to Modify (+6 more)

### Community 335 - "Test Implementer Instructions"
Cohesion: 0.25
Nodes (7): 1. Test Location & Structure, 2. Naming Conventions, 3. Coding Best Practices, 4. Running Tests, 5. Architecture Verification, Test Implementer Instructions, Usage

### Community 337 - "AI Enrichment — Speed Improvement Plans"
Cohesion: 0.33
Nodes (5): AI Enrichment — Speed Improvement Plans, Context, Modules Overview, Plans Index, Recommended Order

### Community 338 - "wake_timer_test.py"
Cohesion: 0.23
Nodes (6): mock_sleep(), mock_windows_api(), test_console_timer_calls_wakeable_timer(), test_wakeable_timer_other_os(), test_wakeable_timer_windows(), Full list of arguments

### Community 340 - "Examples"
Cohesion: 0.10
Nodes (19): Basic HTTP Request, Basic Usage, DELETE, Downloading Files, Examples, Form Submission, GET, HTTP Methods (+11 more)

### Community 342 - "content.js"
Cohesion: 0.60
Nodes (3): cssSelector(), detectAllQuestions(), detectQuestion()

### Community 346 - "SalaryHistoryService"
Cohesion: 0.29
Nodes (6): get_company_history(), get_job_history(), get_service(), test_get_service_returns_service(), SalaryHistoryService, test_service_imports()

### Community 347 - "aiEnrichSkill/main.py"
Cohesion: 0.32
Nodes (10): get_backend(), get_max_ollama_failures(), get_ollama_base_url(), run(), test_get_backend_default_ollama(), test_run_disabled(), test_run_enriched_some_skills(), test_run_no_skills_waits() (+2 more)

### Community 348 - "Fix scrapper job failures logged on 2026-10-09"
Cohesion: 0.40
Nodes (4): Fix scrapper job failures logged on 2026-10-09, Outcome, Problem, Solution

### Community 350 - "Agentic SDLC"
Cohesion: 0.22
Nodes (9): Agent Homes, Agentic SDLC, Crawlee (source-page change analysis), Database changes require user permission (enforced guardrail), Dependabot PR workflow, Documentation Sync (automatic, mandatory), Related Documentation, Required Tools (+1 more)

### Community 351 - "sleep"
Cohesion: 0.12
Nodes (5): TestSleep, sleep(), GlassdoorAuthenticator, GlassdoorGmailService, TestGlassdoorGmailService

### Community 352 - "parametrize"
Cohesion: 0.18
Nodes (3): TestCheckNoResults, TestLoadAndProcessRow, TestProcessKeyword

### Community 353 - "uninstall.sh"
Cohesion: 0.32
Nodes (10): app_artifacts_present(), global_tool_installed(), main(), remove_app(), remove_global_tool(), remove_path(), remove_root(), root_artifacts_present() (+2 more)

### Community 354 - "uninstall-menu.ps1"
Cohesion: 0.13
Nodes (13): formatter, ruff, uv, instructions, plugins, disabled, $schema, disabled (+5 more)

### Community 356 - "sqlUtil.py"
Cohesion: 0.12
Nodes (14): avoidInjection(), binaryColumnIgnoreCase(), deleteJobsQuery(), emptyToNone(), formatSql(), getAndFilter(), getColumnTranslated(), inFilter() (+6 more)

### Community 357 - "log_writer_test.py"
Cohesion: 0.17
Nodes (10): _env(), file_backup_count(), file_max_bytes(), get_log_dir(), resolve_read_path(), log_dir(), test_resolve_read_path_falls_back_to_legacy(), test_resolve_read_path_prefers_per_app_name() (+2 more)

### Community 359 - "graphify.sh"
Cohesion: 0.83
Nodes (3): clean_graph(), extract_module(), graphify.sh script

### Community 360 - "backend/conftest.py"
Cohesion: 0.24
Nodes (5): client(), log_records(), read(), _read_jsonl(), Testing log output

### Community 361 - "Scrapling Examples"
Cohesion: 0.33
Nodes (5): Escalation Guide, Examples, Quick Start, Running, Scrapling Examples

### Community 362 - "SalaryHistoryRepository"
Cohesion: 0.15
Nodes (5): get_best_candidate(), search_partial_company(), SalaryHistoryRepository, TestGetBestCandidate, TestSearchPartialCompany

### Community 364 - "coverage.config.ts"
Cohesion: 0.31
Nodes (5): coverageOptions, isProductionFile(), isSourceFile(), WEB_SRC_DIR, monocart-coverage-reports

### Community 365 - "docker-build.md"
Cohesion: 0.40
Nodes (4): Dependency-refresh caveats, Docker container bring-up: always `--build`, Layer caching, When rebuilding is required (why)

### Community 366 - "rotate_if_needed"
Cohesion: 0.40
Nodes (3): rotate_if_needed(), _seed(), TestRotation

### Community 373 - "test-sandbox.sh"
Cohesion: 0.60
Nodes (3): env_file(), module_disabled(), test-sandbox.sh script

### Community 374 - "pytest"
Cohesion: 0.06
Nodes (11): mock_db(), StackTrace, mock_sleep(), mock_selenium(), navigator(), mock_selenium(), navigator(), TestModuleSurface (+3 more)

### Community 376 - "test.sh"
Cohesion: 0.83
Nodes (3): run_e2e_gate(), run_test(), test.sh script

### Community 377 - "Solution"
Cohesion: 0.22
Nodes (7): _writer(), public_record(), Follow-ups, Outcome, Problem, Restore the scrapper console while keeping structured records, Solution

### Community 378 - "scrapper_coverage_gate.py"
Cohesion: 0.36
Nodes (4): _is_production(), main(), _pct(), read_coverage()

### Community 379 - "query_ollama"
Cohesion: 0.16
Nodes (5): query_ollama(), _down(), _ok(), TestProbeCache, TestQueryOllama

### Community 381 - "requests"
Cohesion: 0.48
Nodes (4): _ping_url(), check_backend(), check_ollama(), check_openrouter()

### Community 388 - "execute_with_error_handler"
Cohesion: 0.27
Nodes (6): execute_with_error_handler(), test_database_error_is_logged_without_bind_values(), test_database_error_with_items_returns_error_payload(), test_execute_with_error_handler_success(), callback(), test_execute_with_error_handler_with_items()

### Community 392 - "docker-build.js"
Cohesion: 0.60
Nodes (4): DockerBuildPlugin(), injectBuild(), OTHER_SUBCOMMANDS, setup()

### Community 397 - "statistics_test.py"
Cohesion: 0.48
Nodes (5): test_get_filter_config_stats(), test_get_history_stats(), test_get_history_stats_exclude_old_jobs(), test_get_sources_by_date(), test_get_sources_by_hour()

### Community 398 - "aiEnrich/test/config_test.py"
Cohesion: 0.36
Nodes (5): get_job_enabled(), clean_env(), test_get_job_enabled(), test_get_ollama_base_url(), test_get_timeout_job()

### Community 399 - "browser_service_test.py"
Cohesion: 0.06
Nodes (13): TestBack, TestBrowserServiceInit, TestGetTitle, TestGetUrl, TestLoadPage, TestScrollProgressive, TestScrollToBottom, TestSendEscapeKey (+5 more)

### Community 400 - "1. PYTHON MODULES (Backend & Commonlib)"
Cohesion: 0.29
Nodes (7): 1.1 Critical: Files Exceeding 200-Line Limit (Architecture Rule #1), 1.2 Module Consolidation: AI Enrich Variants, 1.3 Commonlib Coupling Issues, 1.4 Layer Architecture Violations, 1.5 Service Layer Analysis, 1.6 Test Architecture, 1. PYTHON MODULES (Backend & Commonlib)

### Community 401 - "get_pipeline"
Cohesion: 0.44
Nodes (5): get_pipeline(), test_get_pipeline_cuda_available(), test_get_pipeline_initialization(), test_get_pipeline_pad_token_set(), test_get_pipeline_singleton()

### Community 404 - "Contribute"
Cohesion: 0.50
Nodes (4): Contribute, Development guide-lines, Related Documentation, Tests & coverage

### Community 405 - "docs-sync.js"
Cohesion: 0.28
Nodes (7): DOC_SUFFIXES, DocsSyncPlugin(), EDIT_TOOLS, IGNORED_FILES, IGNORED_PREFIXES, needsReminder(), setup()

### Community 409 - "aiEnrichNew"
Cohesion: 0.25
Nodes (8): aiEnrichNew, Configuration, Job selection, Linux / Mac, Manual, Prerequisites, Usage, Windows

### Community 410 - "consoleTimer"
Cohesion: 0.19
Nodes (6): consoleTimer(), consoleTimerDocker(), _consoleTimerLocal(), Spinner, TestSpinner, TestTerminalFunctions

### Community 411 - "install.sh"
Cohesion: 0.52
Nodes (6): is_uv_app(), ollama_hf_spec(), ollama_pull(), ollama_registry_reachable(), ollama_runner(), install.sh script

### Community 540 - "LocalHFProvider"
Cohesion: 0.24
Nodes (4): get_pipeline(), LocalHFProvider, TestGetPipeline, TestLocalHFProvider

### Community 564 - "Documentation Sync (mandatory, automatic)"
Cohesion: 0.33
Nodes (5): Definition-of-done checklist (before reporting done), Doc map: which docs to update for which change, Documentation Sync (mandatory, automatic), Rules, When it applies

### Community 565 - "request_logging_test.py"
Cohesion: 0.09
Nodes (23): _fields(), RequestLoggingMiddleware, _StatusCapture, _asgi_app(), app(), _call(), receive(), send() (+15 more)

### Community 572 - "Phase 8 — Tests and docs"
Cohesion: 0.50
Nodes (3): browser_service(), mock_driver(), Phase 8 — Tests and docs

### Community 698 - "SalaryCalculator.tsx"
Cohesion: 0.13
Nodes (21): { mockPost }, salaryApi, SalaryCalculationRequest, SalaryCalculationResponse, JobDetail(), formatSavedLabel(), SalaryCalculator(), SalaryCalculatorProps (+13 more)

### Community 701 - "Database changes require explicit user permission"
Cohesion: 0.29
Nodes (6): Allowed without permission, Ask like this, Blocked without permission, Database changes require explicit user permission, Enforcement, How to run an approved mutation

### Community 703 - "ddl.sql"
Cohesion: 0.29
Nodes (6): `company_synonyms`, `filter_configurations`, `job_skills`, `job_snapshots`, `jobs`, `scrapper_state`

### Community 705 - "Debug GitHub Actions & Dependabot Runs with `gh`"
Cohesion: 0.40
Nodes (4): Debug GitHub Actions & Dependabot Runs with `gh`, Dependabot update-run failures, Inspect an Actions run, Tips

### Community 718 - "db-mutation.js"
Cohesion: 0.83
Nodes (3): DbMutationPlugin(), findViolation(), setup()

## Knowledge Gaps
- **22 isolated node(s):** `aiCvMatcher`, `aiEnrich3`, `aiEnrichNew`, `aiEnrichSkill`, `aiEnrich` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2469 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **441 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `config()` connect `WakeableTimer` to `vitest`?**
  _High betweenness centrality (0.204) - this node is a cross-community bridge._
- **Are the 66 inferred relationships involving `MysqlUtil` (e.g. with `FastCVMatcher` and `.process_db_jobs()`) actually correct?**
  _`MysqlUtil` has 66 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aiCvMatcher`, `aiEnrich3`, `aiEnrichNew` to the rest of the system?**
  _22 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `green` be split into smaller, more focused modules?**
  _Cohesion score 0.10695187165775401 - nodes in this community are weakly interconnected._
- **Why does `vitest` connect `vitest` to `useViewer.ts`, `App.tsx`, `Statistics.tsx`, `Viewer.tsx`, `JobDetailInfo.tsx`, `DashboardApi.ts`, `PageHeader`, `SkillsManager.tsx`, `Settings.tsx`, `testSetup.ts`, `JobTable.test.tsx`, `ViewerTestUtils.tsx`, `SalaryCalculator.tsx`, `web/package.json`, `useSqlEditor.ts`, `ViewerApi.ts`, `backendDiscovery.ts`, `@testing-library/react`, `FilterConfigurations.tsx`, `useAutoLoadMore.fixtures.tsx`, `validationUtils.ts`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Should `GmailService` be split into smaller, more focused modules?**
  _Cohesion score 0.070578231292517 - nodes in this community are weakly interconnected._
- **Why does `Logs` connect `WakeableTimer` to `time`, `ai_helpers.py`, `AI Job Enrichment`, `logIdleWait`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._