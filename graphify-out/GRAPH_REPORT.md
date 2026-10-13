# Graph Report - ai_job_search  (2026-10-13)

## Corpus Check
- 943 files · ~413,781 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 89 file(s) not represented in the graph (top: .css 34, (none) 21, .bat 16)

## Summary
- 7452 nodes · 16511 edges · 684 communities (244 shown, 440 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1449 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fc06f8bf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- environmentUtil.py
- GmailService
- useJobMutations.ts
- aiEnrichNew/dataExtractor.py
- PersistenceManager
- TestAttributes
- sleep
- Viewer.tsx
- ViewerApi.ts
- metrics_collector_test.py
- captured_records
- TestLinkedinNavigator
- GmailConnectionError
- SeleniumService
- MysqlUtil
- observability_test.py
- IndeedService
- TestTecnoempleoCompanyReader
- sys
- ContextLoader
- prometheus_exporter_test.py
- pytest
- useFilterWatcher.ts
- @testing-library/react
- aiEnrich3/dataExtractor.py
- jobQueryService_test.py
- executor/test/conftest.py
- jobsApi
- Most Important Improvements for this Monorepo
- aiEnrichSkill/test/config_test.py
- TecnoempleoNavigator
- WatcherRepository
- QueryExecutor
- salary_history_repository_test.py
- TestBaseService
- companyExtractor_test.py
- ai_helpers_test.py
- compilerOptions
- FilterConfigSelector
- GlassdoorNavigator
- useSqlEditor.ts
- TestJobRepository
- TestIndeedNavigator
- filter_configurations_service_test.py
- datetime
- @tanstack/react-query
- yellow
- rawToJson
- mysql_discovery_test.py
- AnswerResult
- SalaryCalculator
- skills.py
- filter_configurations_repository_test.py
- scrapper_scheduler_test.py
- persistence_manager_test.py
- seleniumService_test.py
- TestScraplingService
- LinkedinExecutor
- salary_calculator.spec.ts
- devDependencies
- api/salary.py
- FilterConfigurationsService
- aiEnrich/test/dataExtractor_test.py
- TestTecnoempleoNavigator
- StatisticsRepository
- AI Job Enrichment
- find_last_duplicated
- AiEnrichRepository
- Job Scrappers
- aiEnrich/dataExtractor.py
- enrichment_service_test.py
- skills_test.py
- seleniumSocketConnRetry
- Examples
- JobWriteRepository
- viewer.helpers.ts
- Statistics.tsx
- compilerOptions
- Plan 0: Observability (Foundation for All Improvements)
- routes.py
- CompanySynonymRepository
- IndeedScraplingNavigator
- DriverUtil
- TestJobQueries
- TestIndeedService
- IndeedScraplingExecutor
- App.tsx
- get
- manifest.json
- make_jsonl_writer
- jobs_test.py
- connection_manager.py
- architecture_test.py
- stringUtil.py
- ConcreteNavigator
- query_openrouter
- Screenshots
- .layout_check.cjs
- get_logger
- selenium/test/conftest.py
- Skill
- ScrapperStateCalculator
- aiEnrichRepository_test.py
- scheduler_test.py
- TestInfojobsNavigator
- testSetup.ts
- AGENTS.md
- patch
- graphify-html-grouped.py
- JobTable.tsx
- e2e/package.json
- view_generator.py
- aiEnrich3/pipeline.py
- AGENTS.md
- TestConfiguration
- console_render.py
- QuestionAnsweringService
- company_synonyms.py
- process_skill_enrichment
- create_mock_db
- CombinedStatsRepository
- jobs_service.py
- keep_system_awake.py
- TestEmailReader
- TestTransactionManager
- AI Job Search — Metrics & Observability
- settings_service.py
- Querying elements
- FastCVMatcher
- WatcherService
- AI Job Search API
- JobDeleteRepository
- SkillsRepository
- extraction_contract_test.py
- exceptionUtil_test.py
- MongoDbProvider
- commonlib_sql_mysqlutil
- JobSnapshotService
- dependencies
- os
- panel.js
- AI Form Filler
- cron/test/main_test.py
- cron_state_repository_test.py
- CVLoader
- Plan C: Two-Stage Pipeline (aiEnrich3 Fast Path + aiEnrich LLM Fallback)
- Plan E: Prompt & Token Optimization (Quick Wins)
- Installation Steps
- configurations.spec.ts
- README.md
- configure_logging
- SnapshotsRepository
- statistics_service_test.py
- CronStateRepository
- CompanySalaryHistoryScanner
- FilterConfigurationsRepository
- Phases
- Plan F: Combined / Recommended Approach
- dashboard_repository_test.py
- jobs_service_test.py
- backendDiscovery.ts
- CompanySynonymService
- jobs_applied_test.py
- PageHeader
- JobsRepository
- systemUtil.py
- TestProbeMysql
- request_logging.py
- JobSnapshotRepository
- Plan D: GGUF Quantized Models via llama-cpp-python
- aiEnrichSkill
- useAutoLoadMore.fixtures.tsx
- .load
- validationUtils.ts
- Auto-merge (staging gate)
- build_jobs_where_clause
- TestLinkedinService
- StatisticsArchivedService
- service_mock
- IndeedAuthenticator
- Common Library
- api/test/main_test.py
- TestGlassdoorAuthenticator
- DdlRepository
- TODO
- Workflow
- TestApiRoutes
- job_delete_service_test.py
- dashboard_service.py
- Company Salary History Scanner
- IndeedNavigator
- ScrapperStateRepository
- mysql_sync.py
- frontend-coverage-gate.mjs
- process_batch
- commonlib
- ScrapperStateRepository
- TestLinkedinDetailReader
- Version Bumper Instructions
- logIdleWait
- scrapper_scheduler.py
- InfojobsExecutor_test.py
- react
- observability.py
- Quick Start Commands for Docker Development
- company_synonym_service_test.py
- TestGlassdoorNavigator
- TestTecnoempleoService
- get_skill_context
- Cron — Background Scheduler
- Undetected ChromeDriver Usage
- TestKeywordPagination
- filter_configurations_test.py
- vitest
- Settings.tsx
- OpenAIProvider
- json
- TestStealthScripts
- configurations.helpers.ts
- post
- cyan
- getEnv
- TestQueryExecutor
- ollama_client.py
- StealthyFetcher
- Plan B: RAG Cache Layer (Skip LLM Inference for Similar Jobs)
- baseScrapper.py
- scripts
- pandas
- ScraplingService
- TestScrapperConfig
- JobsService
- web/package.json
- E2E Implementer Instructions
- Adaptive scraping
- Proxy management and handling Blocks
- AI Job Search Default Development Guide
- Components
- TestTecnoempleoSalaryReader
- get_connection
- Plan A: Direct Ollama API (Remove CrewAI)
- resolve_mysql_host
- AI Enrichment — Speed Improvement Plans
- console_render_test.py
- Examples
- content.js
- IndeedGmailService
- watcher_refresh.spec.ts
- TestGetConnection
- SalaryHistoryService
- run
- Agentic SDLC
- opencode.json
- sqlUtil_test.py
- log_writer_test.py
- JobReadRepository
- graphify.sh
- Scrapling Examples
- SalaryHistoryRepository
- .test_bound_name_is_kept_without_an_app_frame
- coverage.fixtures.ts
- docker-build.md
- tsconfig.json
- View Backend Logs Instructions
- TestJobBooleanKeys
- test-sandbox.sh
- nvidia-linux-restart.sh
- test.sh
- query_ollama
- aiEnrich/run.sh
- aiEnrichNew/run.sh
- aiEnrichSkill/run.sh
- aiFormFiller/run.sh
- execute_with_error_handler
- backend/run.sh
- cron/run.sh
- scrapper/run.sh
- docker-build.js
- docker-entrypoint.sh
- Migrating from BeautifulSoup to Scrapling
- backend/conftest.py
- statistics_test.py
- aiEnrich/test/config_test.py
- BrowserService
- .fetch
- get_pipeline
- verify_mysql
- web/run.sh
- Contribute
- docs-sync.js
- .claude/rules/architecture-guidelines.md
- .claude/skills/skill-builder/SKILL.md
- Test Implementer Instructions
- aiEnrichNew
- terminalUtil.py
- install.sh
- backup.sh
- restore.sh
- runMysql.sh
- BaseExecutor_test.py
- LocalHFProvider
- Documentation Sync (mandatory, automatic)
- request_logging_test.py
- api/test/settings_test.py
- docs-sync.py
- TestTryTargets
- JobDetail.tsx
- Database changes require explicit user permission
- 1. PYTHON MODULES (Backend & Commonlib)
- ddl.sql
- TestBooleanFilterKeys
- Debug GitHub Actions & Dependabot Runs with `gh`
- TestResolveDbHost
- Crawlee Page Analyst Instructions
- CustomConverter
- TestElementLookup
- .get_job_data
- sync.sh
- db-mutation.js
- mock_sleep
- TestTab
- seleniumSocketConnRetry_test.py
- .update_from_ai

## God Nodes (most connected - your core abstractions)
1. `vitest` - 155 edges
2. `MysqlUtil` - 147 edges
3. `@testing-library/react` - 117 edges
4. `SeleniumService` - 96 edges
5. `PersistenceManager` - 85 edges
6. `react` - 80 edges
7. `yellow()` - 77 edges
8. `getEnv()` - 73 edges
9. `get_logger()` - 68 edges
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

## Communities (684 total, 440 thin omitted)

### Community 2 - "environmentUtil.py"
Cohesion: 0.09
Nodes (15): checkEnvReload(), _get_mtime(), getEnvAll(), getEnvBool(), getEnvByPrefix(), getEnvModified(), getEnvMultiline(), _logEnvLoaded() (+7 more)

### Community 5 - "useJobMutations.ts"
Cohesion: 0.11
Nodes (26): getModalityValues(), useConfirmationModal(), useModalityValues(), STATE_FIELDS, mockSearchParams, createWrapper(), jobs, Props (+18 more)

### Community 8 - "aiEnrichNew/dataExtractor.py"
Cohesion: 0.07
Nodes (23): get_batch_size(), get_enrich_timeout_job(), get_job_enabled(), get_job_system_prompt(), should_cleanup_gpu(), dataExtractor(), retry_failed_jobs(), get_pipeline() (+15 more)

### Community 9 - "PersistenceManager"
Cohesion: 0.06
Nodes (12): mock_env_vars(), mock_mysql(), mock_persistence_manager(), mock_selenium(), TestGlassdoorService, GlassdoorService, TestGlassdoorService, PersistenceManager (+4 more)

### Community 11 - "TestAttributes"
Cohesion: 0.08
Nodes (5): TestAttributes, TestClearInputbox, TestScrollAndClick, TestSendKeys, TestWaits

### Community 13 - "sleep"
Cohesion: 0.09
Nodes (7): decorator(), wrapper(), TestSleep, sleep(), GlassdoorAuthenticator, GlassdoorGmailService, TestGlassdoorGmailService

### Community 17 - "Viewer.tsx"
Cohesion: 0.08
Nodes (41): PinnedConfigurations(), PinnedConfigurationsProps, JobDetailHeader(), JobDetailHeaderProps, JobActions(), JobActionsProps, PanelDivider(), PanelDividerProps (+33 more)

### Community 18 - "ViewerApi.ts"
Cohesion: 0.06
Nodes (43): CvMatchBar(), CvMatchBarProps, Job, JobListResponse, SalaryHistoryEntry, WatcherStats, useJobEditForm(), UseJobEditFormProps (+35 more)

### Community 22 - "metrics_collector_test.py"
Cohesion: 0.10
Nodes (9): f(), MetricsCollector, collector(), reset_singleton(), test_load_corrupted_file(), test_persist_and_load(), test_persist_if_due_skips_when_recent(), test_persist_if_due_writes_when_interval_elapsed() (+1 more)

### Community 23 - "captured_records"
Cohesion: 0.07
Nodes (29): join(), printPage(), printScrapperTitle(), removeInvalidScapes(), removeLinks(), removeUrlParameter(), summarize(), validate() (+21 more)

### Community 28 - "GmailConnectionError"
Cohesion: 0.10
Nodes (7): EmailNotFoundError, GmailConnectionError, GmailTimeoutError, VerificationCodeExtractionError, EmailReader, _message_ref(), TestEmailExceptions

### Community 36 - "observability_test.py"
Cohesion: 0.22
Nodes (5): job_log_context(), _events(), fake_app(), log_dir(), TestJobLogContext

### Community 39 - "IndeedService"
Cohesion: 0.09
Nodes (12): mock_env_vars(), mock_mysql(), mock_persistence_manager(), mock_selenium(), TestCheckNoResults, TestLoadAndProcessRow, TestProcessKeyword, mock_env_vars() (+4 more)

### Community 41 - "sys"
Cohesion: 0.13
Nodes (10): mock_sleep(), mock_windows_api(), test_console_timer_calls_wakeable_timer(), test_wakeable_timer_other_os(), test_wakeable_timer_windows(), cleanup_all_e2e_databases(), get_e2e_connection(), run_e2e_tests() (+2 more)

### Community 42 - "ContextLoader"
Cohesion: 0.23
Nodes (4): init_routes(), ContextLoader, create_app(), TestMain

### Community 43 - "prometheus_exporter_test.py"
Cohesion: 0.15
Nodes (16): get_prometheus_metrics(), build_log_metrics(), build_prometheus_metrics(), test_build_log_metrics_file_oserror(), test_build_log_metrics_invalid_json_lines(), test_build_log_metrics_no_files(), test_build_log_metrics_survives_non_object_lines(), test_build_log_metrics_survives_null_job_id() (+8 more)

### Community 44 - "pytest"
Cohesion: 0.05
Nodes (13): test_parse_job_enrichment_result(), BaseNavigator, check_for_otp_error(), is_element_present(), raise_if_otp_invalid(), wait_for_cloudflare_filter(), wait_for_element_present(), TestExceptionHandler (+5 more)

### Community 45 - "useFilterWatcher.ts"
Cohesion: 0.13
Nodes (16): notificationService, persistenceApi, persistenceDefaults, cleanupMocks(), createWrapper(), mockSavedConfigs, resetTestQueryClient(), setupMocks() (+8 more)

### Community 47 - "@testing-library/react"
Cohesion: 0.08
Nodes (26): defaultProps, defaultProps, renderWithQueryClient(), mockGetFilterConfigStats, mockGetHistoryStats, mockGetSourcesByDate, mockGetSourcesByHour, mockGetSourcesByWeekday (+18 more)

### Community 50 - "aiEnrich3/dataExtractor.py"
Cohesion: 0.13
Nodes (20): get_batch_size(), get_input_max_len(), get_job_enabled(), get_skill_enabled(), getEnvBool(), dataExtractor(), run(), ExtractionPipeline (+12 more)

### Community 51 - "jobQueryService_test.py"
Cohesion: 0.18
Nodes (4): mock_repo(), mock_synonym_service(), service(), test_get_applied_jobs_by_company_name_empty_company()

### Community 52 - "executor/test/conftest.py"
Cohesion: 0.18
Nodes (10): base_mysql(), indeed_executor(), indeed_navigator(), infojobs_executor(), infojobs_navigator(), persistence(), process_keyword(), selenium_service() (+2 more)

### Community 54 - "jobsApi"
Cohesion: 0.16
Nodes (24): MockFilters(), MockJobActions(), MockJobDetail(), MockJobEditForm(), MockJobList(), MockReactMarkdownCustom(), MockSelectableJobList(), MockViewTabs() (+16 more)

### Community 58 - "Most Important Improvements for this Monorepo"
Cohesion: 0.08
Nodes (23): 2.1 Component File Size Analysis, 2.2 Custom Hooks Pattern (Good Practice), 2.3 Architecture Test Coverage, 2.4 Common Components & Reusability, 2.5 API Layer Organization, 2. REACT FRONTEND (apps/web), 3.1 Service Architecture, 3. SCRAPPER MODULE (apps/scrapper) (+15 more)

### Community 62 - "aiEnrichSkill/test/config_test.py"
Cohesion: 0.08
Nodes (43): get_backend(), get_batch_size(), get_enabled(), get_enrich_limit(), get_hf_model_id(), get_hf_repetition_penalty(), get_hf_temperature(), get_hf_top_p() (+35 more)

### Community 63 - "TecnoempleoNavigator"
Cohesion: 0.05
Nodes (13): join(), TecnoempleoExecutor, mock_env_vars(), mock_mysql(), mock_persistence_manager(), mock_selenium(), TestTecnoempleoExecutor, TestTecnoempleoService (+5 more)

### Community 64 - "WatcherRepository"
Cohesion: 0.24
Nodes (6): mock_db(), test_create_view_failure_is_logged(), test_get_watcher_stats_empty_ids(), test_get_watcher_stats_from_view(), test_parse_json_filters_returns_empty_on_invalid_json(), WatcherRepository

### Community 72 - "companyExtractor_test.py"
Cohesion: 0.13
Nodes (10): get_max_validation_retries(), build_company_prompt(), resolve_unspecified_company(), _ollama_reply(), _process_unspecified_job(), query_returning(), repo(), TestBuildCompanyPrompt (+2 more)

### Community 74 - "ai_helpers_test.py"
Cohesion: 0.13
Nodes (26): combineTaskResults(), _expand_parenthesized_skills(), flatten_skill_groups(), footer(), listsToString(), _normalizeModality(), validateResult(), completed() (+18 more)

### Community 75 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection, moduleResolution (+14 more)

### Community 77 - "FilterConfigSelector"
Cohesion: 0.13
Nodes (19): FilterConfigSelector, parse_job_order(), FakeLogger, FakeMysql, _match_queries(), test_configs_query_only_watched_ordered_by_ordering_asc(), test_iter_batches_follows_config_order_and_chunks(), test_iter_batches_maps_jobs_to_first_matching_config() (+11 more)

### Community 78 - "GlassdoorNavigator"
Cohesion: 0.09
Nodes (10): blue(), magenta(), printHR(), test_color_functions(), test_printHR_with_color(), test_printHR_without_color(), GlassdoorExecutor, TestGlassdoorExecutor (+2 more)

### Community 79 - "useSqlEditor.ts"
Cohesion: 0.14
Nodes (17): DdlSchemaResponse, fetchDdlSchema(), mockApiClient, useSqlEditor(), UseSqlEditorProps, SqlEditor(), SqlEditorProps, getCaretCoordinates() (+9 more)

### Community 84 - "filter_configurations_service_test.py"
Cohesion: 0.08
Nodes (13): mock_repo(), service(), test_create_duplicate_name(), test_create_success(), test_delete_not_found(), test_delete_success(), test_get_all_seeds_when_empty(), test_get_all_skips_seeding_when_not_empty() (+5 more)

### Community 85 - "datetime"
Cohesion: 0.28
Nodes (10): FilterConfiguration, FilterConfigurationCreate, FilterConfigurationUpdate, test_filter_configuration(), test_filter_configuration_create(), test_filter_configuration_create_pinned(), test_filter_configuration_create_watched(), test_filter_configuration_update_all_optional() (+2 more)

### Community 86 - "@tanstack/react-query"
Cohesion: 0.05
Nodes (44): HistoryInput(), HistoryInputProps, testQueryClient, testQueryClient, testQueryClient, JobListParams, byCompanyConfigs, TestConfig (+36 more)

### Community 87 - "yellow"
Cohesion: 0.06
Nodes (7): retry(), StackTrace, TestRetry, yellow(), InfojobsExecutor, TestInfojobsExecutor, InfojobsNavigator

### Community 88 - "rawToJson"
Cohesion: 0.09
Nodes (13): decode_unicode_escapes(), fixJsonEndCurlyBraces(), fixJsonInvalidAttribute(), fixJsonStartCurlyBraces(), LazyDecoder, printJsonException(), rawToJson(), TestDecodeUnicodeEscapes (+5 more)

### Community 89 - "mysql_discovery_test.py"
Cohesion: 0.14
Nodes (9): discover_mysql_hosts(), get_local_ip(), get_local_subnets(), _scan_hosts(), _scan_port(), TestGetLocalIp, TestGetLocalSubnets, TestScanHosts (+1 more)

### Community 90 - "AnswerResult"
Cohesion: 0.17
Nodes (6): AIProvider, AnswerResult, OpenRouterProvider, TestAIProvider, TestAnswerResult, TestOpenRouterProvider

### Community 95 - "SalaryCalculator"
Cohesion: 0.23
Nodes (10): SalaryCalculator, test_calculate_salary_hourly(), test_get_year_tax_equation(), test_get_year_tax_equation_zero(), test_salary_calculation_daily(), test_salary_calculations(), test_tax_bracket_all_brackets(), test_tax_bracket_below_first() (+2 more)

### Community 97 - "skills.py"
Cohesion: 0.15
Nodes (14): bulk_create_skills(), create_skill(), delete_skill(), get_skill(), list_skills(), update_skill(), SkillBase, SkillCreate (+6 more)

### Community 98 - "filter_configurations_repository_test.py"
Cohesion: 0.10
Nodes (3): mock_db(), repo_with_mock(), test_create()

### Community 101 - "scrapper_scheduler_test.py"
Cohesion: 0.20
Nodes (10): mock_selenium_service(), mocks(), run_mocks(), scheduler(), setup_scrappers(), test_get_properties(), test_preload_execution(), test_run_scenarios() (+2 more)

### Community 102 - "persistence_manager_test.py"
Cohesion: 0.11
Nodes (14): test_add_failed_keyword(), test_clear_state(), test_finalize_scrapper(), test_get_failed_keywords(), test_get_last_execution(), test_get_state(), test_is_state_stale(), test_load_fallback_on_repo_error() (+6 more)

### Community 103 - "seleniumService_test.py"
Cohesion: 0.09
Nodes (6): service(), TestConstruction, TestContextManager, TestDelegation, TestPresenceWaitNoError, TestSetFocus

### Community 105 - "LinkedinExecutor"
Cohesion: 0.07
Nodes (6): LinkedinExecutor, TestLinkedinExecutor, LinkedinDetailReader, LinkedinNavigator, mock_selenium(), navigator()

### Community 106 - "salary_calculator.spec.ts"
Cohesion: 0.16
Nodes (6): BASE_URL, test, SALARY_CALC_RESPONSE, MOCK_JOB_WITH_CALC_COMMENTS, PAGE_SIZE, PAGINATED_JOB_COUNT

### Community 107 - "devDependencies"
Cohesion: 0.09
Nodes (22): devDependencies, baseline-browser-mapping, coverage-badges-cli, eslint, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+14 more)

### Community 110 - "api/salary.py"
Cohesion: 0.28
Nodes (5): calculate_salary(), SalaryCalculationRequest, SalaryService, test_calculate_salary(), test_calculate_salary_params()

### Community 111 - "FilterConfigurationsService"
Cohesion: 0.22
Nodes (7): create_configuration(), delete_configuration(), get_all_configurations(), get_configuration(), get_service(), update_configuration(), FilterConfigurationsService

### Community 112 - "aiEnrich/test/dataExtractor_test.py"
Cohesion: 0.15
Nodes (9): dataExtractor(), clean_env(), mock_deps(), test_get_backend(), test_get_openrouter_base_url(), test_get_openrouter_fallback_model(), test_get_openrouter_model(), TestDataExtractor (+1 more)

### Community 115 - "StatisticsRepository"
Cohesion: 0.37
Nodes (5): StatisticsRepository, test_get_history_stats_df(), test_get_history_stats_df_with_dates(), test_get_sources_by_date_df(), test_get_sources_by_hour_df()

### Community 118 - "AI Job Enrichment"
Cohesion: 0.17
Nodes (12): 1. Install `uv` Package Manager, 2. Install Project Dependencies, AI Job Enrichment, Automated Loop, Configuration, Installation, Job selection, LLM Backend Selection (+4 more)

### Community 119 - "find_last_duplicated"
Cohesion: 0.14
Nodes (17): is_unspecified_company(), normalize_company_name(), find_last_duplicated(), test_collapses_spaces(), test_empty_name(), test_is_not_unspecified_company(), test_is_unspecified_company(), test_lowercases_and_trims() (+9 more)

### Community 120 - "AiEnrichRepository"
Cohesion: 0.06
Nodes (38): enrich_jobs(), _fetch_and_sort_jobs(), _process_job_batch_local(), retry_failed_job(), _save_job_result(), _update_error_state(), mock_pipeline(), mock_repo() (+30 more)

### Community 125 - "Job Scrappers"
Cohesion: 0.11
Nodes (19): Architecture, Configuration, Console Output & Structured Logging, Coverage, Dual Architecture (Selenium vs Scrapling), Dynamic Cadency (Time-based), Features, Gmail Configuration (+11 more)

### Community 126 - "aiEnrich/dataExtractor.py"
Cohesion: 0.15
Nodes (27): get_backend(), get_job_enabled(), get_max_ollama_failures(), get_model(), get_ollama_base_url(), get_openrouter_base_url(), get_openrouter_fallback_model(), get_openrouter_model() (+19 more)

### Community 128 - "enrichment_service_test.py"
Cohesion: 0.18
Nodes (23): _enrich_ollama(), timed_generate(), enrich_skills(), generate_skill_description_ollama(), assert_failure_metric(), capture_process_batch_callbacks(), side_effect(), make_ollama_mocks() (+15 more)

### Community 129 - "skills_test.py"
Cohesion: 0.43
Nodes (6): test_create_skill(), test_delete_skill(), test_delete_skill_not_found(), test_list_skills(), test_update_skill(), test_update_skill_not_found()

### Community 131 - "seleniumSocketConnRetry"
Cohesion: 0.19
Nodes (4): ElementService, seleniumSocketConnRetry(), _aria_checkbox(), TestCheckboxUnselect

### Community 133 - "Examples"
Cohesion: 0.10
Nodes (20): 1. Vanilla Playwright, 2. Real Chrome, 3. CDP Connection, Async Session Usage, Basic Usage, Browser Automation, Domain Blocking, Downloading Files (+12 more)

### Community 136 - "JobWriteRepository"
Cohesion: 0.29
Nodes (11): JobWriteRepository, _mock_db(), repo(), test_create_job(), test_update_job(), test_update_job_empty_data(), test_update_job_not_found(), test_update_jobs_by_filter() (+3 more)

### Community 137 - "viewer.helpers.ts"
Cohesion: 0.19
Nodes (17): searchJobs(), setupBulkJobsRoute(), setupDefaultJobsRoute(), setupJobUpdateRoute(), setupPaginatedJobsRoute(), setupStateChangeJobsRoute(), toggleFiltersIfNeeded(), waitForFilterConfigurations() (+9 more)

### Community 140 - "Statistics.tsx"
Cohesion: 0.10
Nodes (37): buildDateParams(), FilterConfigStat, getFilterConfigStats(), getHistoryStats(), getSourcesByDate(), getSourcesByHour(), getSourcesByWeekday(), HistoryStat (+29 more)

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
Cohesion: 0.18
Nodes (12): CompanySynonymRepository, test_add_to_group(), test_add_to_group_failure_is_logged(), test_create_group(), test_create_group_empty(), test_find_synonyms(), test_find_synonyms_not_found(), test_list_groups() (+4 more)

### Community 146 - "IndeedScraplingNavigator"
Cohesion: 0.12
Nodes (10): _extract_total_from_title(), IndeedScraplingNavigator, create_mock_scrapling_service(), _make_navigator(), MockSelector, _new_dom_page(), css(), TestIndeedScraplingNavigator (+2 more)

### Community 152 - "App.tsx"
Cohesion: 0.09
Nodes (26): App(), CompanySynonymsManager, Dashboard, Settings, SkillsManager, Statistics, Viewer, LoadingFallback() (+18 more)

### Community 153 - "get"
Cohesion: 0.11
Nodes (22): get_enum_values(), get_schema(), get_timezone(), health_check(), get_env_settings(), get_scrapper_state(), get_archived_history_stats(), get_archived_sources_by_date() (+14 more)

### Community 155 - "manifest.json"
Cohesion: 0.12
Nodes (15): background, service_worker, content_scripts, description, host_permissions, icons, 128, 16 (+7 more)

### Community 157 - "make_jsonl_writer"
Cohesion: 0.12
Nodes (12): append_jsonl(), make_jsonl_writer(), _writer(), public_record(), _events(), TestAppend, TestWriterFactory, Follow-ups (+4 more)

### Community 159 - "jobs_test.py"
Cohesion: 0.13
Nodes (18): get_watcher_service(), get_query_from_mock(), mock_job_dict(), request_jobs(), mock_db_session(), mock_jobs_service(), mock_watcher_service(), test_create_job_success() (+10 more)

### Community 161 - "connection_manager.py"
Cohesion: 0.11
Nodes (12): _init_pool(), _parse_host_targets(), _parse_ip_range(), _resolve_db_host(), mock_mysql_connect(), test_parse_host_targets(), test_parse_host_targets_cleanup(), test_parse_ip_range() (+4 more)

### Community 162 - "architecture_test.py"
Cohesion: 0.12
Nodes (23): check_layer(), get_file_imports(), _validate_dependencies(), get_console_violations(), get_print_violations(), _is_log_call(), getLongFiles(), get_test_naming_violations() (+15 more)

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
Nodes (33): AI daemons & fullstack app logs, AI Job Search Monorepo  [![master CI](https://img.shields.io/github/actions/workflow/status/davidgfolch/AI-job-search/ci.yml?branch=master&label=master%20CI)](https://github.com/davidgfolch/AI-job-search/actions/workflows/ci.yml?branch=master)  [![staging CI](https://img.shields.io/github/actions/workflow/status/davidgfolch/AI-job-search/ci.yml?branch=staging&label=staging%20CI)](https://github.com/davidgfolch/AI-job-search/actions/workflows/ci.yml?branch=staging), Build the graph, CI / GitHub Automation, Cross-module edges, Distributed execution, Docker Compose Profiles, Documentation (+25 more)

### Community 168 - ".layout_check.cjs"
Cohesion: 0.10
Nodes (20): api, distinctBands, extX, fn, fs, html, internal, intMaxX (+12 more)

### Community 169 - "get_logger"
Cohesion: 0.15
Nodes (6): get_logger(), green(), _events(), TestConsoleEnd, TestConsoleField, Phase 0 — Root causes in `commonlib/observability.py`

### Community 170 - "selenium/test/conftest.py"
Cohesion: 0.27
Nodes (6): action_chains(), driver(), make_element(), no_sleep(), service(), wait_mock()

### Community 172 - "Skill"
Cohesion: 0.24
Nodes (9): Skill, SkillsService, test_bulk_create_skills(), test_bulk_create_skills_logs_failures(), test_create_skill(), test_delete_skill(), test_list_skills(), test_normalize_skill_name() (+1 more)

### Community 173 - "ScrapperStateCalculator"
Cohesion: 0.08
Nodes (12): get_tz(), getDatetimeNow(), getDatetimeNowStr(), getSeconds(), getTimeUnits(), parseDatetime(), TestDatetimeStr, TestGetTz (+4 more)

### Community 174 - "aiEnrichRepository_test.py"
Cohesion: 0.10
Nodes (26): MockMysqlUtil, mockRepo(), test_config_for_job_exposes_priority_config(), test_count_pending_cv_match(), test_count_pending_enrichment(), test_get_enrichment_error_id_retry(), test_get_filter_batch_size(), test_get_job_to_enrich() (+18 more)

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
Cohesion: 0.19
Nodes (4): auto_discover_host(), TestAutoDiscoverHost, TestDiscoverMySQLHosts, TestScanPort

### Community 180 - "graphify-html-grouped.py"
Cohesion: 0.19
Nodes (10): Where customization actually lives, community_colors(), generate_html(), hsl_to_hex(), main(), module_order(), build_raw_vis(), js_safe() (+2 more)

### Community 182 - "JobTable.tsx"
Cohesion: 0.10
Nodes (22): calculateLapsedTime(), calculateLapsedTimeDetail(), getDayDiff(), getLapsed(), getLapsedParts(), getLapsedTime(), LapsedTime, JobList() (+14 more)

### Community 183 - "e2e/package.json"
Cohesion: 0.12
Nodes (16): devDependencies, coverage-badges-cli, monocart-coverage-reports, @playwright/test, @types/node, typescript, coverage-badges-cli, @types/node (+8 more)

### Community 184 - "view_generator.py"
Cohesion: 0.22
Nodes (8): test_drop_config_view_sql(), test_generate_config_view_sql(), test_generate_config_view_sql_with_all_filters(), test_generate_config_view_sql_with_duplicated(), test_generate_config_view_sql_with_flat_boolean_filters(), drop_config_view_sql(), generate_config_view_sql(), _get_view_name()

### Community 186 - "aiEnrich3/pipeline.py"
Cohesion: 0.08
Nodes (12): ExtractionResult, ModalityType, ModalityExtractor, SalaryExtractor, SkillsExtractor, extractor(), test_default_pipeline_is_pinned_to_cpu(), test_extract_modality() (+4 more)

### Community 187 - "AGENTS.md"
Cohesion: 0.09
Nodes (22): AGENTS.md, Architecture Patterns, Backend (FastAPI Layered), Build & Test Commands, Code Style Guidelines, Database Safety (ask before any write), Definition of Done, Development & Linting (+14 more)

### Community 190 - "console_render.py"
Cohesion: 0.14
Nodes (8): color_enabled(), console_mode(), _env(), render_console(), set_console_mode(), split_console_text(), TestConsoleModeResolution, Console fields

### Community 191 - "QuestionAnsweringService"
Cohesion: 0.20
Nodes (5): QuestionAnsweringService, TestQuestionAnsweringService, make_mock_cfg(), make_mock_provider(), TempFiles

### Community 193 - "company_synonyms.py"
Cohesion: 0.23
Nodes (11): add_to_group(), create_synonym_group(), get_synonyms(), list_synonym_groups(), remove_name(), SynonymAddRequest, SynonymGroup, SynonymGroupCreate (+3 more)

### Community 194 - "process_skill_enrichment"
Cohesion: 0.16
Nodes (14): log_no_pending_skills(), parse_skill_llm_output(), process_skill_enrichment(), test_parse_skill_llm_output(), test_process_skill_enrichment_check_empty_false(), test_process_skill_enrichment_description_with_error(), test_process_skill_enrichment_error_in_context(), test_process_skill_enrichment_error_in_generation() (+6 more)

### Community 195 - "create_mock_db"
Cohesion: 0.21
Nodes (13): test_add_to_group(), test_create_group(), test_create_group_invalid(), test_get_synonyms(), test_get_synonyms_not_found(), test_list_synonym_groups(), test_list_synonym_groups_empty(), test_remove_name() (+5 more)

### Community 196 - "CombinedStatsRepository"
Cohesion: 0.29
Nodes (6): CombinedStatsRepository, test_get_combined_history_stats_df(), test_get_combined_history_stats_df_with_dates(), test_get_combined_sources_by_date_df_with_dates(), test_get_combined_sources_by_hour_df_with_dates(), test_get_combined_sources_by_weekday_df_with_dates()

### Community 197 - "jobs_service.py"
Cohesion: 0.08
Nodes (5): build_where_params(), extract_boolean_filters(), extract_filter_params(), TestExtractBooleanFilters, TestExtractFilterParams

### Community 198 - "keep_system_awake.py"
Cohesion: 0.18
Nodes (9): _clear_power_request(), _close_handle(), DetailedStructure, KeepSystemAwake, REASON_CONTEXT, ReasonUnion, _try_power_request(), _use_legacy_api() (+1 more)

### Community 202 - "AI Job Search — Metrics & Observability"
Cohesion: 0.12
Nodes (17): Accessing the Dashboard, Adding a New Enrichment Module, AI Job Search — Metrics & Observability, Architecture, Business Overview, Dashboard, Data Flow, Docker Volume Mounts for Logs (+9 more)

### Community 203 - "settings_service.py"
Cohesion: 0.23
Nodes (12): get_env_settings(), get_scrapper_state(), update_env_setting(), update_env_settings_bulk(), update_scrapper_state(), test_get_env_settings(), test_get_scrapper_state_returns_empty_on_error(), test_get_scrapper_state_returns_state() (+4 more)

### Community 204 - "Querying elements"
Cohesion: 0.15
Nodes (13): Advanced examples, CSS/XPath selectors, Examples, Examples, Filters-based searching, Finding Similar Elements, Generating selectors, Querying elements (+5 more)

### Community 205 - "FastCVMatcher"
Cohesion: 0.17
Nodes (18): FastCVMatcher, mock_all(), patched_matcher(), reset_shared_state(), test_disabled(), test_footer_logs_summary(), test_init(), test_job_none() (+10 more)

### Community 206 - "WatcherService"
Cohesion: 0.20
Nodes (8): get_watcher_stats(), mock_repo(), test_get_watcher_stats(), test_get_watcher_stats_error_handling(), test_get_watcher_stats_naive_local_input(), test_get_watcher_stats_string_dates(), test_get_watcher_stats_timezone_mismatch(), WatcherService

### Community 207 - "AI Job Search API"
Cohesion: 0.12
Nodes (16): AI Job Search API, API Documentation, API Endpoints, Company Synonyms, Database, Features, How it affects the applied-by-company search, Installation (+8 more)

### Community 208 - "JobDeleteRepository"
Cohesion: 0.20
Nodes (11): JobDeleteRepository, mock_mysql(), test_delete_jobs_by_filter(), test_delete_jobs_by_ids(), test_delete_jobs_by_ids_empty(), test_delete_jobs_with_snapshots(), test_get_jobs_by_filter(), test_update_jobs_by_filter() (+3 more)

### Community 209 - "SkillsRepository"
Cohesion: 0.27
Nodes (14): SkillsRepository, test_create_skill(), test_delete_skill(), test_find_by_name_case_insensitive_found(), test_find_by_name_case_insensitive_invalid_json(), test_find_by_name_case_insensitive_not_found(), test_list_skills(), test_list_skills_invalid_json() (+6 more)

### Community 210 - "extraction_contract_test.py"
Cohesion: 0.16
Nodes (16): ExtractionValidationError, parse_company_result(), parse_extraction_result(), query_and_parse(), query_company(), _query_retry(), _strip_code_fence(), validate_extraction_result() (+8 more)

### Community 211 - "exceptionUtil_test.py"
Cohesion: 0.18
Nodes (14): filter_trace_by_paths(), getProjectTraceItems(), try_or_warn(), fail_fn(), ok_fn(), test_cleanUnresolvedTrace(), test_filter_trace_by_paths_apps_only(), test_filter_trace_by_paths_filters_out_non_matching() (+6 more)

### Community 212 - "MongoDbProvider"
Cohesion: 0.23
Nodes (7): get_mongo_provider(), MongoDbProvider, test_get_database_returns_database(), test_get_database_write_returns_writer(), test_get_mongo_provider_caches(), test_get_mongo_provider_different_keys(), test_provider_creates_read_and_write_clients()

### Community 213 - "commonlib_sql_mysqlutil"
Cohesion: 0.09
Nodes (9): htmlToMarkdown(), BaseService, mock_mysql(), mock_persistence_manager(), service(), assert_console_text(), assert_logged(), logged_calls() (+1 more)

### Community 214 - "JobSnapshotService"
Cohesion: 0.10
Nodes (4): JobSnapshotService, mock_repo(), service(), test_maybe_create_snapshot_on_update()

### Community 215 - "dependencies"
Cohesion: 0.20
Nodes (10): dependencies, axios, prismjs, react, react-dom, react-markdown, react-router-dom, react-simple-code-editor (+2 more)

### Community 216 - "os"
Cohesion: 0.21
Nodes (5): createFolder(), getSrcPath(), listFiles(), TestFileSystemUtil, main()

### Community 217 - "panel.js"
Cohesion: 0.16
Nodes (14): answerAll(), answerAllBtn, container, detectAllFields(), errorSection, errorText, fields, fillAllBtn (+6 more)

### Community 218 - "AI Form Filler"
Cohesion: 0.13
Nodes (15): 1. Prepare context documents, 2. Start the backend, 3. Install the browser extension, AI Form Filler, AI Providers, API Endpoints, Architecture, Development (+7 more)

### Community 219 - "cron/test/main_test.py"
Cohesion: 0.22
Nodes (12): run(), _events(), log_dir(), _raw_log(), _run_one_tick(), _StopLoop, test_run_configures_logging_before_connecting_to_mongo(), test_run_emits_lifecycle_events_in_order() (+4 more)

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
Nodes (20): 1. Install Python 3.11, 2. Install Poetry (Python), 3. Install uv (Python), 4. Install Node.js & npm, 5. Install GitHub CLI (recommended), 6.1 ISP blocking the Ollama registry (e.g. Movistar), 6. Install Ollama & required models, 7.1 Install Google Chrome & system libraries (scrapper) (+12 more)

### Community 225 - "configurations.spec.ts"
Cohesion: 0.33
Nodes (3): JobListRequests, openConfigDropdown(), clickConfig()

### Community 226 - "README.md"
Cohesion: 0.19
Nodes (6): AI CV Matcher, Quickstart, Requirements, aiEnrich3, Job selection, Setup

### Community 227 - "configure_logging"
Cohesion: 0.17
Nodes (10): configure_logging(), _env(), get_app_name(), log_file_path(), _stamp_app_name(), _read(), TestAppNameResolution, TestJsonlRecords (+2 more)

### Community 228 - "SnapshotsRepository"
Cohesion: 0.21
Nodes (12): SnapshotsRepository, mock_connection(), test_get_history_stats_df(), test_get_history_stats_df_with_dates(), test_get_snapshot_count_by_platform(), test_get_snapshot_count_by_reason(), test_get_sources_by_date_df(), test_get_sources_by_date_df_with_dates() (+4 more)

### Community 229 - "statistics_service_test.py"
Cohesion: 0.14
Nodes (9): StatisticsService, mock_filter_repo(), mock_jobs_repo(), mock_repo(), service(), test_get_history_stats(), test_get_history_stats_with_dates(), test_get_sources_by_date() (+1 more)

### Community 230 - "CronStateRepository"
Cohesion: 0.25
Nodes (7): CronStateRepository, CompanySalaryHistoryJob, test_job_has_name_and_cadency(), test_job_run_no_prior_state(), test_job_run_with_prior_state(), CronJob, test_cron_job_base_run_raises()

### Community 231 - "CompanySalaryHistoryScanner"
Cohesion: 0.36
Nodes (9): CompanySalaryHistoryScanner, test_scanner_backfill_new_jobs(), test_scanner_imports(), test_scanner_incremental_new_jobs(), test_scanner_last_run_at_no_updates(), test_scanner_no_new_jobs(), test_scanner_updated_jobs_no_prior_record(), test_scanner_updated_jobs_salary_changed() (+1 more)

### Community 233 - "Phases"
Cohesion: 0.40
Nodes (5): Phase 2 — cron (4 files, 16 prints), Phase 4 — backend (9 prints + 9 swallowed exceptions), Phase 6 — Infrastructure, Phase 8 — Tests and docs, Phases

### Community 234 - "Plan F: Combined / Recommended Approach"
Cohesion: 0.13
Nodes (14): Architecture, Comparison Script, Configuration, Goal, Gradual Rollout, Implementation Phases, Per-Phase Validation, Performance Budget (+6 more)

### Community 235 - "dashboard_repository_test.py"
Cohesion: 0.20
Nodes (14): DashboardRepository, resolve_log_path(), test_check_ollama_errors(), test_check_ollama_errors_no_matches(), test_check_ollama_errors_recency(), test_log_source_is_logged_as_source_module(), test_read_last_activity(), test_read_recent_errors() (+6 more)

### Community 236 - "jobs_service_test.py"
Cohesion: 0.11
Nodes (4): mock_db(), service(), test_bulk_update_jobs(), test_update_job_creates_snapshot()

### Community 237 - "backendDiscovery.ts"
Cohesion: 0.20
Nodes (9): cidrToHosts(), detectLocalSubnets(), discoverBackendUrl(), probeBackend(), scanPort(), createMockSocket(), socketFactory(), vite (+1 more)

### Community 238 - "CompanySynonymService"
Cohesion: 0.15
Nodes (5): JobQueryRepository, test_find_applied_by_company(), CompanySynonymService, JobQueryService, scapeRegexChars()

### Community 239 - "jobs_applied_test.py"
Cohesion: 0.21
Nodes (8): test_get_applied_jobs_by_company(), test_get_applied_jobs_by_company_empty_string(), test_get_applied_jobs_by_company_missing_parameter(), test_get_applied_jobs_by_company_special_characters(), test_get_applied_jobs_partial_search_exception(), test_get_applied_jobs_partial_search_exclusions(), test_get_applied_jobs_sql_injection(), test_get_applied_jobs_with_synonym_expansion()

### Community 240 - "PageHeader"
Cohesion: 0.09
Nodes (21): API_BASE_URL, apiClient, Dropdown(), DropdownProps, HeaderMenu(), PageHeader(), PageHeaderProps, companySynonymsApi (+13 more)

### Community 241 - "JobsRepository"
Cohesion: 0.09
Nodes (8): get_job(), _execute_with_error_handler(), JobsRepository, mock_db(), repo(), test_fetch_job_row_and_columns(), test_update_job_empty_data(), test_update_job_found()

### Community 242 - "systemUtil.py"
Cohesion: 0.29
Nodes (5): isDocker(), isLinuxOS(), isMacOS(), isWindowsOS(), TestSystemUtil

### Community 245 - "JobSnapshotRepository"
Cohesion: 0.09
Nodes (7): JobSnapshotRepository, mock_mysql(), repo(), test_build_snapshot_query_and_params(), test_build_snapshot_query_empty_job(), test_default_mysql_creates_instance(), test_save_snapshot()

### Community 247 - "Plan D: GGUF Quantized Models via llama-cpp-python"
Cohesion: 0.14
Nodes (13): `apps/aiEnrichNew/pyproject.toml`, `apps/aiEnrichNew/src/aiEnrichNew/llm_client.py`, `apps/aiEnrichNew/src/aiEnrichNew/llm_utils.py`, Architecture, Files to Modify, Goal, Implementation Order, Installation (+5 more)

### Community 248 - "aiEnrichSkill"
Cohesion: 0.18
Nodes (11): aiEnrichSkill, Backends, Configuration, Dependencies, General, HuggingFace Backend, Linux / Mac, Manual (+3 more)

### Community 249 - "useAutoLoadMore.fixtures.tsx"
Cohesion: 0.09
Nodes (37): AI Job Search Web UI, Backend Discovery, Coverage, Environment Variables (`.env` & `.env.secrets`), Features, Infinite Scroll Pagination, Installation, Keeping the Selected Job Visible (+29 more)

### Community 251 - "validationUtils.ts"
Cohesion: 0.31
Nodes (6): getFilesRecursively(), getTestFiles(), extractImports(), ImportViolation, checkImportViolation(), validateFeatureFolder()

### Community 252 - "Auto-merge (staging gate)"
Cohesion: 0.13
Nodes (15): Adding a new app, Auto-merge (staging gate), Behavior, Change detection rules, CI / GitHub Actions Pipeline, Coverage gates, Dependabot, Ecosystems & cadency (+7 more)

### Community 253 - "build_jobs_where_clause"
Cohesion: 0.09
Nodes (24): test_build_jobs_where_clause_boolean_filters(), test_build_jobs_where_clause_created_after(), test_build_jobs_where_clause_modality(), test_build_jobs_where_clause_search(), test_build_jobs_where_clause_status(), test_parse_job_order(), _get_where(), _get_where_status() (+16 more)

### Community 255 - "TestLinkedinService"
Cohesion: 0.09
Nodes (6): mock_mysql(), mock_pm(), mock_selenium(), mocks(), LinkedinService, TestLinkedinService

### Community 257 - "StatisticsArchivedService"
Cohesion: 0.16
Nodes (4): app(), mock_service(), test_archived_endpoints(), StatisticsArchivedService

### Community 258 - "service_mock"
Cohesion: 0.26
Nodes (3): service_mock(), TestKeyboardInterrupt, TestKeywordLoop

### Community 260 - "Common Library"
Cohesion: 0.25
Nodes (7): Common Library, Installation, MySQL connection, Resolution order, Supported host formats, Testing, Usage

### Community 263 - "DdlRepository"
Cohesion: 0.17
Nodes (10): test_get_schema(), DdlRepository, test_get_enum_values(), test_get_enum_values_not_enum(), test_get_enum_values_not_found(), test_get_keywords(), test_get_schema(), DdlService (+2 more)

### Community 264 - "TODO"
Cohesion: 0.17
Nodes (11): apps/aiEnrich, apps/aiEnrich3, apps/aiEnrichNew, apps/backend, apps/commonlib, apps/scrapper, apps/web, cross module tasks (+3 more)

### Community 266 - "Workflow"
Cohesion: 0.14
Nodes (13): 1. List open Dependabot PRs, 2. Process each PR (smallest PR number first), 3. Changelog / breaking-change gate, 4. Run the TDD pipeline for the module, 5. Sandbox build+run the affected docker-compose services and check logs — MANDATORY GATE, 6. Green result, 7. Red result, 8. Wrap-up (+5 more)

### Community 268 - "job_delete_service_test.py"
Cohesion: 0.12
Nodes (8): JobDeleteService, mock_get_job(), mock_repo(), service(), service_with_callback(), test_build_snapshot_queries(), test_delete_by_ids_with_callback(), test_update_jobs_by_ids()

### Community 269 - "dashboard_service.py"
Cohesion: 0.17
Nodes (18): get_services_status(), _determine_status(), _display_name(), get_services_status(), _local(), _parse_local(), _pick_freshest(), _iso() (+10 more)

### Community 270 - "Company Salary History Scanner"
Cohesion: 0.17
Nodes (10): 1. New job backfill (`_fetch_jobs`), 2. Updated job detection (`_fetch_updated`), Company name matching, Company Salary History Scanner, Configuration, Data model, Duplicate prevention, How it works (+2 more)

### Community 271 - "IndeedNavigator"
Cohesion: 0.11
Nodes (3): IndeedExecutor, TestIndeedExecutor, IndeedNavigator

### Community 272 - "ScrapperStateRepository"
Cohesion: 0.24
Nodes (3): ScrapperStateRepository, mock_db(), repo_with_mock()

### Community 273 - "mysql_sync.py"
Cohesion: 0.07
Nodes (23): build_dump_cmd(), build_restore_cmd(), confirm(), dump_local(), dump_tables(), main(), make_dump_path(), preflight_target() (+15 more)

### Community 274 - "frontend-coverage-gate.mjs"
Cohesion: 0.13
Nodes (13): byKey(), drift, e2e, files, GATED, keyOf(), METRICS, MIN (+5 more)

### Community 275 - "process_batch"
Cohesion: 0.22
Nodes (8): get_gpu_cleanup(), process_batch(), test_get_gpu_cleanup_default_true(), test_cleanup_gpu(), test_process_batch_empty(), test_process_batch_inference_error(), test_process_batch_success(), test_process_batch_tokenizer_error()

### Community 276 - "commonlib"
Cohesion: 0.18
Nodes (11): ai-job-search, aiCvMatcher, aiEnrich, aiEnrich3, aiEnrichNew, aiEnrichSkill, aiFormFiller, api (+3 more)

### Community 280 - "Version Bumper Instructions"
Cohesion: 0.17
Nodes (11): 1. Detect Modified Apps, 2. Ask User for Bump Type, 3. Update the Version File, 4. Sync commonlib Dependency Version, 5. Version Reference Table, 6. Verify, aiFormFiller extension (extension/manifest.json):, npm apps (web, e2e — package.json): (+3 more)

### Community 281 - "logIdleWait"
Cohesion: 0.06
Nodes (32): Configuration, Structured logging, Logs, Logs, Logs, Architecture, Configuration, Structured logging (+24 more)

### Community 282 - "scrapper_scheduler.py"
Cohesion: 0.06
Nodes (28): get_debug(), ScrapperScheduler, mocks(), create_executor(), process_page_url(), _get_executor_names(), test_create_executor(), test_create_executor_invalid() (+20 more)

### Community 283 - "InfojobsExecutor_test.py"
Cohesion: 0.07
Nodes (10): mock_env_vars(), mock_mysql(), mock_persistence_manager(), mock_selenium(), silence_console(), TestInfojobsService, TestLoadRow, TestProcessAndLoadRow (+2 more)

### Community 285 - "react"
Cohesion: 0.06
Nodes (37): ConfirmModal(), ConfirmModalProps, FormField(), FormFieldProps, Modal(), ModalProps, useAutoResizeTextArea(), EditSynonymGroupModal() (+29 more)

### Community 286 - "observability.py"
Cohesion: 0.09
Nodes (9): get_input_max_len(), build_job_prompt_messages(), map_db_job_to_domain(), test_build_job_prompt_messages(), test_map_db_job_to_domain(), mapJob(), error(), getColumnTranslated() (+1 more)

### Community 288 - "Quick Start Commands for Docker Development"
Cohesion: 0.20
Nodes (10): All Services, Core Services (Backend + Web + Viewer), Development Tips, Quick Start Commands for Docker Development, Related Documentation, Scrapper (runs on the host, not in Docker), Service URLs, Troubleshooting (+2 more)

### Community 296 - "Cron — Background Scheduler"
Cohesion: 0.20
Nodes (9): Configuration, Cron — Background Scheduler, Docker, How it works, Registered jobs, Running, Structured logging, Tech Stack (+1 more)

### Community 297 - "Undetected ChromeDriver Usage"
Cohesion: 0.22
Nodes (8): Benefits, Configuration, How It Works, Option 1: Environment Variable (Recommended), Option 2: Programmatic, Overview, Troubleshooting, Undetected ChromeDriver Usage

### Community 299 - "filter_configurations_test.py"
Cohesion: 0.33
Nodes (9): test_create_configuration(), test_create_duplicate_name(), test_delete_configuration(), test_delete_missing_configuration_logs_rejection(), test_get_all_configurations(), test_get_configuration_by_id(), test_get_missing_configuration_logs_rejection(), test_update_configuration() (+1 more)

### Community 302 - "vitest"
Cohesion: 0.05
Nodes (42): downloadFile(), Skill, skillsApi, mocks, mocks, mocks, mocks, mocks (+34 more)

### Community 303 - "Settings.tsx"
Cohesion: 0.10
Nodes (31): MessageContainer(), MessageContainerProps, Messages(), MessagesProps, useDefaultComment(), useEnvSettings(), ScrapperStateUpdateDto, settingsApi (+23 more)

### Community 306 - "json"
Cohesion: 0.09
Nodes (16): find_violation(), main(), is_up_command(), main(), filter_deps(), is_external_dep(), main(), _belongs_to_module() (+8 more)

### Community 308 - "configurations.helpers.ts"
Cohesion: 0.21
Nodes (16): setupApiSafetyNet(), setupAppBootstrapMocks(), setupModalityMock(), setupSalaryHistoryMocks(), setupTimezoneMock(), setupSynonymsMocks(), MOCK_FILTER_CONFIGS, setupConfigurationsJobsRoute() (+8 more)

### Community 309 - "post"
Cohesion: 0.30
Nodes (10): update_env_setting(), update_env_settings_bulk(), update_scrapper_state(), ScrapperStateUpdateDto, SettingsEnvBulkUpdateDto, SettingsEnvUpdateDto, test_scrapper_state_update_dto(), test_settings_env_bulk_update_dto() (+2 more)

### Community 310 - "cyan"
Cohesion: 0.18
Nodes (10): run(), app_events(), enabled(), test_run_configures_logging_before_first_event(), test_run_logs_disabled_and_exits(), test_run_polls_and_logs_the_idle_wait(), run_pipeline(), assert_any_idle() (+2 more)

### Community 311 - "getEnv"
Cohesion: 0.16
Nodes (19): get_cv_path(), get_hf_model(), get_looking_for_path(), get_max_tokens(), get_openai_api_key(), get_openai_model(), get_openrouter_api_key(), get_openrouter_model() (+11 more)

### Community 313 - "ollama_client.py"
Cohesion: 0.11
Nodes (21): _probe_ollama(), _candidate_urls(), get_num_ctx(), get_num_predict(), get_repeat_penalty(), ollama_candidate_urls(), ollama_probe_urls(), strip_provider_prefix() (+13 more)

### Community 314 - "StealthyFetcher"
Cohesion: 0.10
Nodes (19): Fetchers basics, Fetchers Overview, Introduction, Parser configuration in all fetchers, Response Object, Set parser config per request, Async Session Usage, Basic Usage (+11 more)

### Community 316 - "Plan B: RAG Cache Layer (Skip LLM Inference for Similar Jobs)"
Cohesion: 0.12
Nodes (16): `apps/aiEnrich/pyproject.toml`, `apps/aiEnrich/src/aiEnrich/crew.py`, `apps/aiEnrich/src/aiEnrich/dataExtractor.py`, `apps/aiEnrich/src/aiEnrich/embedding_service.py`, `apps/aiEnrich/src/aiEnrich/rag_cache.py`, Architecture, Dependencies, Files to Create (+8 more)

### Community 317 - "baseScrapper.py"
Cohesion: 0.09
Nodes (12): cleanUnresolvedTrace(), getAndCheckEnvVars(), TestAbortExecution, TestDebug, TestPageExists, TestRunPreload, abortExecution(), debug() (+4 more)

### Community 318 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, dev, lint, preview, test

### Community 319 - "pandas"
Cohesion: 0.17
Nodes (16): mock_combined_repo(), mock_snapshots_repo(), mock_stats_repo(), service(), test_get_archived_history_stats(), test_get_archived_history_stats_empty(), test_get_archived_sources_by_date(), test_get_archived_sources_by_hour() (+8 more)

### Community 322 - "JobsService"
Cohesion: 0.12
Nodes (25): get_applied_jobs_by_company(), get_service(), bulk_delete_jobs(), bulk_update_jobs(), BulkJobDelete, BulkJobUpdate, create_job(), get_service() (+17 more)

### Community 323 - "web/package.json"
Cohesion: 0.09
Nodes (23): coverage-badges-cli, @types/node, typescript, name, private, type, version, queryClient (+15 more)

### Community 324 - "E2E Implementer Instructions"
Cohesion: 0.29
Nodes (6): 1. Location & Structure, 2. Naming Conventions, 3. Best Practices, 4. Architecture Verification, E2E Implementer Instructions, Usage

### Community 325 - "Adaptive scraping"
Cohesion: 0.08
Nodes (23): Adaptive scraping, How the adaptive scraping feature works, How to use adaptive feature, Known Issues, No Matches Found, Real-World Scenario, The CSS/XPath Selection way, The manual way (+15 more)

### Community 326 - "Proxy management and handling Blocks"
Cohesion: 0.20
Nodes (9): Blocked Request Handling, Custom Block Detection, Custom Rotation Strategies, Customizing Retries, Per-Request Proxy Override, Proxy management and handling Blocks, ProxyRotator, Random Rotation (+1 more)

### Community 328 - "AI Job Search Default Development Guide"
Cohesion: 0.20
Nodes (10): Agentic SDLC, AI Job Search Default Development Guide, Coverage Gates, Development with VS Code, Documentation Sync, Frontend: web unit + e2e union, Related Documentation, Scrapper: production statements (+2 more)

### Community 329 - "Components"
Cohesion: 0.05
Nodes (29): QuotesSpider, Checkpoint System, Comparison with Scrapy, Components, Crawler Engine, Data Flow, Output, Scheduler (+21 more)

### Community 331 - "TestTecnoempleoSalaryReader"
Cohesion: 0.17
Nodes (3): TestTecnoempleoSalaryReader, Scrapling Implementer Instructions, Usage

### Community 334 - "Plan A: Direct Ollama API (Remove CrewAI)"
Cohesion: 0.14
Nodes (13): `apps/aiEnrich/pyproject.toml`, `apps/aiEnrich/src/aiEnrich/crew.py`, `apps/aiEnrich/src/aiEnrich/ollama_client.py`, Architecture, Dependencies, Files to Create, Files to Modify, Goal (+5 more)

### Community 337 - "AI Enrichment — Speed Improvement Plans"
Cohesion: 0.33
Nodes (5): AI Enrichment — Speed Improvement Plans, Context, Modules Overview, Plans Index, Recommended Order

### Community 339 - "console_render_test.py"
Cohesion: 0.13
Nodes (5): stripAnsi(), console(), TestColumnOrder, TestFileOnlyRecords, TestMessageColumn

### Community 340 - "Examples"
Cohesion: 0.10
Nodes (19): Basic HTTP Request, Basic Usage, DELETE, Downloading Files, Examples, Form Submission, GET, HTTP Methods (+11 more)

### Community 342 - "content.js"
Cohesion: 0.60
Nodes (3): cssSelector(), detectAllQuestions(), detectQuestion()

### Community 344 - "watcher_refresh.spec.ts"
Cohesion: 0.27
Nodes (7): setupPageLogging(), createJobsListRoute(), markJobAsApplied(), setupFilterConfigurationMock(), setupJobsMocks(), setupWatcherStatsMock(), verifyNoRefresh()

### Community 346 - "SalaryHistoryService"
Cohesion: 0.29
Nodes (6): get_company_history(), get_job_history(), get_service(), test_get_service_returns_service(), SalaryHistoryService, test_service_imports()

### Community 347 - "run"
Cohesion: 0.19
Nodes (10): get_max_ollama_failures(), run(), test_run_disabled(), test_run_enriched_some_skills(), test_run_no_skills_waits(), test_run_persists_after_each_enrich_cycle(), test_run_unreachable_backend_waits_before_enriching(), resolve_ollama_url() (+2 more)

### Community 350 - "Agentic SDLC"
Cohesion: 0.10
Nodes (19): graphify, Always invoke through the repo scripts, graphify development, Hard rule: `graphify-out/graph.html` is repo-owned, Hard rule: never edit the uv-installed graphify package, How to change or improve graphify, Verify the install is pristine, When NOT to use this skill (+11 more)

### Community 354 - "opencode.json"
Cohesion: 0.22
Nodes (8): formatter, ruff, uv, instructions, plugin, disabled, $schema, disabled

### Community 356 - "sqlUtil_test.py"
Cohesion: 0.09
Nodes (14): OpenRouter backend (cloud), avoidInjection(), binaryColumnIgnoreCase(), deleteJobsQuery(), emptyToNone(), formatSql(), getAndFilter(), inFilter() (+6 more)

### Community 357 - "log_writer_test.py"
Cohesion: 0.13
Nodes (13): _env(), file_backup_count(), file_max_bytes(), get_log_dir(), resolve_read_path(), rotate_if_needed(), log_dir(), _seed() (+5 more)

### Community 359 - "graphify.sh"
Cohesion: 0.83
Nodes (3): clean_graph(), extract_module(), graphify.sh script

### Community 361 - "Scrapling Examples"
Cohesion: 0.33
Nodes (5): Escalation Guide, Examples, Quick Start, Running, Scrapling Examples

### Community 362 - "SalaryHistoryRepository"
Cohesion: 0.15
Nodes (5): get_best_candidate(), search_partial_company(), SalaryHistoryRepository, TestGetBestCandidate, TestSearchPartialCompany

### Community 364 - "coverage.fixtures.ts"
Cohesion: 0.36
Nodes (5): coverageOptions, isProductionFile(), isSourceFile(), WEB_SRC_DIR, monocart-coverage-reports

### Community 365 - "docker-build.md"
Cohesion: 0.40
Nodes (4): Dependency-refresh caveats, Docker container bring-up: always `--build`, Layer caching, When rebuilding is required (why)

### Community 373 - "test-sandbox.sh"
Cohesion: 0.60
Nodes (3): env_file(), module_disabled(), test-sandbox.sh script

### Community 376 - "test.sh"
Cohesion: 0.83
Nodes (3): run_e2e_gate(), run_test(), test.sh script

### Community 379 - "query_ollama"
Cohesion: 0.12
Nodes (12): TestProcessJobSafeBackend, OllamaResponse, ping_ollama(), query_ollama(), _query_url(), clean_fallback_urls(), _down(), no_retry_sleep() (+4 more)

### Community 388 - "execute_with_error_handler"
Cohesion: 0.27
Nodes (6): execute_with_error_handler(), test_database_error_is_logged_without_bind_values(), test_database_error_with_items_returns_error_payload(), test_execute_with_error_handler_success(), callback(), test_execute_with_error_handler_with_items()

### Community 392 - "docker-build.js"
Cohesion: 0.67
Nodes (3): DockerBuildPlugin(), injectBuild(), OTHER_SUBCOMMANDS

### Community 396 - "backend/conftest.py"
Cohesion: 0.24
Nodes (5): client(), log_records(), read(), _read_jsonl(), Testing log output

### Community 397 - "statistics_test.py"
Cohesion: 0.48
Nodes (5): test_get_filter_config_stats(), test_get_history_stats(), test_get_history_stats_exclude_old_jobs(), test_get_sources_by_date(), test_get_sources_by_hour()

### Community 398 - "aiEnrich/test/config_test.py"
Cohesion: 0.17
Nodes (7): get_job_enabled(), run(), clean_env(), test_get_job_enabled(), test_get_ollama_base_url(), test_get_timeout_job(), TestMain

### Community 399 - "BrowserService"
Cohesion: 0.05
Nodes (17): BrowserService, browser_service(), _events(), mock_driver(), TestBack, TestBrowserServiceInit, TestGetTitle, TestGetUrl (+9 more)

### Community 400 - ".fetch"
Cohesion: 0.15
Nodes (11): `bulk_fetch` -- Browser fetch (multiple URLs), `bulk_get` -- HTTP request (multiple URLs), `bulk_stealthy_fetch` -- Stealth browser fetch (multiple URLs), Content extraction tips, `fetch` -- Browser fetch (single URL), `get` -- HTTP request (single URL), Scrapling MCP Server, Setup (+3 more)

### Community 401 - "get_pipeline"
Cohesion: 0.44
Nodes (5): get_pipeline(), test_get_pipeline_cuda_available(), test_get_pipeline_initialization(), test_get_pipeline_pad_token_set(), test_get_pipeline_singleton()

### Community 402 - "verify_mysql"
Cohesion: 0.24
Nodes (4): verify_mysql(), TestVerifyMySQL, _probe_mysql(), _try_targets()

### Community 404 - "Contribute"
Cohesion: 0.50
Nodes (4): Contribute, Development guide-lines, Related Documentation, Tests & coverage

### Community 405 - "docs-sync.js"
Cohesion: 0.29
Nodes (6): DOC_SUFFIXES, DocsSyncPlugin(), EDIT_TOOLS, IGNORED_FILES, IGNORED_PREFIXES, needsReminder()

### Community 408 - "Test Implementer Instructions"
Cohesion: 0.25
Nodes (7): 1. Test Location & Structure, 2. Naming Conventions, 3. Coding Best Practices, 4. Running Tests, 5. Architecture Verification, Test Implementer Instructions, Usage

### Community 409 - "aiEnrichNew"
Cohesion: 0.25
Nodes (8): aiEnrichNew, Configuration, Job selection, Linux / Mac, Manual, Prerequisites, Usage, Windows

### Community 410 - "terminalUtil.py"
Cohesion: 0.19
Nodes (6): consoleTimer(), consoleTimerDocker(), _consoleTimerLocal(), Spinner, TestSpinner, TestTerminalFunctions

### Community 411 - "install.sh"
Cohesion: 0.60
Nodes (5): ollama_hf_spec(), ollama_pull(), ollama_registry_reachable(), ollama_runner(), install.sh script

### Community 526 - "BaseExecutor_test.py"
Cohesion: 0.22
Nodes (4): MockBaseExecutor, mocks(), run_mocks(), TestExecutor

### Community 540 - "LocalHFProvider"
Cohesion: 0.24
Nodes (4): get_pipeline(), LocalHFProvider, TestGetPipeline, TestLocalHFProvider

### Community 564 - "Documentation Sync (mandatory, automatic)"
Cohesion: 0.33
Nodes (5): Definition-of-done checklist (before reporting done), Doc map: which docs to update for which change, Documentation Sync (mandatory, automatic), Rules, When it applies

### Community 565 - "request_logging_test.py"
Cohesion: 0.06
Nodes (38): RequestLoggingMiddleware, _asgi_app(), app(), _call(), receive(), send(), _client_app(), stream() (+30 more)

### Community 581 - "docs-sync.py"
Cohesion: 0.43
Nodes (4): already_reminded(), main(), needs_reminder(), remind_path()

### Community 698 - "JobDetail.tsx"
Cohesion: 0.10
Nodes (28): createHeadingRenderer(), getText(), ReactMarkdownCustom(), ReactMarkdownCustomProps, slugify(), { mockPost }, AppliedCompanyJob, salaryApi (+20 more)

### Community 701 - "Database changes require explicit user permission"
Cohesion: 0.29
Nodes (6): Allowed without permission, Ask like this, Blocked without permission, Database changes require explicit user permission, Enforcement, How to run an approved mutation

### Community 702 - "1. PYTHON MODULES (Backend & Commonlib)"
Cohesion: 0.29
Nodes (7): 1.1 Critical: Files Exceeding 200-Line Limit (Architecture Rule #1), 1.2 Module Consolidation: AI Enrich Variants, 1.3 Commonlib Coupling Issues, 1.4 Layer Architecture Violations, 1.5 Service Layer Analysis, 1.6 Test Architecture, 1. PYTHON MODULES (Backend & Commonlib)

### Community 703 - "ddl.sql"
Cohesion: 0.29
Nodes (6): `company_synonyms`, `filter_configurations`, `job_skills`, `job_snapshots`, `jobs`, `scrapper_state`

### Community 705 - "Debug GitHub Actions & Dependabot Runs with `gh`"
Cohesion: 0.40
Nodes (4): Debug GitHub Actions & Dependabot Runs with `gh`, Dependabot update-run failures, Inspect an Actions run, Tips

### Community 711 - ".get_job_data"
Cohesion: 0.20
Nodes (7): Supported Sites, _extract_location(), _extract_text(), Fix scrapper job failures logged on 2026-10-09, Outcome, Problem, Solution

## Knowledge Gaps
- **851 isolated node(s):** `$schema`, `instructions`, `disabled`, `disabled`, `plugin` (+846 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2443 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **440 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `config()` connect `logIdleWait` to `useFilterWatcher.ts`, `@testing-library/react`?**
  _High betweenness centrality (0.230) - this node is a cross-community bridge._
- **Are the 66 inferred relationships involving `MysqlUtil` (e.g. with `FastCVMatcher` and `.process_db_jobs()`) actually correct?**
  _`MysqlUtil` has 66 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `instructions`, `disabled` to the rest of the system?**
  _851 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `environmentUtil.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09468599033816426 - nodes in this community are weakly interconnected._
- **Why does `vitest` connect `vitest` to `useJobMutations.ts`, `Statistics.tsx`, `Viewer.tsx`, `ViewerApi.ts`, `App.tsx`, `react`, `useFilterWatcher.ts`, `Settings.tsx`, `@testing-library/react`, `testSetup.ts`, `JobTable.tsx`, `jobsApi`, `JobDetail.tsx`, `web/package.json`, `useSqlEditor.ts`, `@tanstack/react-query`, `backendDiscovery.ts`, `PageHeader`, `useAutoLoadMore.fixtures.tsx`, `validationUtils.ts`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Should `GmailService` be split into smaller, more focused modules?**
  _Cohesion score 0.070578231292517 - nodes in this community are weakly interconnected._
- **Why does `Logs` connect `logIdleWait` to `AiEnrichRepository`, `ai_helpers_test.py`, `AI Job Enrichment`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._